#!/usr/bin/env python3
"""compatibility.json is the single source of truth: hacs.json, the manifest,
the protocol fixture, the README matrix, the disposable-HA test, and the CI
matrix must all agree with it, so no derived surface can silently drift and
no untested combination can be advertised as supported."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
compat = json.loads((ROOT / "compatibility.json").read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


VERSION = re.compile(r"^\d{4}\.\d{1,2}\.\d+$")

ha = compat["homeassistant"]
minimum = ha["minimum"]
tested = ha["tested"]

require(compat["schema"] == 1, "unexpected schema")
require(VERSION.fullmatch(minimum) is not None, "minimum HA version malformed")
require(bool(tested) and all(VERSION.fullmatch(v) for v in tested), "tested versions malformed")
# HA ships no .0 patch image, so the minimum feature line (YYYY.M) must be
# covered by a tested patch, not the exact minimum string.
def line(version: str) -> str:
    return ".".join(version.split(".")[:2])


require(any(line(v) == line(minimum) for v in tested),
        f"no tested version covers the minimum release line {line(minimum)}")
require(tested == sorted(tested, key=lambda v: [int(p) for p in v.split(".")]),
        "tested versions must be ascending")
require(compat["protocol"] == "dynamic-tools-v1", "unexpected runtime protocol")
require(compat["integration"]["protocol"] == compat["protocol"],
        "integration protocol must match the required runtime protocol")

# hacs.json minimum cannot drift from the canonical source.
hacs = json.loads((ROOT / "hacs.json").read_text())
require(hacs["homeassistant"] == minimum,
        f"hacs.json homeassistant {hacs['homeassistant']} != compat minimum {minimum}")
require(hacs["zip_release"] == compat["hacs"]["zip_release"], "hacs zip_release drift")

# Manifest version is the mapped integration version.
manifest = json.loads((ROOT / "custom_components/geist_conversation/manifest.json").read_text())
require(manifest["version"] == compat["integration"]["version"],
        f"manifest version {manifest['version']} != compat {compat['integration']['version']}")

# The runtime protocol fixture is the mandatory protocol id.
fixture = json.loads((ROOT / "protocol/dynamic-tools-v1.json").read_text())
require(fixture["protocol"] == compat["protocol"], "protocol fixture id drift")

# README advertises exactly the canonical minimum and tested set — nothing more.
readme = (ROOT / "README.md").read_text()
require(minimum in readme, f"README does not state the minimum HA version {minimum}")
for version in tested:
    require(version in readme, f"README does not list tested HA version {version}")
for candidate in VERSION.findall(readme):
    require(candidate == minimum or candidate in tested,
            f"README advertises untested HA version {candidate}")

# The disposable-HA test defaults to a tested version, never an untested one.
container = (ROOT / "tests/test_hacs_ha_container.sh").read_text()
default_image = re.search(r"HA_IMAGE:-ghcr\.io/home-assistant/home-assistant:([0-9.]+)", container)
require(default_image is not None, "disposable-HA default image not found")
require(default_image.group(1) in tested,
        f"disposable-HA default {default_image.group(1)} is not a tested version")

# The CI matrix runs exactly the tested versions — visible in the workflow.
workflow = (ROOT / ".github/workflows/hacs.yml").read_text()
matrix = re.search(r"disposable-ha:.*?ha_version:\s*\[([^\]]*)\]", workflow, re.S)
require(matrix is not None, "disposable-ha CI matrix not found")
ci_versions = [v.strip().strip('"') for v in matrix.group(1).split(",") if v.strip()]
require(ci_versions == tested,
        f"CI matrix {ci_versions} != compat tested {tested}")

print("compatibility: hacs/manifest/protocol/readme/container/ci agree with source")
