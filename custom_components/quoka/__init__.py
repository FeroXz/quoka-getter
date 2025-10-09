"""The Quoka integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS, SERVICE_REFRESH
from .coordinator import QuokaDataUpdateCoordinator

ConfigEntryType = ConfigEntry[Any]
_SERVICE_REFRESH_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Quoka integration."""

    hass.data.setdefault(DOMAIN, {})

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):

        async def _handle_refresh(call: ServiceCall) -> None:
            entity_ids: list[str] | None = call.data.get(ATTR_ENTITY_ID)
            await _async_request_refresh(hass, entity_ids)

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH,
            _handle_refresh,
            schema=_SERVICE_REFRESH_SCHEMA,
        )

    return True


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
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntryType) -> None:
    """Handle config entry updates."""

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: QuokaDataUpdateCoordinator = data["coordinator"]
    await coordinator.async_set_entry_data({**entry.data, **entry.options})


async def _async_request_refresh(hass: HomeAssistant, entity_ids: list[str] | None) -> None:
    """Trigger a manual refresh for coordinators."""

    coordinators: set[QuokaDataUpdateCoordinator] = set()
    if entity_ids:
        entity_registry = er.async_get(hass)
        for entity_id in entity_ids:
            entity_entry = entity_registry.async_get(entity_id)
            if not entity_entry:
                continue
            entry_id = entity_entry.config_entry_id
            if not entry_id or entry_id not in hass.data.get(DOMAIN, {}):
                continue
            coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
            coordinators.add(coordinator)
    else:
        for data in hass.data.get(DOMAIN, {}).values():
            coordinators.add(data["coordinator"])

    for coordinator in coordinators:
        await coordinator.async_request_refresh()
