#!/bin/sh
set -eu

# Paths are env-overridable for the model-free lifecycle tests only; the
# image and Supervisor never set these variables.
runtime=${GEIST_RUNTIME:-/usr/bin/geist}
data_dir=${GEIST_DATA_DIR:-/data}
preflight=${GEIST_PREFLIGHT:-/preflight.sh}
socket="$data_dir/geist.sock"

if [ ! -x "$runtime" ]; then
    echo "geist_app status=runtime_missing"
    echo "The verified embedded-model runtime is missing from the image."
    exit 1
fi

# Supervisor mounts /data; create it for by-digest smoke runs outside HA.
mkdir -p "$data_dir"
GEIST_DATA_DIR="$data_dir" "$preflight"
# Upgrade/rollback keeps no persistent state: the only thing a previous
# container version can leave behind is a stale socket, removed here.
rm -f "$socket"
# Private app transport: bridge the container-internal port 8099 to the
# runtime socket. No host port is mapped (config.yaml ports: {}); only
# containers on the internal network — HA Core — can reach it.
socat TCP-LISTEN:8099,fork,reuseaddr UNIX-CONNECT:"$socket" &
exec "$runtime" --serve "$socket"
