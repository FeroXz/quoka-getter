"""API helpers for the Quoka integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from urllib.parse import quote, quote_plus, urljoin

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

        base_url = API_BASE_URL.rstrip("/")
        queries: list[tuple[str, str]] = []
        for term in search_terms:
            normalized_term = term.strip()
            if not normalized_term:
                continue
            encoded_term = quote_plus(normalized_term)
            if categories:
                for category in categories:
                    normalized_category = category.strip(" /")
                    if not normalized_category:
                        continue
                    encoded_category = quote(normalized_category, safe="/-")
                    queries.append(
                        (
                            f"{base_url}/{encoded_category}?query={encoded_term}",
                            normalized_term,
                        )
                    )
            else:
                queries.append((f"{base_url}?query={encoded_term}", normalized_term))

        if not queries:
            raise ValueError("At least one search term is required")

        async def fetch_for_query(url: str, term: str) -> list[QuokaListing]:
            """Fetch listings for a single query with resilient logging."""

            try:
                results = await self._fetch_listings(url)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Failed to fetch listings for %s", url)
                return []

            _LOGGER.debug(
                "Fetched %s listings for url %s (term=%s)",
                len(results),
                url,
                term,
            )
            return results

        listings: list[QuokaListing] = []
        results_by_query = await asyncio.gather(
            *(fetch_for_query(url, term) for url, term in queries),
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

    async def _fetch_listings(self, url: str) -> list[QuokaListing]:
        """Fetch listings for a single query."""

        async with self._lock:
            async with self._session.get(
                url,
                headers=HEADERS,
                timeout=30,
            ) as response:
                if response.status == 404:
                    _LOGGER.debug("Request %s returned 404 – treating as empty result", url)
                    await response.read()
                    return []
                response.raise_for_status()
                html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.article-item[data-articleid]")

        listings: list[QuokaListing] = []
        for card in cards:
            title_elem = card.select_one("h2.article-title a")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            href = title_elem.get("href") or ""
            listing_url = urljoin(API_BASE_URL, href)
            price_elem = card.select_one("span.article-price")
            price = price_elem.get_text(strip=True) if price_elem else None
            location_elem = card.select_one("p.article-location span")
            location = location_elem.get_text(strip=True) if location_elem else None
            image_elem = card.select_one("div.art-img img")
            image: str | None = None
            if image_elem:
                image = image_elem.get("src") or image_elem.get("data-src")
                if image and image.startswith("//"):
                    image = f"https:{image}"
            date_elem = card.select_one("p.article-date span")
            published = self._parse_published(date_elem.get_text(strip=True)) if date_elem else None
            listings.append(
                QuokaListing(
                    title=title,
                    price=price,
                    location=location,
                    url=listing_url,
                    image=image,
                    published=published,
                )
            )

        return listings

    @staticmethod
    def _parse_published(raw: str) -> datetime | None:
        """Parse the published timestamp from the search results."""

        text = raw.strip()
        if not text:
            return None

        lower = text.casefold()
        now = datetime.now()

        def _apply_time(base: datetime, fragments: list[str]) -> datetime:
            if fragments:
                time_fragment = fragments[-1].replace("Uhr", "").replace(",", "").strip()
                if ":" in time_fragment:
                    try:
                        hours, minutes = time_fragment.split(":", 1)
                        base = base.replace(hour=int(hours), minute=int(minutes), second=0, microsecond=0)
                    except ValueError:
                        _LOGGER.debug("Failed to parse time fragment '%s'", time_fragment)
            return base

        if lower.startswith("heute"):
            parts = text.split()
            base = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return _apply_time(base, parts[1:])

        if lower.startswith("gestern"):
            parts = text.split()
            base = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            return _apply_time(base, parts[1:])

        month_map = {
            "januar": 1,
            "februar": 2,
            "märz": 3,
            "maerz": 3,
            "april": 4,
            "mai": 5,
            "juni": 6,
            "juli": 7,
            "august": 8,
            "september": 9,
            "oktober": 10,
            "november": 11,
            "dezember": 12,
        }

        parts = text.replace(".", " ").split()
        if not parts or not parts[0].isdigit():
            return None

        try:
            day = int(parts[0])
        except ValueError:
            return None

        month_name = parts[1].casefold() if len(parts) > 1 else ""
        month = month_map.get(month_name)
        if not month:
            return None

        year = now.year
        next_part_index = 2
        if len(parts) > 2:
            year_candidate = parts[2].rstrip(".,")
            if year_candidate.isdigit():
                year = int(year_candidate)
                next_part_index = 3

        try:
            base = datetime(year, month, day)
        except ValueError:
            return None

        # If the parsed date lies in the future by more than a day, assume it belongs to the previous year.
        if base > now + timedelta(days=1):
            try:
                base = base.replace(year=year - 1)
            except ValueError:
                return None

        return _apply_time(base, parts[next_part_index:])
