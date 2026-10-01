import asyncio
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.models.civic_update import CivicUpdateItem, CivicUpdatesResponse, SourceStatus
from app.services.civic_sources import (
    BaseCivicSource,
    SourceResult,
    IST,
    GhmcCivicSource,
    HyderabadDistrictCivicSource,
    TelanganaGovernmentCivicSource,
)


class CivicUpdatesService:
    """
    Multi-source Official Civic Notice Aggregator for Hyderabad.

    Architecture:
    GHMC (Flash News ticker + Tenders page)
          ↓
    Hyderabad District Government (NIC/S3WaaS notice table)
          ↓
    Government of Telangana (RSS feed — Hyderabad-relevant / statewide items)
          ↓
    Source Adapters (concurrent non-blocking execution)
          ↓
    Normalize
          ↓
    Validate
          ↓
    Hyderabad Relevance Filter
          ↓
    Deduplicate (cross-source canonical keying)
          ↓
    Sort by date (Asia/Kolkata, most recent first)
          ↓
    Cache (In-memory, 30-min TTL, controlled refresh)
          ↓
    FastAPI /api/civic-updates
    """

    def __init__(self, sources: Optional[List[BaseCivicSource]] = None):
        if sources is not None:
            self.sources = sources
        else:
            self.sources = [
                GhmcCivicSource(),
                HyderabadDistrictCivicSource(),
                TelanganaGovernmentCivicSource(),
            ]
        # In-memory cache: cache_key -> (timestamp, CivicUpdatesResponse)
        self._cache: Dict[str, Tuple[float, CivicUpdatesResponse]] = {}

    def _get_cache_key(self, city: str) -> str:
        return f"civic-updates:{city.strip().lower()}"

    def _get_from_cache(self, key: str) -> Optional[CivicUpdatesResponse]:
        if key in self._cache:
            timestamp, cached_res = self._cache[key]
            if time.time() - timestamp < settings.CIVIC_UPDATES_CACHE_TTL_SECONDS:
                return cached_res.model_copy(update={"cached": True})
            else:
                del self._cache[key]
        return None

    def _save_to_cache(self, key: str, response: CivicUpdatesResponse) -> None:
        self._cache[key] = (time.time(), response)

    def _normalize_title_key(self, title: str) -> str:
        """Strip punctuation and whitespace for fuzzy duplicate detection."""
        return re.sub(r"[^a-z0-9]", "", title.lower())

    def _deduplicate_updates(self, updates: List[CivicUpdateItem]) -> List[CivicUpdateItem]:
        """
        Deduplicates civic updates across official sources.
        Uses normalized title (and publication date when available) to detect identical notices
        published across multiple government portals.
        Retains the most complete/authoritative record (direct document URL, district-level over state-level,
        presence of deadline or source-provided summary).
        """
        unique_map: Dict[str, CivicUpdateItem] = {}

        for upd in updates:
            norm_title = self._normalize_title_key(upd.title)
            dedup_key = norm_title

            if dedup_key not in unique_map:
                unique_map[dedup_key] = upd
            else:
                existing = unique_map[dedup_key]
                # Scoring: prefer district-specific over state, direct document URL over portal home,
                # presence of deadline or summary
                def record_score(item: CivicUpdateItem) -> int:
                    score = 0
                    if item.summary:
                        score += 3
                    if item.deadline:
                        score += 2
                    if item.source_url and any(item.source_url.endswith(ext) for ext in (".pdf", ".aspx", ".html")):
                        score += 2
                    if item.scope and item.scope != "Statewide":
                        score += 2
                    if item.published_at:
                        score += 1
                    return score

                if record_score(upd) > record_score(existing):
                    unique_map[dedup_key] = upd

        return list(unique_map.values())

    def _filter_recency(self, updates: List[CivicUpdateItem], now_ist: datetime) -> List[CivicUpdateItem]:
        """
        Filters updates for recency according to TodayNearMe specifications.
        - Prioritizes notices within the recent display window (latest 60 days).
        - Retains older notices if they have an active future deadline or ongoing validity.
        - Retains active homepage flash notices that do not specify a published date.
        - Filters out stale historical notices with expired deadlines.
        """
        filtered: List[CivicUpdateItem] = []
        for upd in updates:
            if upd.published_at:
                try:
                    pub_dt = datetime.fromisoformat(upd.published_at)
                    age_days = (now_ist - pub_dt).days
                    if age_days <= 60:
                        filtered.append(upd)
                        continue
                    # Retain older notice if it has an ongoing future deadline
                    if upd.deadline:
                        filtered.append(upd)
                        continue
                    # Skip expired archived entries
                    continue
                except Exception:
                    filtered.append(upd)
            else:
                # Active notice without publication timestamp (e.g. homepage flash ticker)
                filtered.append(upd)

        return filtered

    def _sort_updates(self, updates: List[CivicUpdateItem]) -> List[CivicUpdateItem]:
        """
        Sort updates primarily by:
        1. Most recently published/updated (descending, in Asia/Kolkata timezone)
        2. Upcoming deadline where applicable
        3. Active undated portal notices
        """
        def sort_key(upd: CivicUpdateItem) -> Tuple[int, str, str]:
            if upd.published_at:
                return (2, upd.published_at, upd.deadline or "")
            if upd.deadline:
                return (1, upd.deadline, "")
            return (0, "", upd.title)

        return sorted(updates, key=sort_key, reverse=True)

    async def get_updates(self, city: str = "Hyderabad", refresh: bool = False) -> CivicUpdatesResponse:
        cache_key = self._get_cache_key(city)
        now_ist = datetime.now(IST)

        # Return from cache if not explicitly refreshing
        if not refresh:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached

        # Execute all source adapters concurrently with isolation
        tasks = [source.fetch_updates(city) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_raw_updates: List[CivicUpdateItem] = []
        source_statuses: List[SourceStatus] = []
        unavailable_count = 0

        for i, res in enumerate(results):
            source = self.sources[i]
            if isinstance(res, Exception):
                unavailable_count += 1
                source_statuses.append(
                    SourceStatus(
                        name=source.source_name,
                        status="unavailable",
                        message=f"Source check failed: {str(res)}",
                    )
                )
            elif isinstance(res, SourceResult):
                if res.status == "unavailable":
                    unavailable_count += 1
                source_statuses.append(
                    SourceStatus(
                        name=res.source_name,
                        status=res.status,
                        message=res.message,
                    )
                )
                if res.updates:
                    all_raw_updates.extend(res.updates)
            else:
                unavailable_count += 1
                source_statuses.append(
                    SourceStatus(
                        name=source.source_name,
                        status="unavailable",
                        message="Unexpected return type from source adapter",
                    )
                )

        all_sources_unavailable = unavailable_count == len(self.sources)

        # Cross-source deduplication
        deduped = self._deduplicate_updates(all_raw_updates)

        # Recency filter (prioritize latest ~60 days, active deadlines, and current active notices)
        recent_updates = self._filter_recency(deduped, now_ist)

        # Sort by recency and deadlines
        sorted_updates = self._sort_updates(recent_updates)

        # Attribution
        sources_summary = ", ".join(s.source_name for s in self.sources)
        attribution_str = f"Aggregated from official public sources: {sources_summary}"

        if all_sources_unavailable:
            message = (
                "We couldn't retrieve the monitored official sources right now. "
                "Please try again later."
            )
        elif not sorted_updates:
            message = (
                "We couldn't find recent Hyderabad-relevant civic notices in the official public sources "
                "currently monitored by TodayNearMe."
            )
        else:
            message = None

        response = CivicUpdatesResponse(
            updates=sorted_updates,
            city=city,
            count=len(sorted_updates),
            checked_at=now_ist.isoformat(),
            source=attribution_str,
            sources=source_statuses,
            cached=False,
            message=message,
            all_unavailable=all_sources_unavailable,
        )

        self._save_to_cache(cache_key, response)
        return response


civic_updates_service = CivicUpdatesService()
