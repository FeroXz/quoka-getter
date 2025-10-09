"""Sensor platform for Quoka."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CATEGORIES, CONF_SEARCH_TERMS, DOMAIN
from .coordinator import QuokaDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Quoka sensor."""

    coordinator: QuokaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([QuokaSensor(coordinator, entry.entry_id)])


class QuokaSensor(CoordinatorEntity[QuokaDataUpdateCoordinator], SensorEntity):
    """Sensor that exposes the number of Quoka listings."""

    _attr_icon = "mdi:view-list"
    _attr_has_entity_name = True

    def __init__(self, coordinator: QuokaDataUpdateCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_listings"
        self._attr_name = "Quoka Listings"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self) -> dict[str, list[dict[str, str | None]]]:
        listings = []
        for item in self.coordinator.data or []:
            listings.append(
                {
                    "title": item.title,
                    "price": item.price,
                    "location": item.location,
                    "url": item.url,
                    "image": item.image,
                    "published": item.published.isoformat() if item.published else None,
                }
            )
        return {
            "search_terms": self.coordinator.entry_data.get(CONF_SEARCH_TERMS, []),
            "categories": self.coordinator.entry_data.get(CONF_CATEGORIES, []),
            "listings": listings,
        }
