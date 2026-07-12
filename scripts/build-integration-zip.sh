#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
component="$root/custom_components/geist_conversation"
output=${1:-"$root/dist/geist_conversation.zip"}

case "$output" in
    /*) ;;
    *) output="$PWD/$output" ;;
esac

mkdir -p "$(dirname -- "$output")"
rm -f "$output"

(
    cd "$component"
    zip -q -r "$output" . \
        -x '__pycache__/*' '*.pyc' '*.pyo' '.DS_Store'
)

printf '%s\n' "$output"
