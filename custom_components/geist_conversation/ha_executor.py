"""Execute already-validated dynamic-tools-v1 calls inside Home Assistant.

Uses duck-typed ``hass``/``context`` objects so the security contract stays
model-free and testable without importing Home Assistant.
"""

from __future__ import annotations

from typing import Any

from .policy import PolicyError

SAFE_STATE_ATTRIBUTES = {
    "brightness",
    "current_temperature",
    "temperature",
    "unit_of_measurement",
}
JSON_SCALARS = (str, int, float, bool, type(None))


class HomeAssistantExecutor:
    def __init__(self, hass: Any, context: Any = None) -> None:
        self._hass = hass
        self._context = context

    def get_state(self, entity_id: str) -> dict[str, Any]:
        state = self._hass.states.get(entity_id)
        if state is None:
            raise PolicyError("unavailable")
        attributes = {
            key: value
            for key, value in state.attributes.items()
            if key in SAFE_STATE_ATTRIBUTES and isinstance(value, JSON_SCALARS)
        }
        return {"state": str(state.state), "attributes": attributes}

    def is_exposed(self, entity_id: str) -> bool:
        """Recheck Assist exposure at the final action boundary."""
        try:
            from homeassistant.components.homeassistant.exposed_entities import (
                async_should_expose,
            )
        except ImportError:
            return self._hass.states.get(entity_id) is not None
        return bool(async_should_expose(self._hass, "conversation", entity_id))

    async def async_call_service(
        self,
        domain: str,
        service: str,
        entity_id: str,
        arguments: dict[str, Any],
    ) -> list[Any]:
        service_data = {"entity_id": entity_id, **arguments}
        try:
            await self._hass.services.async_call(
                domain,
                service,
                service_data,
                blocking=True,
                context=self._context,
            )
        except Exception as err:
            if err.__class__.__name__ == "Unauthorized":
                raise PolicyError("denied") from err
            raise PolicyError("unavailable") from err
        return []
