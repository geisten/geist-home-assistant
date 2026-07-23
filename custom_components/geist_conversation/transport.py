"""Fail-closed address parsing and connection for both transport profiles.

Core/Container uses an absolute Unix-socket path; HA OS uses the app's
internal ``host:port`` address on the private Docker network. Anything
else — schemes, paths with spaces, bad ports, IPv6 literals — is rejected
before any connection attempt. Both profiles speak the identical
``dynamic-tools-v1`` newline-JSON protocol.
"""

from __future__ import annotations

import asyncio
import re

_LABEL = r"[A-Za-z0-9]([A-Za-z0-9-]{0,62}[A-Za-z0-9])?"
HOST = re.compile(rf"^{_LABEL}(\.{_LABEL})*$")


def parse_address(address: object) -> tuple[str, str] | tuple[str, str, int]:
    """Return ``("unix", path)`` or ``("tcp", host, port)``; raise ValueError."""
    if not isinstance(address, str) or not 1 <= len(address) <= 255 or address != address.strip():
        raise ValueError("invalid_address")
    if address.startswith("/"):
        return ("unix", address)
    host, sep, port_text = address.rpartition(":")
    if not sep or HOST.fullmatch(host) is None or not port_text.isdigit():
        raise ValueError("invalid_address")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError("invalid_address")
    return ("tcp", host, port)


async def open_transport(address: str) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    parsed = parse_address(address)
    if parsed[0] == "unix":
        return await asyncio.open_unix_connection(parsed[1])
    return await asyncio.open_connection(parsed[1], parsed[2])
