import asyncio
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.models.event import EventItem, EventResponse, SourceStatus
from app.services.event_sources import (
    BaseEventSource,
    SourceResult,
    IST,
    FossUnitedSource,
    TelanganaTourismSource,
    HyderabadDistrictSource,
)

# Backwards compatibility alias for existing test suites
FossUnitedEventProvider = FossUnitedSource
BaseEventProvider = BaseEventSource


class EventsService:
    """
    Multi-source Public Event Aggregator for Hyderabad.
    
    Architecture:
    FOSS United
          ↓
    Telangana Tourism
          ↓
    Hyderabad District Government
          ↓
    Event Source Adapters (concurrent non-blocking execution)
          ↓
    Normalize
          ↓
    Validate
          ↓
    Deduplicate (cross-source canonical keying)
          ↓
    Filter Hyderabad (strict exclusion of other cities/districts)
          ↓
    Sort by Date (Asia/Kolkata chronological ordering)
          ↓
    Cache (In-memory, 30-min TTL, controlled refresh)
          ↓
    FastAPI /api/events
    """

    def __init__(
        self,
        sources: Optional[List[BaseEventSource]] = None,
        provider: Optional[BaseEventSource] = None,
    ):
        if provider is not None:
            self.sources = [provider]
        elif sources is not None:
            self.sources = sources
        else:
            self.sources = [
                FossUnitedSource(),
                TelanganaTourismSource(),
                HyderabadDistrictSource(),
            ]
        # In-memory cache: cache_key -> (timestamp, EventResponse)
        self._cache: Dict[str, Tuple[float, EventResponse]] = {}

    def _get_cache_key(self, city: str) -> str:
        return f"events:{city.strip().lower()}"

    def _get_from_cache(self, key: str) -> Optional[EventResponse]:
        if key in self._cache:
            timestamp, cached_res = self._cache[key]
            if time.time() - timestamp < settings.EVENTS_CACHE_TTL_SECONDS:
                return cached_res.model_copy(update={"cached": True})
            else:
                del self._cache[key]
        return None

    def _save_to_cache(self, key: str, response: EventResponse) -> None:
        self._cache[key] = (time.time(), response)

    def _normalize_title_key(self, title: str) -> str:
        """Strip punctuation and whitespace for fuzzy duplicate detection."""
        return re.sub(r"[^a-z0-9]", "", title.lower())

    def _deduplicate_events(self, events: List[EventItem]) -> List[EventItem]:
        """
        Deduplicates events across sources using normalized title and event date.
        When duplicates are found, prefers retaining the more complete record.
        """
        unique_map: Dict[str, EventItem] = {}

        for ev in events:
            # Extract date part of start_time (YYYY-MM-DD)
            date_part = ev.start_time[:10] if len(ev.start_time) >= 10 else "nodate"
            norm_title = self._normalize_title_key(ev.title)
            dedup_key = f"{norm_title}:{date_part}"

            if dedup_key not in unique_map:
                unique_map[dedup_key] = ev
            else:
                existing = unique_map[dedup_key]
                # Completeness scoring: prefer record with description, venue, or official source
                existing_score = (
                    (1 if existing.description else 0)
                    + (1 if existing.venue and existing.venue.lower() != "hyderabad" else 0)
                    + (1 if existing.source_type == "official" else 0)
                )
                new_score = (
                    (1 if ev.description else 0)
                    + (1 if ev.venue and ev.venue.lower() != "hyderabad" else 0)
                    + (1 if ev.source_type == "official" else 0)
                )
                if new_score > existing_score:
                    unique_map[dedup_key] = ev

        return list(unique_map.values())

    async def get_events(self, city: str = "Hyderabad", refresh: bool = False) -> EventResponse:
        cache_key = self._get_cache_key(city)
        now_ist = datetime.now(IST)

        # Check in-memory cache if not explicitly refreshing
        if not refresh:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached

        # Execute all source adapters concurrently with isolation
        tasks = [source.fetch_events(city) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_raw_events: List[EventItem] = []
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
                if res.events:
                    all_raw_events.extend(res.events)
            else:
                unavailable_count += 1
                source_statuses.append(
                    SourceStatus(
                        name=source.source_name,
                        status="unavailable",
                        message="Unexpected return type from source adapter",
                    )
                )

        all_sources_unavailable = (unavailable_count == len(self.sources))

        # Filter strictly for Hyderabad and future dates
        filtered_events: List[EventItem] = []
        for ev in all_raw_events:
            full_context = f"{ev.title} {ev.venue or ''} {ev.area or ''} {ev.description or ''}"
            if not BaseEventSource.is_hyderabad_event(full_context):
                continue
            filtered_events.append(ev)

        # Cross-source deduplication
        deduped_events = self._deduplicate_events(filtered_events)

        # Sort chronologically by start_time ascending
        deduped_events.sort(key=lambda x: x.start_time)

        # Attribution line summarizing monitored sources
        sources_summary = ", ".join(s.source_name for s in self.sources)
        attribution_str = f"Aggregated from public sources: {sources_summary}"

        if all_sources_unavailable:
            message = "We couldn't retrieve the monitored public event sources right now. Please try again later."
        elif not deduped_events:
            message = "We couldn't find upcoming Hyderabad events in the public sources currently monitored by TodayNearMe."
        else:
            message = None

        response = EventResponse(
            events=deduped_events,
            city=city,
            count=len(deduped_events),
            checked_at=now_ist.isoformat(),
            source=attribution_str,
            sources=source_statuses,
            cached=False,
            message=message,
            all_unavailable=all_sources_unavailable,
        )

        self._save_to_cache(cache_key, response)
        return response


events_service = EventsService()
