#!/usr/bin/env python3
"""Model-free chaos contract: kill the runtime mid-session, interrupt the
transport, deliver an invalid health frame — every failure is correlated,
no mutating call is silently replayed, and recovery needs no HA restart.
The Repairs lifecycle is driven against a stubbed issue registry to prove
exactly one deduplicated issue per instance."""

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
    package_name = "geist_chaos_contract"
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
policy = load("policy")
session = load("dynamic_session_v1")
health = load("health")


class CountingExecutor:
    def __init__(self) -> None:
        self.mutations = 0

    def get_state(self, entity_id: str):
        return {"state": "off"}

    async def async_call_service(self, domain, service, entity_id, arguments):
        self.mutations += 1
        return []


def frame(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode() + b"\n"


async def run_session(port: int, executor: CountingExecutor) -> str:
    exposure = policy.ExposureStore(frozenset({"light.kitchen"}), 1)
    return await session.async_ask_geist_dynamic(
        f"127.0.0.1:{port}", "turn on the light", exposure, executor, timeout_s=5)


async def serve_once(handler) -> tuple[asyncio.AbstractServer, int]:
    server = await asyncio.start_server(handler, host="127.0.0.1", port=0)
    return server, server.sockets[0].getsockname()[1]


async def checks() -> None:
    executor = CountingExecutor()

    # Runtime dies after executing a mutating tool call: the session fails
    # correlated (connection_closed) and the mutation count is exactly one.
    async def dies_after_tool(reader, writer):
        await reader.readline()
        writer.write(frame({"type": "tool.call", "call_id": "c1",
                            "name": "HassTurnOn", "arguments": {"name": "light.kitchen"}}))
        await writer.drain()
        await reader.readline()  # tool.result arrives, then the process "dies"
        writer.close()

    server, port = await serve_once(dies_after_tool)
    try:
        await run_session(port, executor)
    except session.ProtocolError as err:
        assert err.code == "connection_closed"
    else:
        raise AssertionError("runtime death was hidden")
    finally:
        server.close()
        await server.wait_closed()
    assert executor.mutations == 1

    # Recovery on a fresh runtime answers normally and does NOT replay the
    # interrupted mutating call.
    async def healthy(reader, writer):
        await reader.readline()
        writer.write(frame({"type": "conversation.result", "text": "done"}))
        await writer.drain()
        writer.close()

    server, port = await serve_once(healthy)
    try:
        assert await run_session(port, executor) == "done"
    finally:
        server.close()
        await server.wait_closed()
    assert executor.mutations == 1, "mutating call was silently replayed"

    # Transport interruption before any reply stays fail-closed and correlated.
    async def slams_door(reader, writer):
        writer.close()

    server, port = await serve_once(slams_door)
    try:
        await run_session(port, executor)
    except session.ProtocolError as err:
        assert err.code == "connection_closed"
    except OSError:
        pass  # platform-dependent: reset on write instead of empty read
    else:
        raise AssertionError("transport interruption was hidden")
    finally:
        server.close()
        await server.wait_closed()

    # A dead endpoint surfaces as OSError (mapped to cannot_connect upstream).
    try:
        await run_session(port, executor)
    except OSError:
        pass
    else:
        raise AssertionError("dead endpoint was hidden")

    # Invalid health frame fails closed; a ready frame afterwards recovers
    # without any restart in between.
    async def bad_health(reader, writer):
        await reader.readline()
        writer.write(b"garbage\n")
        await writer.drain()
        writer.close()

    server, port = await serve_once(bad_health)
    try:
        await health.async_validate_health(f"127.0.0.1:{port}", 1)
    except health.HealthError as err:
        assert err.code == "invalid_response"
    else:
        raise AssertionError("invalid health frame accepted")
    finally:
        server.close()
        await server.wait_closed()

    async def ready_health(reader, writer):
        await reader.readline()
        writer.write(frame({"type": "health.result", "protocol": "dynamic-tools-v1",
                            "status": "ready"}))
        await writer.drain()
        writer.close()

    server, port = await serve_once(ready_health)
    try:
        result = await health.async_validate_health(f"127.0.0.1:{port}", 1)
        assert result.status == "ready"
    finally:
        server.close()
        await server.wait_closed()


def stub_homeassistant() -> types.SimpleNamespace:
    """Minimal HA stubs so sensor.py imports without Home Assistant."""
    registry = types.SimpleNamespace(created=[], deleted=[])

    def module(name: str) -> types.ModuleType:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
        return mod

    ha = module("homeassistant")
    components = module("homeassistant.components")
    sensor_mod = module("homeassistant.components.sensor")
    sensor_mod.SensorEntity = object
    config_entries = module("homeassistant.config_entries")
    config_entries.ConfigEntry = object
    const = module("homeassistant.const")
    const.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
    core = module("homeassistant.core")
    core.HomeAssistant = object
    helpers = module("homeassistant.helpers")
    ir = module("homeassistant.helpers.issue_registry")
    ir.IssueSeverity = types.SimpleNamespace(ERROR="error")
    ir.async_create_issue = lambda hass, domain, issue_id, **kwargs: registry.created.append(issue_id)
    ir.async_delete_issue = lambda hass, domain, issue_id: registry.deleted.append(issue_id)
    device_registry = module("homeassistant.helpers.device_registry")
    device_registry.DeviceInfo = dict
    entity_platform = module("homeassistant.helpers.entity_platform")
    entity_platform.AddEntitiesCallback = object
    ha.components = components
    ha.helpers = helpers
    return registry


async def repairs_dedup() -> None:
    registry = stub_homeassistant()
    sensor = load("sensor")

    entry = types.SimpleNamespace(entry_id="entry1", data={})
    probe = sensor.GeistHealthSensor(entry)
    probe.hass = object()

    outcomes = ["cannot_connect", "timeout", "ok", "cannot_connect"]

    async def scripted(address, timeout_s):
        outcome = outcomes.pop(0)
        if outcome == "ok":
            return health.HealthResult(protocol="dynamic-tools-v1", status="ready")
        raise sensor.HealthError(outcome)

    sensor.async_validate_health = scripted

    await probe.async_update()
    await probe.async_update()
    # Two consecutive failures upsert the SAME issue id: one deduplicated Repair.
    assert registry.created == [probe._issue_id] * 2
    assert probe._attr_native_value == "timeout"

    await probe.async_update()
    # Recovery deletes the Repair without any HA restart.
    assert registry.deleted == [probe._issue_id]
    assert probe._attr_native_value == "ready"

    await probe.async_update()
    assert registry.created == [probe._issue_id] * 3, "issue id must stay stable"


if __name__ == "__main__":
    asyncio.run(checks())
    asyncio.run(repairs_dedup())
    print("ha_chaos: correlated failures, no replay, dedup repair, recovery pass")
