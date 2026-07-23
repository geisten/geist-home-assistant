#!/usr/bin/env python3
"""Model-free security and packaging contract for the HA app scaffold."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/geist"

repository = yaml.safe_load((ROOT / "repository.yaml").read_text())
config = yaml.safe_load((APP / "config.yaml").read_text())
dockerfile = (APP / "Dockerfile").read_text()
apparmor = (APP / "apparmor.txt").read_text()
run = (APP / "rootfs/run.sh").read_text()
health = (APP / "rootfs/healthcheck.sh").read_text()
workflow = (ROOT / ".github/workflows/ha-app.yml").read_text()

assert repository["name"] and repository["url"].startswith("https://")
assert config["slug"] == "geist"
assert config["arch"] == ["aarch64", "amd64"]
assert config["apparmor"] is True and config["init"] is False
assert config["watchdog"] == "tcp://[HOST]:[PORT:8099]"
assert config["map"] == [] and config["ports"] == {}
for key in ("host_network", "host_ipc", "host_dbus", "host_pid", "host_uts",
            "hassio_api", "homeassistant_api", "docker_api", "full_access",
            "audio", "video", "gpio", "usb", "uart", "udev", "stdin", "legacy"):
    assert config[key] is False, key
assert "BUILD_FROM" not in dockerfile
assert "FROM ghcr.io/home-assistant/base:" in dockerfile
assert "HEALTHCHECK" in dockerfile and "EXPOSE" not in dockerfile
assert 'io.hass.arch="${BUILD_ARCH}"' in dockerfile
assert "/usr/bin/geist" in run and "--serve" in run
assert "GEIST_HA_" not in run and "http" not in run.lower()
assert "TCP-LISTEN:8099,fork,reuseaddr UNIX-CONNECT:" in run
assert "/preflight.sh" in run
preflight = (APP / "rootfs/preflight.sh").read_text()
assert "status=arch_mismatch" in preflight and "status=insufficient_ram" in preflight
assert "status=insufficient_disk" in preflight and "MemAvailable" in preflight
assert 'ENV GEIST_BUILD_ARCH=${BUILD_ARCH}' in dockerfile and "/preflight.sh" in dockerfile
assert "/preflight.sh rix" in apparmor
assert 'TCP:127.0.0.1:8099' in health
assert '"type":"health"' in health and '"protocol":"dynamic-tools-v1"' in health
assert "network inet stream" in apparmor and "network inet6 stream" in apparmor
assert "/data/** rwk" in apparmor
assert "deny /config/**" in apparmor and "deny /run/docker.sock" in apparmor
assert "linux/arm64" in workflow and "linux/amd64" in workflow
assert "push: false" in workflow and "docker/build-push-action@10e90e3645eae34f1e60eeb005ba3a3d33f178e8" in workflow
assert "verify-runtime-lock.sh" in workflow and "test_runtime_lock.py" in workflow
assert 'COPY build/${BUILD_ARCH}/geist /usr/bin/geist' in dockerfile
assert "/usr/bin/geist rix" in apparmor

release = (ROOT / ".github/workflows/release-app.yml").read_text()
assert '"app-v*"' in release and 'test "$TAG" = "app-v$version"' in release
assert "verify-runtime-lock.sh" in release and "test_runtime_lock.py" in release
assert "provenance: mode=max" in release and "sbom: true" in release
assert "cosign sign --yes" in release and "cosign verify" in release
assert "id-token: write" in release and "permissions: {}" in release
assert "--certificate-oidc-issuer https://token.actions.githubusercontent.com" in release
assert ":latest" not in release
print("ha_app: multi-arch protected scaffold + private data/health boundary pass")
