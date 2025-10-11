"""Constants for the Quoka integration."""

from __future__ import annotations

DOMAIN = "quoka"
PLATFORMS: list[str] = ["sensor", "button"]

CONF_SEARCH_TERMS = "search_terms"
CONF_CATEGORIES = "categories"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_MAX_LISTINGS = "max_listings"

DEFAULT_UPDATE_INTERVAL = 30  # minutes
DEFAULT_MAX_LISTINGS = 20
API_BASE_URL = "https://www.quoka.de/anzeigen"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.quoka.de/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}
SERVICE_REFRESH = "refresh"
