#!/usr/bin/env python3
"""Model-free upgrade/rollback lifecycle contract.

The app is stateless, so the entire N-1 <-> N surface is: a fresh container
must start cleanly on whatever /data the previous version left behind (a
stale socket, at most), user junk must survive untouched, and a runtime
that does not speak dynamic-tools-v1 must never look healthy."""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "apps/geist/rootfs/run.sh"
HEALTHCHECK = ROOT / "apps/geist/rootfs/healthcheck.sh"
PREFLIGHT = ROOT / "apps/geist/rootfs/preflight.sh"

FAKE_RUNTIME = """#!/bin/sh
echo "runtime $*" >> "$GEIST_TEST_LOG"
"""
FAKE_SOCAT_BRIDGE = """#!/bin/sh
echo "socat $*" >> "$GEIST_TEST_LOG"
"""
FAKE_SOCAT_HEALTH = """#!/bin/sh
cat > /dev/null
printf '%s\\n' '{response}'
"""


def executable(path: Path, content: str) -> Path:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def start_app(tmp: Path, data: Path) -> subprocess.CompletedProcess:
    meminfo = tmp / "meminfo"
    meminfo.write_text("MemAvailable: 4000000 kB\n")
    log = tmp / "log"
    log.write_text("")
    env = os.environ | {
        "PATH": f"{tmp}/bin:{os.environ['PATH']}",
        "GEIST_RUNTIME": str(tmp / "bin/geist"),
        "GEIST_DATA_DIR": str(data),
        "GEIST_PREFLIGHT": str(PREFLIGHT),
        "GEIST_TEST_LOG": str(log),
        "GEIST_BUILD_ARCH": "aarch64",
        "GEIST_UNAME_M": "aarch64",
        "GEIST_MEMINFO": str(meminfo),
        "GEIST_MIN_DISK_MB": "1",
    }
    return subprocess.run(["sh", str(RUN)], env=env, capture_output=True, text=True)


def healthcheck(tmp: Path, response: str) -> int:
    executable(tmp / "bin/socat", FAKE_SOCAT_HEALTH.format(response=response))
    env = os.environ | {"PATH": f"{tmp}/bin:{os.environ['PATH']}"}
    return subprocess.run(["sh", str(HEALTHCHECK)], env=env, capture_output=True).returncode


def checks() -> None:
    with tempfile.TemporaryDirectory(prefix="geist-lifecycle-") as name:
        tmp = Path(name)
        (tmp / "bin").mkdir()
        executable(tmp / "bin/geist", FAKE_RUNTIME)
        executable(tmp / "bin/socat", FAKE_SOCAT_BRIDGE)

        # N-1 left a stale socket and the user parked junk in /data.
        data = tmp / "data"
        data.mkdir()
        (data / "geist.sock").write_text("stale")
        (data / "user-note.txt").write_text("keep me")

        # Upgrade start (N) and rollback start (N-1) are the same contract:
        # clean start from stale state, no migrations, junk untouched.
        for _ in ("upgrade", "rollback"):
            result = start_app(tmp, data)
            assert result.returncode == 0, (result.stdout, result.stderr)
            log = (tmp / "log").read_text()
            assert log.count("runtime --serve") == 1, log
            assert f"--serve {data}/geist.sock" in log
            assert not (data / "geist.sock").exists(), "stale socket must be removed"
            assert (data / "user-note.txt").read_text() == "keep me"
            (data / "geist.sock").write_text("stale")

        # Fresh install: /data does not exist yet.
        result = start_app(tmp, tmp / "fresh-data")
        assert result.returncode == 0, (result.stdout, result.stderr)

        # Protocol gate: only the exact dynamic-tools-v1 ready frame is
        # healthy. A pre-protocol (v0.3.3-style) or alien runtime never is.
        ready = '{"type":"health.result","protocol":"dynamic-tools-v1","status":"ready"}'
        assert healthcheck(tmp, ready) == 0
        for wrong in (
            '{"type":"health.result","protocol":"dynamic-tools-v0","status":"ready"}',
            '{"type":"health.result","protocol":"dynamic-tools-v1","status":"ok"}',
            '{"error":"unknown request"}',
            "",
        ):
            assert healthcheck(tmp, wrong) != 0, wrong


if __name__ == "__main__":
    checks()
    print("ha_lifecycle: stale-state upgrade/rollback + protocol gate pass")
