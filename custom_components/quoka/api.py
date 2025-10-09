"""API helpers for the Quoka integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

from .const import API_BASE_URL, DEFAULT_MAX_LISTINGS, HEADERS

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class QuokaListing:
    """Representation of a Quoka listing."""

    title: str
    price: str | None
    location: str | None
    url: str
    image: str | None
    published: datetime | None


class QuokaApiClient:
    """Simple client that scrapes listings from Quoka."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._lock = asyncio.Lock()

    async def async_search(
        self,
        search_terms: list[str],
        categories: list[str],
        max_items: int | None = None,
    ) -> list[QuokaListing]:
        """Fetch listings for the given search terms and categories."""

        if not search_terms:
            raise ValueError("At least one search term is required")

        queries = []
        for term in search_terms:
            encoded_term = quote_plus(term.strip())
            if categories:
                for category in categories:
                    queries.append(f"{encoded_term}/{quote_plus(category.strip())}")
            else:
                queries.append(encoded_term)

        listings: list[QuokaListing] = []
        tasks = [self._fetch_listings(query) for query in queries]
        for future in asyncio.as_completed(tasks):
            try:
                listings.extend(await future)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Failed to fetch listings for a query")

        # Deduplicate by URL while preserving order
        seen: set[str] = set()
        unique_listings = []
        max_results = max_items or DEFAULT_MAX_LISTINGS
        for item in listings:
            if item.url in seen:
                continue
            seen.add(item.url)
            unique_listings.append(item)
            if len(unique_listings) >= max_results:
                break

        return unique_listings

    async def _fetch_listings(self, query: str) -> list[QuokaListing]:
        """Fetch listings for a single query."""

        async with self._lock:
            response = await self._session.get(f"{API_BASE_URL}{query}", headers=HEADERS, timeout=30)
        response.raise_for_status()
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("article")

        listings: list[QuokaListing] = []
        for card in cards:
            title_elem = card.select_one("a.result-list-entry__brand-title")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            url = title_elem.get("href") or ""
            price_elem = card.select_one("span.result-list-entry__price")
            price = price_elem.get_text(strip=True) if price_elem else None
            location_elem = card.select_one("span.result-list-entry__city")
            location = location_elem.get_text(strip=True) if location_elem else None
            image_elem = card.select_one("img")
            image = (
                (image_elem.get("data-src") or image_elem.get("src"))
                if image_elem
                else None
            )
            timestamp_elem = card.select_one("time")
            published: datetime | None = None
            if timestamp_elem and timestamp_elem.has_attr("datetime"):
                try:
                    published = datetime.fromisoformat(timestamp_elem["datetime"])  # type: ignore[index]
                except ValueError:
                    published = None
            listings.append(
                QuokaListing(
                    title=title,
                    price=price,
                    location=location,
                    url=url,
                    image=image,
                    published=published,
                )
            )

        return listings
