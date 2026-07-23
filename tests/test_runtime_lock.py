#!/usr/bin/env python3
"""Model-free runtime-lock contract: schema, digests, traversal, fail-closed.

Positive and negative paths run against locally generated fake assets, so no
network access and no GGUF download is needed. Only the committed lock's
static invariants are checked directly.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify-runtime-lock.sh"
LOCK = json.loads((ROOT / "apps/geist/runtime.lock.json").read_text())

# The serve payload embeds the response frame as hex so the sh single-quoted
# python3 -c argument never contains quotes from the frame itself.
FAKE_BINARY = """#!/bin/sh
case "${1:-}" in
    --version) echo "%(version)s" ;;
    --serve) exec python3 -c '
import socket, sys
server = socket.socket(socket.AF_UNIX)
server.bind(sys.argv[1])
server.listen(1)
conn, _ = server.accept()
conn.recv(4096)
conn.sendall(bytes.fromhex("%(frame_hex)s"))
conn.close()
' "$2" ;;
    *) exit 2 ;;
esac
"""
GOOD_FRAME = b'{"type":"health.result","protocol":"dynamic-tools-v1","status":"ready"}\n'


def make_asset(path: Path, topdir: str, *, version: str = "geist 0.4.0",
               frame: bytes = GOOD_FRAME, extra: str | None = None,
               symlink_member: bool = False) -> str:
    binary = (FAKE_BINARY % {"version": version, "frame_hex": frame.hex()}).encode()
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo(f"{topdir}/geist-bitnet")
        info.size = len(binary)
        info.mode = 0o755
        tar.addfile(info, io.BytesIO(binary))
        if extra is not None:
            info = tarfile.TarInfo(extra)
            info.size = 0
            tar.addfile(info, io.BytesIO(b""))
        if symlink_member:
            info = tarfile.TarInfo(f"{topdir}/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            tar.addfile(info)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(lock: dict, tmp: Path, *args: str) -> subprocess.CompletedProcess:
    lock_path = tmp / "lock.json"
    lock_path.write_text(json.dumps(lock))
    env = os.environ | {
        "GEIST_RUNTIME_LOCK": str(lock_path),
        "GEIST_RUNTIME_BUILD_DIR": str(tmp / "build"),
    }
    return subprocess.run([str(SCRIPT), "aarch64", *args],
                          env=env, capture_output=True, text=True)


def base_lock(sha256: str) -> dict:
    asset = {"url": "https://github.com/geisten/geistlib/releases/download/"
                    "v0.4.0/geist-bitnet-linux-arm64.tar.gz",
             "sha256": sha256,
             "member": "geist-bitnet-linux-arm64/geist-bitnet"}
    return {"schema": 1, "release": "v0.4.0", "protocol": "dynamic-tools-v1",
            "version_output": "geist 0.4.0",
            "assets": {"aarch64": dict(asset), "amd64": dict(asset)}}


def expect_fail(result: subprocess.CompletedProcess, needle: str) -> None:
    assert result.returncode != 0, (needle, result.stdout, result.stderr)
    assert needle in result.stdout + result.stderr, (needle, result.stdout, result.stderr)


def checks() -> None:
    # Committed lock: static immutability invariants.
    assert LOCK["schema"] == 1 and LOCK["protocol"] == "dynamic-tools-v1"
    assert re.fullmatch(r"v\d+\.\d+\.\d+", LOCK["release"])
    assert set(LOCK["assets"]) == {"aarch64", "amd64"}
    for entry in LOCK["assets"].values():
        assert entry["url"].startswith(
            f"https://github.com/geisten/geistlib/releases/download/{LOCK['release']}/")
        assert "latest" not in entry["url"]
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
        assert entry["member"].count("/") == 1 and ".." not in entry["member"]

    with tempfile.TemporaryDirectory(prefix="geist-lock-test-") as name:
        tmp = Path(name)
        asset = tmp / "asset.tar.gz"

        # Positive: verify, extract, --exec version and --handshake pass.
        digest = make_asset(asset, "geist-bitnet-linux-arm64")
        result = run(base_lock(digest), tmp, "--asset", str(asset),
                     "--exec", "--handshake")
        assert result.returncode == 0, (result.stdout, result.stderr)
        binary = tmp / "build/aarch64/geist"
        assert binary.is_file() and os.access(binary, os.X_OK)

        # Tampered digest fails before extraction.
        expect_fail(run(base_lock("0" * 64), tmp, "--asset", str(asset)),
                    "digest mismatch")

        # Mutable or off-host URLs never validate.
        for url in (
            "https://github.com/geisten/geistlib/releases/latest/download/geist.tar.gz",
            "https://github.com/geisten/geistlib/releases/download/v0.3.3/geist.tar.gz",
            "https://evil.example/geist-bitnet-linux-arm64.tar.gz",
        ):
            bad = base_lock(digest)
            bad["assets"]["aarch64"]["url"] = url
            expect_fail(run(bad, tmp, "--asset", str(asset)), "runtime lock invalid")

        # Schema violations fail closed.
        for mutate in (
            lambda l: l.update(schema=2),
            lambda l: l.update(release="latest"),
            lambda l: l.update(protocol="dynamic-tools-v2"),
            lambda l: l["assets"].pop("amd64"),
            lambda l: l["assets"]["aarch64"].pop("sha256"),
            lambda l: l["assets"]["aarch64"].update(member="../escape"),
        ):
            bad = base_lock(digest)
            mutate(bad)
            expect_fail(run(bad, tmp, "--asset", str(asset)), "runtime lock invalid")

        # Archive with a traversal entry is rejected.
        digest = make_asset(asset, "geist-bitnet-linux-arm64", extra="../evil")
        expect_fail(run(base_lock(digest), tmp, "--asset", str(asset)),
                    "unsafe archive entry")

        # Entries outside the locked top directory are rejected.
        digest = make_asset(asset, "geist-bitnet-linux-arm64", extra="other/file")
        expect_fail(run(base_lock(digest), tmp, "--asset", str(asset)),
                    "unexpected archive entry")

        # Symlinks are rejected.
        digest = make_asset(asset, "geist-bitnet-linux-arm64", symlink_member=True)
        expect_fail(run(base_lock(digest), tmp, "--asset", str(asset)),
                    "unsafe archive entry")

        # Locked member missing from the archive.
        digest = make_asset(asset, "geist-bitnet-linux-other")
        expect_fail(run(base_lock(digest), tmp, "--asset", str(asset)),
                    "unexpected archive entry")

        # Version mismatch fails --exec.
        digest = make_asset(asset, "geist-bitnet-linux-arm64", version="geist 0.3.3")
        expect_fail(run(base_lock(digest), tmp, "--asset", str(asset), "--exec"),
                    "version mismatch")

        # Wrong health frame fails --handshake.
        digest = make_asset(
            asset, "geist-bitnet-linux-arm64",
            frame=b'{"type":"health.result","protocol":"dynamic-tools-v1","status":"ok"}\n')
        expect_fail(run(base_lock(digest), tmp, "--asset", str(asset), "--handshake"),
                    "health handshake mismatch")


if __name__ == "__main__":
    checks()
    print("runtime_lock: schema + digest + traversal + fail-closed pass")
