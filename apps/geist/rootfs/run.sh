#!/bin/sh
set -eu

runtime=/usr/bin/geist
socket=/data/geist.sock

if [ ! -x "$runtime" ]; then
    echo "geist_app status=runtime_missing"
    echo "The verified embedded-model runtime is missing from the image."
    exit 1
fi

rm -f "$socket"
exec "$runtime" --serve "$socket"
