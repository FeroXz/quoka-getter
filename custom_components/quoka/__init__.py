"""The Quoka integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS
from .coordinator import QuokaDataUpdateCoordinator

ConfigEntryType = ConfigEntry[Any]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntryType) -> bool:
    """Set up Quoka from a config entry."""

    session = async_get_clientsession(hass)
    config = {**entry.data, **entry.options}
    coordinator = QuokaDataUpdateCoordinator(hass, session, config)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntryType) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntryType) -> None:
    """Handle config entry updates."""

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: QuokaDataUpdateCoordinator = data["coordinator"]
    await coordinator.async_set_entry_data({**entry.data, **entry.options})
