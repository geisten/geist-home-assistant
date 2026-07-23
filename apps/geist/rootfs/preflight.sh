#!/bin/sh
# Resource and architecture preflight: fail with a stable, structured error
# before the runtime starts instead of crash-looping on a hopeless host.
# Status lines carry codes and numbers only — never local paths.
set -eu

# ponytail: fixed thresholds with env override — the calibration knob for
# small boards; raise/lower without rebuilding the image.
min_ram_mb=${GEIST_MIN_RAM_MB:-1536}
min_disk_mb=${GEIST_MIN_DISK_MB:-64}
meminfo=${GEIST_MEMINFO:-/proc/meminfo}
data_dir=${GEIST_DATA_DIR:-/data}
machine=${GEIST_UNAME_M:-$(uname -m)}
build_arch=${GEIST_BUILD_ARCH:-}

case "$build_arch" in
    aarch64) expected=aarch64 ;;
    amd64) expected=x86_64 ;;
    *)
        echo "geist_app status=arch_unknown build_arch=${build_arch:-unset}"
        exit 1
        ;;
esac
if [ "$machine" != "$expected" ]; then
    echo "geist_app status=arch_mismatch expected=$expected actual=$machine"
    exit 1
fi

avail_kb=$(awk '$1 == "MemAvailable:" {print $2}' "$meminfo" 2>/dev/null || true)
case "$avail_kb" in
    ''|*[!0-9]*) avail_kb=0 ;;
esac
if [ $((avail_kb / 1024)) -lt "$min_ram_mb" ]; then
    echo "geist_app status=insufficient_ram required_mb=$min_ram_mb available_mb=$((avail_kb / 1024))"
    exit 1
fi

free_mb=$(df -Pm "$data_dir" 2>/dev/null | awk 'NR == 2 {print $4}')
case "$free_mb" in
    ''|*[!0-9]*) free_mb=0 ;;
esac
if [ "$free_mb" -lt "$min_disk_mb" ]; then
    echo "geist_app status=insufficient_disk required_mb=$min_disk_mb available_mb=$free_mb"
    exit 1
fi

echo "geist_app status=preflight_ok arch=$machine available_ram_mb=$((avail_kb / 1024)) free_disk_mb=$free_mb"
