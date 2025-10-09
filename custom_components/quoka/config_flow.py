"""Config flow for the Quoka integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CATEGORIES,
    CONF_SEARCH_TERMS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class QuokaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Quoka."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            search_terms = _split_csv(user_input.get(CONF_SEARCH_TERMS))
            if not search_terms:
                errors[CONF_SEARCH_TERMS] = "required"
            else:
                categories = _split_csv(user_input.get(CONF_CATEGORIES))
                update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                if update_interval < 5:
                    errors[CONF_UPDATE_INTERVAL] = "min_value"
                if not errors:
                    return self.async_create_entry(
                        title=", ".join(search_terms),
                        data={
                            CONF_SEARCH_TERMS: search_terms,
                            CONF_CATEGORIES: categories,
                            CONF_UPDATE_INTERVAL: update_interval,
                        },
                    )

        defaults = user_input or {}
        data_schema = vol.Schema(
            {
                vol.Required(CONF_SEARCH_TERMS, default=defaults.get(CONF_SEARCH_TERMS, "")): str,
                vol.Optional(CONF_CATEGORIES, default=defaults.get(CONF_CATEGORIES, "")): str,
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_user(user_input)


class QuokaOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Quoka."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            search_terms = _split_csv(user_input.get(CONF_SEARCH_TERMS))
            if not search_terms:
                errors[CONF_SEARCH_TERMS] = "required"
            else:
                categories = _split_csv(user_input.get(CONF_CATEGORIES))
                update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                if update_interval < 5:
                    errors[CONF_UPDATE_INTERVAL] = "min_value"
                if not errors:
                    return self.async_create_entry(
                        title=self.config_entry.title,
                        data={
                            CONF_SEARCH_TERMS: search_terms,
                            CONF_CATEGORIES: categories,
                            CONF_UPDATE_INTERVAL: update_interval,
                        },
                    )

        data = self.config_entry.data | self.config_entry.options
        options_schema = vol.Schema(
            {
                vol.Required(CONF_SEARCH_TERMS, default=", ".join(data.get(CONF_SEARCH_TERMS, []))): str,
                vol.Optional(CONF_CATEGORIES, default=", ".join(data.get(CONF_CATEGORIES, []))): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=options_schema, errors=errors)


def async_get_options_flow(config_entry: ConfigEntry) -> QuokaOptionsFlow:
    """Return the options flow handler."""

    return QuokaOptionsFlow(config_entry)
