"""Constants for the Quoka integration."""

from __future__ import annotations

DOMAIN = "quoka"
PLATFORMS: list[str] = ["sensor"]

CONF_SEARCH_TERMS = "search_terms"
CONF_CATEGORIES = "categories"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 30  # minutes
MAX_ITEMS = 20
API_BASE_URL = "https://www.quoka.de/q/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
