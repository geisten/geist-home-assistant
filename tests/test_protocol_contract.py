#!/usr/bin/env python3
"""Pinned cross-repository protocol boundary."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "protocol/dynamic-tools-v1.json").read_text())
health = (ROOT / "custom_components/geist_conversation/health.py").read_text()
session = (ROOT / "custom_components/geist_conversation/dynamic_session_v1.py").read_text()

assert contract["protocol"] == "dynamic-tools-v1"
for value in contract["health_request"].values():
    assert value in health
for field in contract["conversation_request_required"]:
    assert field in session
for field in contract["conversation_result_required"]:
    assert field in session

print("protocol_contract: dynamic-tools-v1 boundary pass")
