"""Button platform for Quoka manual refresh."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import QuokaDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Quoka refresh button."""

    coordinator: QuokaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities([QuokaRefreshButton(coordinator, entry.entry_id)])


class QuokaRefreshButton(ButtonEntity):
    """Button to trigger a manual refresh of Quoka listings."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: QuokaDataUpdateCoordinator, entry_id: str) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_refresh"
        self._attr_name = "Manuell aktualisieren"

    async def async_press(self) -> None:
        await self._coordinator.async_request_refresh()
