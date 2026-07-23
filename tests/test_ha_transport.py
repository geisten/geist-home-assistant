#!/usr/bin/env python3
"""Golden transport contract: the identical dynamic session runs over a real
Unix socket and a real internal TCP connection, and address parsing fails
closed on everything else. No public listener is introduced: the app config
keeps ports: {} and the bridge listens container-internally only."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/geist_conversation"


def load(name: str):
    package_name = "geist_transport_contract"
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


class Executor:
    def get_state(self, entity_id: str):
        return {"state": "off"}

    async def async_call_service(self, domain, service, entity_id, arguments):
        return []


async def scripted_engine(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """One golden exchange: read the request, answer conversation.result."""
    request = json.loads(await reader.readline())
    assert {"input", "max_tool_steps", "tools"} <= set(request)
    writer.write(json.dumps(
        {"type": "conversation.result", "text": f"echo:{request['input']}"}
    ).encode() + b"\n")
    await writer.drain()
    writer.close()


async def golden(address: str) -> str:
    exposure = policy.ExposureStore(frozenset({"light.kitchen"}), 1)
    return await session.async_ask_geist_dynamic(
        address, "turn on", exposure, Executor(), timeout_s=5)


async def checks() -> None:
    # Same golden session over a real Unix socket ...
    with tempfile.TemporaryDirectory(prefix="geist-transport-") as tmp:
        sock = f"{tmp}/geist.sock"
        server = await asyncio.start_unix_server(scripted_engine, path=sock)
        try:
            assert await golden(sock) == "echo:turn on"
        finally:
            server.close()
            await server.wait_closed()

    # ... and over a real internal TCP connection, byte-identical protocol.
    # Ten sequential requests hit the same resident server instance: fresh
    # connections per request never respawn the process (no reload per
    # request); real-model residency evidence lands with the P5.7 soak.
    connections = 0

    async def counting_engine(reader, writer):
        nonlocal connections
        connections += 1
        await scripted_engine(reader, writer)

    server = await asyncio.start_server(counting_engine, host="127.0.0.1", port=0)
    port = server.sockets[0].getsockname()[1]
    try:
        for _ in range(10):
            assert await golden(f"127.0.0.1:{port}") == "echo:turn on"
    finally:
        server.close()
        await server.wait_closed()
    assert connections == 10

    # The app starts the runtime exactly once per process lifetime.
    run = (ROOT / "apps/geist/rootfs/run.sh").read_text()
    assert run.count('exec "$runtime"') == 1 and "while" not in run

    # Address parsing fails closed.
    assert transport.parse_address("/config/geist.sock") == ("unix", "/config/geist.sock")
    assert transport.parse_address("local-geist:8099") == ("tcp", "local-geist", 8099)
    assert transport.parse_address("a.b-c.d:1") == ("tcp", "a.b-c.d", 1)
    for bad in ("http://host:1", "host:0", "host:65536", "host:", ":1", "host",
                "ho st:1", "host:1/x", "-bad:1", "bad-:1", "[::1]:1", "", None,
                "x" * 256, "host:01a"):
        try:
            transport.parse_address(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid address: {bad!r}")

    # No public listener: the app maps no host port and keeps no REST path.
    config = (ROOT / "apps/geist/config.yaml").read_text()
    assert "ports: {}" in config and "host_network: false" in config
    run = (ROOT / "apps/geist/rootfs/run.sh").read_text()
    assert "TCP-LISTEN:8099" in run and "http" not in run.lower()


if __name__ == "__main__":
    asyncio.run(checks())
    print("ha_transport: golden unix+tcp session, fail-closed addresses pass")
