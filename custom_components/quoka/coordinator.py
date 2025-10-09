"""Data update coordinator for Quoka."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import QuokaApiClient, QuokaListing
from .const import (
    CONF_CATEGORIES,
    CONF_SEARCH_TERMS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class QuokaDataUpdateCoordinator(DataUpdateCoordinator[list[QuokaListing]]):
    """Coordinator that fetches Quoka listings."""

    def __init__(self, hass: HomeAssistant, session: ClientSession, entry_data: dict[str, Any]) -> None:
        self.api = QuokaApiClient(session)
        self.entry_data = entry_data
        update_interval = entry_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name="Quoka listings",
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_update_data(self) -> list[QuokaListing]:
        search_terms = self.entry_data.get(CONF_SEARCH_TERMS, [])
        categories = self.entry_data.get(CONF_CATEGORIES, [])
        return await self.api.async_search(search_terms, categories)

    async def async_set_entry_data(self, new_data: dict[str, Any]) -> None:
        """Update coordinator configuration when options change."""

        self.entry_data = new_data
        update_interval = new_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self.update_interval = timedelta(minutes=update_interval)
        await self.async_request_refresh()
