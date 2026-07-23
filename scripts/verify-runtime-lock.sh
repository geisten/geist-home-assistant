#!/bin/sh
# Materialize and verify the immutable Geist runtime for one architecture.
#
#   scripts/verify-runtime-lock.sh ARCH [--asset FILE] [--exec] [--handshake]
#
# ARCH is aarch64 or amd64. Without --asset the locked release URL is
# downloaded. The SHA-256 is checked before extraction, archive paths are
# validated against traversal and unexpected entries, and only the locked
# member is extracted to apps/geist/build/ARCH/geist. --exec additionally
# runs the binary and compares `--version` against the lock; --handshake
# starts `--serve` and requires the exact dynamic-tools-v1 health frame.
# Every failure is fatal (fail closed); a mutable or off-host URL never
# passes lock validation.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
# Overridable for the model-free negative tests only; CI and builds use the
# committed lock and the in-repo build directory.
lock="${GEIST_RUNTIME_LOCK:-$root/apps/geist/runtime.lock.json}"
build_root="${GEIST_RUNTIME_BUILD_DIR:-$root/apps/geist/build}"

arch=${1:?usage: verify-runtime-lock.sh ARCH [--asset FILE] [--exec] [--handshake]}
shift
asset=""
run_exec=0
run_handshake=0
while [ $# -gt 0 ]; do
    case "$1" in
        --asset) asset=${2:?--asset needs a file}; shift 2 ;;
        --exec) run_exec=1; shift ;;
        --handshake) run_handshake=1; shift ;;
        *) echo "verify-runtime-lock: unknown argument $1" >&2; exit 2 ;;
    esac
done

out_dir="$build_root/$arch"
mkdir -p "$out_dir"

# Validate the lock and print "url sha256 member" for the arch; fail closed.
fields=$(python3 - "$lock" "$arch" <<'EOF'
import json, re, sys

lock_path, arch = sys.argv[1], sys.argv[2]
try:
    lock = json.load(open(lock_path))
except (OSError, json.JSONDecodeError) as err:
    sys.exit(f"runtime lock unreadable: {err}")

def fail(message):
    sys.exit(f"runtime lock invalid: {message}")

if lock.get("schema") != 1:
    fail("schema must be 1")
release = lock.get("release")
if not isinstance(release, str) or not re.fullmatch(r"v\d+\.\d+\.\d+", release):
    fail("release must be an exact vX.Y.Z tag")
if lock.get("protocol") != "dynamic-tools-v1":
    fail("protocol must be dynamic-tools-v1")
version_output = lock.get("version_output")
if not isinstance(version_output, str) or not version_output.strip():
    fail("version_output missing")
assets = lock.get("assets")
if not isinstance(assets, dict) or set(assets) != {"aarch64", "amd64"}:
    fail("assets must cover exactly aarch64 and amd64")
if arch not in assets:
    fail(f"no asset for {arch}")
for name, entry in assets.items():
    if not isinstance(entry, dict) or set(entry) != {"url", "sha256", "member"}:
        fail(f"asset {name} must have exactly url, sha256, member")
    url, sha256, member = entry["url"], entry["sha256"], entry["member"]
    prefix = f"https://github.com/geisten/geistlib/releases/download/{release}/"
    if not isinstance(url, str) or not url.startswith(prefix) or "/" in url[len(prefix):]:
        fail(f"asset {name} URL is not an immutable {release} release asset")
    if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256):
        fail(f"asset {name} sha256 must be 64 hex chars")
    if (not isinstance(member, str) or member.startswith("/")
            or ".." in member.split("/") or member.count("/") != 1):
        fail(f"asset {name} member must be topdir/file")

entry = assets[arch]
print(entry["url"], entry["sha256"], entry["member"])
EOF
)
url=$(echo "$fields" | cut -d' ' -f1)
sha256=$(echo "$fields" | cut -d' ' -f2)
member=$(echo "$fields" | cut -d' ' -f3)

if [ -z "$asset" ]; then
    asset="$out_dir/$(basename "$url")"
    echo "verify-runtime-lock: downloading $url"
    curl -fsSL --proto '=https' --tlsv1.2 -o "$asset" "$url"
fi

# Digest before extraction, then traversal-safe single-member extraction.
python3 - "$asset" "$sha256" "$member" "$out_dir/geist" <<'EOF'
import hashlib, sys, tarfile

asset, expected, member, target = sys.argv[1:5]
digest = hashlib.sha256(open(asset, "rb").read()).hexdigest()
if digest != expected:
    sys.exit(f"digest mismatch: expected {expected}, got {digest}")

topdir = member.split("/", 1)[0]
with tarfile.open(asset, "r:gz") as tar:
    names = set()
    for info in tar.getmembers():
        parts = info.name.split("/")
        if (info.name.startswith("/") or ".." in parts or "" in parts
                or not (info.isreg() or info.isdir())):
            sys.exit(f"unsafe archive entry: {info.name}")
        if parts[0] != topdir:
            sys.exit(f"unexpected archive entry outside {topdir}: {info.name}")
        names.add(info.name)
    if member not in names:
        sys.exit(f"locked member {member} missing from archive")
    binary = tar.extractfile(member)
    if binary is None:
        sys.exit(f"locked member {member} is not a regular file")
    with open(target, "wb") as out:
        while chunk := binary.read(1 << 20):
            out.write(chunk)
EOF
chmod 0755 "$out_dir/geist"

if [ "$run_exec" = 1 ]; then
    expected_version=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version_output"])' "$lock")
    actual_version=$("$out_dir/geist" --version)
    if [ "$actual_version" != "$expected_version" ]; then
        echo "verify-runtime-lock: version mismatch: expected '$expected_version', got '$actual_version'" >&2
        exit 1
    fi
fi

if [ "$run_handshake" = 1 ]; then
    python3 - "$out_dir/geist" <<'EOF'
import asyncio, os, subprocess, sys, tempfile

binary = sys.argv[1]
REQUEST = b'{"type":"health"}\n'
EXPECTED = b'{"type":"health.result","protocol":"dynamic-tools-v1","status":"ready"}\n'

async def handshake(sock, server):
    # ponytail: 300s covers scalar-fallback model load; matches engine release CI.
    async with asyncio.timeout(300):
        while not os.path.exists(sock):
            if server.poll() is not None:
                sys.exit(f"serve exited before handshake: {server.returncode}")
            await asyncio.sleep(0.5)
        while True:
            try:
                reader, writer = await asyncio.open_unix_connection(sock)
            except OSError:
                if server.poll() is not None:
                    sys.exit(f"serve exited before handshake: {server.returncode}")
                await asyncio.sleep(0.5)
                continue
            writer.write(REQUEST)
            await writer.drain()
            line = await reader.readline()
            writer.close()
            if line == EXPECTED:
                return
            sys.exit(f"health handshake mismatch: {line!r}")

sock = os.path.join(tempfile.mkdtemp(prefix="geist-lock-"), "geist.sock")
server = subprocess.Popen([binary, "--serve", sock])
try:
    asyncio.run(handshake(sock, server))
finally:
    server.terminate()
    server.wait(timeout=10)
print("verify-runtime-lock: health handshake ok")
EOF
fi

echo "verify-runtime-lock: $arch ok -> $out_dir/geist"
