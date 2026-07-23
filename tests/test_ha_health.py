#!/usr/bin/env python3
"""Model-free health-client contract tests for both transport profiles."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/geist_conversation"


def load(name: str):
    package_name = "geist_health_contract"
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


transport = load("transport")
health = load("health")


class Reader:
    def __init__(self, response: object) -> None:
        self.response = response

    async def readline(self) -> bytes:
        if isinstance(self.response, bytes):
            return self.response
        return json.dumps(self.response, separators=(",", ":")).encode() + b"\n"


class Writer:
    def __init__(self) -> None:
        self.payload = b""
        self.closed = False

    def write(self, payload: bytes) -> None:
        self.payload += payload

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


async def expect(code: str, response: object | None = None, error: Exception | None = None,
                 address: str = "/config/geist.sock") -> None:
    async def connect(*_args):
        if error is not None:
            raise error
        return Reader(response), Writer()

    original_unix = transport.asyncio.open_unix_connection
    original_tcp = transport.asyncio.open_connection
    transport.asyncio.open_unix_connection = connect
    transport.asyncio.open_connection = connect
    try:
        await health.async_validate_health(address, 0.1)
    except health.HealthError as err:
        assert err.code == code, (err.code, code)
    else:
        raise AssertionError(f"expected {code}")
    finally:
        transport.asyncio.open_unix_connection = original_unix
        transport.asyncio.open_connection = original_tcp


async def ready_check(address: str, patch: str) -> None:
    writer = Writer()

    async def ready(*_args):
        return Reader({"type": "health.result", "protocol": "dynamic-tools-v1",
                       "status": "ready"}), writer

    original = getattr(transport.asyncio, patch)
    setattr(transport.asyncio, patch, ready)
    try:
        result = await health.async_validate_health(address, 0.1)
    finally:
        setattr(transport.asyncio, patch, original)
    assert writer.payload == health.REQUEST and writer.closed
    assert result == health.HealthResult(protocol="dynamic-tools-v1", status="ready")


async def checks() -> None:
    # The identical golden handshake passes over both transport profiles.
    await ready_check("/config/geist.sock", "open_unix_connection")
    await ready_check("local-geist:8099", "open_connection")

    await expect("cannot_connect", error=FileNotFoundError())
    await expect("timeout", error=TimeoutError())
    await expect("invalid_response", response=b"not-json\n")
    await expect("unsupported_protocol", response={"type": "health.result",
                 "protocol": "other", "status": "ready"})
    await expect("not_ready", response={"type": "health.result",
                 "protocol": "dynamic-tools-v1", "status": "loading"})
    for bad in ("relative.sock", "", "http://host:1", "host:0", "host:70000",
                "host:port", " host:1", "host:1 ", "a b:1"):
        try:
            await health.async_validate_health(bad, 0.1)
        except health.HealthError as err:
            assert err.code == "invalid_socket", (bad, err.code)
        else:
            raise AssertionError(f"invalid address accepted: {bad!r}")


if __name__ == "__main__":
    asyncio.run(checks())
    print("ha_health: pass")
