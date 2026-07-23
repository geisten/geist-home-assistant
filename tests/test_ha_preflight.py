#!/usr/bin/env python3
"""Model-free preflight contract: arch, RAM, and disk gates fail closed with
structured status lines and never leak local paths."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "apps/geist/rootfs/preflight.sh"


def run(tmp: Path, *, build_arch: str = "aarch64", machine: str = "aarch64",
        mem_available_kb: int | None = 4_000_000, min_ram_mb: str = "1536",
        min_disk_mb: str = "1") -> subprocess.CompletedProcess:
    meminfo = tmp / "meminfo"
    if mem_available_kb is None:
        meminfo.write_text("MemTotal: 1 kB\n")
    else:
        meminfo.write_text(f"MemTotal: 8000000 kB\nMemAvailable: {mem_available_kb} kB\n")
    env = os.environ | {
        "GEIST_BUILD_ARCH": build_arch,
        "GEIST_UNAME_M": machine,
        "GEIST_MEMINFO": str(meminfo),
        "GEIST_DATA_DIR": str(tmp),
        "GEIST_MIN_RAM_MB": min_ram_mb,
        "GEIST_MIN_DISK_MB": min_disk_mb,
    }
    return subprocess.run(["sh", str(SCRIPT)], env=env, capture_output=True, text=True)


def expect(result: subprocess.CompletedProcess, ok: bool, needle: str, tmp: Path) -> None:
    assert (result.returncode == 0) == ok, (result.returncode, result.stdout, result.stderr)
    assert needle in result.stdout, (needle, result.stdout)
    assert str(tmp) not in result.stdout, "status line leaked a local path"


def checks() -> None:
    with tempfile.TemporaryDirectory(prefix="geist-preflight-") as name:
        tmp = Path(name)

        expect(run(tmp), True, "status=preflight_ok", tmp)
        expect(run(tmp, build_arch="amd64", machine="x86_64"), True, "status=preflight_ok", tmp)

        # Architecture gate: mismatch and unknown build arch never start.
        expect(run(tmp, build_arch="amd64", machine="aarch64"), False, "status=arch_mismatch", tmp)
        expect(run(tmp, build_arch="aarch64", machine="x86_64"), False, "status=arch_mismatch", tmp)
        expect(run(tmp, build_arch="riscv64"), False, "status=arch_unknown", tmp)
        expect(run(tmp, build_arch=""), False, "status=arch_unknown", tmp)

        # RAM gate: below threshold and unreadable meminfo fail closed.
        expect(run(tmp, mem_available_kb=500_000), False, "status=insufficient_ram", tmp)
        expect(run(tmp, mem_available_kb=None), False, "status=insufficient_ram", tmp)
        expect(run(tmp, mem_available_kb=2_000_000, min_ram_mb="4096"), False,
               "status=insufficient_ram", tmp)

        # Disk gate: an absurd requirement proves the free-space comparison.
        expect(run(tmp, min_disk_mb="99999999"), False, "status=insufficient_disk", tmp)


if __name__ == "__main__":
    checks()
    print("ha_preflight: arch + ram + disk gates fail closed pass")
