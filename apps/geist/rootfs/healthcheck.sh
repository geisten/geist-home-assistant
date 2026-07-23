#!/bin/sh
set -eu

# Probe through the internal TCP bridge so a dead bridge or a dead runtime
# both mark the container unhealthy.
response=$(
    printf '%s\n' '{"type":"health"}' |
        socat -T 4 - TCP:127.0.0.1:8099
)

test "$response" = '{"type":"health.result","protocol":"dynamic-tools-v1","status":"ready"}'
