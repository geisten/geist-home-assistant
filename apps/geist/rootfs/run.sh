#!/bin/sh
set -eu

runtime=/usr/bin/geist
socket=/data/geist.sock

if [ ! -x "$runtime" ]; then
    echo "geist_app status=runtime_missing"
    echo "The verified embedded-model runtime is missing from the image."
    exit 1
fi

# Supervisor mounts /data; create it for by-digest smoke runs outside HA.
mkdir -p "$(dirname "$socket")"
rm -f "$socket"
# Private app transport: bridge the container-internal port 8099 to the
# runtime socket. No host port is mapped (config.yaml ports: {}); only
# containers on the internal network — HA Core — can reach it.
socat TCP-LISTEN:8099,fork,reuseaddr UNIX-CONNECT:"$socket" &
exec "$runtime" --serve "$socket"
