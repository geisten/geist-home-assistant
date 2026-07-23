"""HA-owned exposure snapshot and fail-closed policy error.

This module deliberately imports no Home Assistant package. Per-call
validation lives in ``dynamic_tools_v1``; authorization is checked both when
tools are offered and immediately before execution so an unexpose or
registry replacement fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class PolicyError(ValueError):
    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


@dataclass
class ExposureStore:
    entities: frozenset[str] = field(default_factory=frozenset)
    version: int = 0

    def replace(self, entities: set[str]) -> int:
        self.entities = frozenset(entities)
        self.version += 1
        return self.version

    def contains(self, entity_id: str) -> bool:
        return entity_id in self.entities
