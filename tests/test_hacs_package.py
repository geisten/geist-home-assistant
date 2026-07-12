#!/usr/bin/env python3
"""HACS metadata and release-ZIP contract."""

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/geist_conversation"

hacs = json.loads((ROOT / "hacs.json").read_text())
manifest = json.loads((COMPONENT / "manifest.json").read_text())

assert hacs == {
    "name": "Geist Conversation",
    "zip_release": True,
    "filename": "geist_conversation.zip",
    "hide_default_branch": True,
    "homeassistant": "2026.6.0",
}
for key in ("domain", "name", "version", "documentation", "issue_tracker",
            "codeowners", "integration_type", "iot_class", "requirements",
            "config_flow"):
    assert key in manifest, key
assert manifest["domain"] == COMPONENT.name
assert manifest["integration_type"] == "service"

with tempfile.TemporaryDirectory() as tmp:
    artifact = Path(tmp) / hacs["filename"]
    subprocess.run(
        [str(ROOT / "scripts/build-integration-zip.sh"), str(artifact)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    with zipfile.ZipFile(artifact) as package:
        names = set(package.namelist())
        assert "manifest.json" in names
        assert "__init__.py" in names
        assert "translations/de.json" in names
        assert "translations/en.json" in names
        assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
        packaged_manifest = json.loads(package.read("manifest.json"))
        assert packaged_manifest["version"] == manifest["version"]

print("hacs_package: metadata + release ZIP pass")
