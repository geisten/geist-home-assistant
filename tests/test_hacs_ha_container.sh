#!/bin/sh
# Package-equivalent HACS install/upgrade against a disposable HA Core image.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ha_image=${HA_IMAGE:-ghcr.io/home-assistant/home-assistant:2026.6.1}
echo "hacs_ha_container: testing against $ha_image"
tmp=${TMPDIR:-/tmp}/geist-hacs-ha-$$
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

mkdir -p "$tmp/config/custom_components/geist_conversation"
printf 'default_config:\n' >"$tmp/config/configuration.yaml"

install_package() {
    rm -rf "$tmp/config/custom_components/geist_conversation"
    mkdir -p "$tmp/config/custom_components/geist_conversation"
    "$root/scripts/build-integration-zip.sh" "$tmp/geist_conversation.zip" >/dev/null
    unzip -q "$tmp/geist_conversation.zip" \
        -d "$tmp/config/custom_components/geist_conversation"
}

check_config() {
    docker run --rm \
        -v "$tmp/config:/config" \
        "$ha_image" \
        python -m homeassistant --script check_config -c /config
}

install_package
check_config

# Simulate a file left by an older HACS version. Upgrade must replace the
# integration directory, not merge obsolete Python modules into the new one.
printf 'obsolete\n' >"$tmp/config/custom_components/geist_conversation/removed_module.py"
install_package
test ! -e "$tmp/config/custom_components/geist_conversation/removed_module.py"
check_config

echo "hacs_ha_container: clean install + replacement upgrade pass"
