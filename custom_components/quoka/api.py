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

        queries: list[tuple[str, str]] = []
        for term in search_terms:
            normalized_term = term.strip()
            if not normalized_term:
                continue
            encoded_term = quote_plus(normalized_term)
            if categories:
                for category in categories:
                    queries.append(
                        (
                            f"{encoded_term}/{quote_plus(category.strip())}",
                            normalized_term,
                        )
                    )
            else:
                queries.append((encoded_term, normalized_term))

        if not queries:
            raise ValueError("At least one search term is required")

        async def fetch_for_query(query: str, term: str) -> list[QuokaListing]:
            """Fetch listings for a single query with resilient logging."""

            try:
                results = await self._fetch_listings(query)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Failed to fetch listings for query %s", query)
                return []

            _LOGGER.debug(
                "Fetched %s listings for query %s (term=%s)",
                len(results),
                query,
                term,
            )
            return results

        listings: list[QuokaListing] = []
        results_by_query = await asyncio.gather(
            *(fetch_for_query(query, term) for query, term in queries),
            return_exceptions=True,
        )

        for result in results_by_query:
            if isinstance(result, Exception):
                _LOGGER.error(
                    "Unexpected error while gathering listings: %s",
                    result,
                    exc_info=(type(result), result, result.__traceback__),
                )
                continue
            listings.extend(result)

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
            async with self._session.get(
                f"{API_BASE_URL}{query}", headers=HEADERS, timeout=30
            ) as response:
                if response.status == 404:
                    _LOGGER.debug("Query %s returned 404 – treating as empty result", query)
                    await response.read()
                    return []
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
