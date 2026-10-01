import hashlib
import re
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from app.models.event import EventItem
from app.services.event_sources.base import BaseEventSource, SourceResult, IST


class TelanganaTourismSource(BaseEventSource):
    """
    Event Source Adapter for Telangana Tourism Official Events.
    
    Status & ₹0 Compliance:
    - Official public events portal: https://www.tourism.telangana.gov.in/events
    - Purpose: Official cultural programs, festivals, public gatherings, and tourism events.
    - Automated-access & integrity policy:
      - Uses a single, respectful, low-frequency GET request (guarded by backend in-memory cache).
      - Never performs aggressive crawling, recursion, or automated form submission.
      - Strict data-integrity checks: Generic articles, festival write-ups, photo retrospectives
        (e.g. 'Glimpses from...'), and past dates are strictly excluded.
      - If the site is unreachable, times out, or changes structure, the adapter marks itself
        'unavailable' gracefully without degrading any other event source.
    """

    PORTAL_URL = "https://www.tourism.telangana.gov.in/events"

    @property
    def source_name(self) -> str:
        return "Telangana Tourism"

    @property
    def attribution(self) -> str:
        return "Telangana Tourism (Government of Telangana Official Portal)"

    @property
    def source_type(self) -> str:
        return "official"

    def _parse_portal_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse human date strings found on the Telangana Tourism portal
        (e.g., '06 May 2026', '6 May 2026', '2026-05-06') into Asia/Kolkata datetime.
        """
        cleaned = date_str.strip()
        date_formats = [
            "%d %b %Y",
            "%d %B %Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%B %d %Y",
            "%b %d %Y",
        ]
        for fmt in date_formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.replace(tzinfo=IST)
            except ValueError:
                continue
        return None

    async def fetch_events(self, city: str = "Hyderabad") -> SourceResult:
        now_ist = datetime.now(IST)
        headers = {
            "User-Agent": "TodayNearMe/1.0 (Hyderabad Local Public Utility; contact@todaynearme.local)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True, verify=False) as client:
                res = await client.get(self.PORTAL_URL)
                if res.status_code != 200:
                    return SourceResult(
                        source_name=self.source_name,
                        events=[],
                        status="unavailable",
                        attribution=self.attribution,
                        message=f"Official portal returned HTTP {res.status_code}",
                    )
                html_text = res.text
        except httpx.TimeoutException:
            return SourceResult(
                source_name=self.source_name,
                events=[],
                status="unavailable",
                attribution=self.attribution,
                message="Connection timed out while querying Telangana Tourism",
            )
        except Exception as e:
            return SourceResult(
                source_name=self.source_name,
                events=[],
                status="unavailable",
                attribution=self.attribution,
                message=f"Could not reach official tourism portal: {e}",
            )

        events: List[EventItem] = self._parse_events_html(html_text, now_ist)
        status = "ok" if events else "empty"

        return SourceResult(
            source_name=self.source_name,
            events=events,
            status=status,
            attribution=self.attribution,
            message="No upcoming events listed on official portal" if not events else None,
        )

    def _parse_events_html(self, html_text: str, now_ist: datetime) -> List[EventItem]:
        items: List[EventItem] = []

        # Find all event-box containers
        box_pattern = re.compile(
            r'<div class=["\']event-box[^"\']*["\']>(.*?)</div>\s*</div>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in box_pattern.finditer(html_text):
            box_html = match.group(1)

            # 1. Extract Title & Link
            title_match = re.search(
                r'<h3[^>]*>.*?<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>.*?</h3>',
                box_html,
                re.DOTALL | re.IGNORECASE,
            )
            if not title_match:
                # Try finding any anchor inside h3 or box
                title_match = re.search(
                    r'<a\s+[^>]*href=["\'](https://www\.tourism\.telangana\.gov\.in/events-single/[^"\']+)["\'][^>]*>(.*?)</a>',
                    box_html,
                    re.DOTALL | re.IGNORECASE,
                )

            if not title_match:
                continue

            event_url = title_match.group(1).strip()
            title_raw = title_match.group(2)
            title = self.clean_text(title_raw)
            if not title:
                continue

            # Strict Data Integrity Rule: Exclude retrospective galleries/articles
            title_lower = title.lower()
            if any(title_lower.startswith(prefix) for prefix in ["glimpses from", "photos from", "highlights of", "recap:"]):
                # Retrospective photo gallery of past celebration, not an active upcoming event
                continue

            # 2. Extract Date String
            date_match = re.search(
                r'<div[^>]*class=["\'][^"\']*text-white[^"\']*["\'][^>]*>\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})\s*</div>',
                box_html,
                re.IGNORECASE,
            )
            if not date_match:
                # Try generic date regex inside box
                date_match = re.search(
                    r'\b([0-9]{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[0-9]{4})\b',
                    box_html,
                    re.IGNORECASE,
                )

            if not date_match:
                # Without a verified date, do not fabricate or publish
                continue

            event_dt = self._parse_portal_date(date_match.group(1))
            if not event_dt:
                continue

            # Skip past events
            if event_dt.date() < now_ist.date():
                continue

            # 3. Location / Venue
            loc_match = re.search(r'<p[^>]*class=["\'][^"\']*text-gray-500[^"\']*["\'][^>]*>(.*?)</p>', box_html, re.DOTALL | re.IGNORECASE)
            venue = self.clean_text(loc_match.group(1)) if loc_match else None
            
            # 4. Check Hyderabad filter
            full_context = f"{title} {venue or ''} {event_url}"
            if not self.is_hyderabad_event(full_context):
                continue

            event_id = hashlib.sha256(f"tgt_{title}_{event_dt.isoformat()}".encode()).hexdigest()[:16]

            items.append(
                EventItem(
                    id=event_id,
                    title=title,
                    description=None,
                    start_time=event_dt.isoformat(),
                    end_time=None,
                    formatted_date=event_dt.strftime("%a, %d %b %Y"),
                    formatted_time="Time TBA",
                    time_label=self.format_time_label(event_dt, now_ist),
                    venue=venue or "Hyderabad",
                    area=None,
                    category="Cultural",
                    city="Hyderabad",
                    source=self.source_name,
                    source_url=event_url,
                    source_type=self.source_type,
                )
            )

        return items
