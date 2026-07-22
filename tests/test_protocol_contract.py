#!/usr/bin/env python3
"""Pinned cross-repository protocol boundary, checked behaviorally.

The fixture is exercised against the real health and session clients: the
bytes actually written on the wire must equal the fixture request, and the
fixture's required response must be accepted. String containment is not
enough to catch drift.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/geist_conversation"
contract = json.loads((ROOT / "protocol/dynamic-tools-v1.json").read_text())


def load(name: str):
    package_name = "geist_protocol_contract"
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(COMPONENT)]
        sys.modules[package_name] = package
    spec = importlib.util.spec_from_file_location(f"{package_name}.{name}", COMPONENT / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


health = load("health")
policy = load("policy")
session = load("dynamic_session_v1")


class Reader:
    def __init__(self, frames: list[dict]) -> None:
        self.frames = iter(frames)

    async def readline(self) -> bytes:
        try:
            return json.dumps(next(self.frames), separators=(",", ":")).encode() + b"\n"
        except StopIteration:
            return b""


class Writer:
    def __init__(self) -> None:
        self.frames: list[dict] = []

    def write(self, payload: bytes) -> None:
        self.frames.append(json.loads(payload))

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass


async def check_health() -> None:
    writer = Writer()

    async def connect(_path: str):
        return Reader([contract["health_response_required"]]), writer

    health.asyncio.open_unix_connection = connect
    result = await health.async_validate_health("/config/geist.sock", 0.1)
    assert writer.frames == [contract["health_request"]], writer.frames
    assert result.protocol == contract["protocol"]


async def check_conversation() -> None:
    result_type, text_field = contract["conversation_result_required"]
    writer = Writer()
    answer = await session.async_dynamic_session(
        Reader([{"type": result_type, text_field: "hello"}]),
        writer,
        "turn on the light",
        policy.ExposureStore(frozenset({"light.kitchen"}), 1),
        object(),
        timeout_s=0.5,
    )
    assert answer == "hello"
    request = writer.frames[0]
    missing = [field for field in contract["conversation_request_required"] if field not in request]
    assert not missing, missing


assert contract["protocol"] == "dynamic-tools-v1"
asyncio.run(check_health())
asyncio.run(check_conversation())
print("protocol_contract: dynamic-tools-v1 boundary pass")
