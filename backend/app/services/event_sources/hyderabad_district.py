import hashlib
import re
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from app.models.event import EventItem
from app.services.event_sources.base import BaseEventSource, SourceResult, IST


class HyderabadDistrictSource(BaseEventSource):
    """
    Event Source Adapter for Hyderabad District Administration (Government of Telangana).
    
    Status & ₹0 Compliance:
    - Official district portal: https://hyderabad.telangana.gov.in/events/
    - Hosted by National Informatics Centre (NIC) under S3WaaS.
    - Purpose: District administration public notices, government events, and official programs.
    - Automated-access & integrity policy:
      - Uses a single, respectful, low-frequency GET request (guarded by backend in-memory cache).
      - 'There is no Event.' is treated as valid empty data, not an error.
      - Handles past events gracefully (events on S3WaaS are moved or archived).
      - Strict date parsing (DD/MM/YYYY) and Asia/Kolkata timezone normalization.
      - If the site is unreachable, times out, or returns HTTP errors, it fails gracefully
        without affecting other event sources.
    """

    PORTAL_URL = "https://hyderabad.telangana.gov.in/events/"

    @property
    def source_name(self) -> str:
        return "Hyderabad District Government"

    @property
    def attribution(self) -> str:
        return "Hyderabad District Administration (Government of Telangana)"

    @property
    def source_type(self) -> str:
        return "official"

    def _parse_district_date(self, date_str: str) -> Optional[datetime]:
        """Parse standard NIC / S3WaaS date format (DD/MM/YYYY) into Asia/Kolkata datetime."""
        cleaned = date_str.strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
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
                        message=f"Official district portal returned HTTP {res.status_code}",
                    )
                html_text = res.text
        except httpx.TimeoutException:
            return SourceResult(
                source_name=self.source_name,
                events=[],
                status="unavailable",
                attribution=self.attribution,
                message="Connection timed out while querying Hyderabad District Government",
            )
        except Exception as e:
            return SourceResult(
                source_name=self.source_name,
                events=[],
                status="unavailable",
                attribution=self.attribution,
                message=f"Could not reach Hyderabad District portal: {e}",
            )

        # Check for explicit empty state indicator
        if "there is no event" in html_text.lower() or "no event found" in html_text.lower():
            return SourceResult(
                source_name=self.source_name,
                events=[],
                status="empty",
                attribution=self.attribution,
                message="No current events listed on district portal",
            )

        events: List[EventItem] = self._parse_events_html(html_text, now_ist)
        status = "ok" if events else "empty"

        return SourceResult(
            source_name=self.source_name,
            events=events,
            status=status,
            attribution=self.attribution,
            message="No upcoming events listed on district portal" if not events else None,
        )

    def _parse_events_html(self, html_text: str, now_ist: datetime) -> List[EventItem]:
        items: List[EventItem] = []

        # Find event container blocks (S3WaaS markup uses photoTxtContainer or similar)
        container_pattern = re.compile(
            r'<div class=["\']photoTxtContainer[^"\']*["\']>(.*?)</div>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in container_pattern.finditer(html_text):
            block_html = match.group(1)

            # 1. Title & URL
            link_match = re.search(
                r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*class=["\']txtHeading["\'][^>]*>(.*?)</a>',
                block_html,
                re.DOTALL | re.IGNORECASE,
            )
            if not link_match:
                link_match = re.search(
                    r'<a\s+[^>]*class=["\']txtHeading["\'][^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                    block_html,
                    re.DOTALL | re.IGNORECASE,
                )

            if not link_match:
                continue

            event_url = link_match.group(1).strip()
            title = self.clean_text(link_match.group(2))
            if not title:
                continue

            # 2. Start and End Dates
            start_date_match = re.search(
                r'Start:\s*</span>\s*([0-9]{2}/[0-9]{2}/[0-9]{4})',
                block_html,
                re.IGNORECASE,
            )
            end_date_match = re.search(
                r'End:\s*</span>\s*([0-9]{2}/[0-9]{2}/[0-9]{4})',
                block_html,
                re.IGNORECASE,
            )

            if not start_date_match:
                continue

            start_dt = self._parse_district_date(start_date_match.group(1))
            if not start_dt:
                continue

            end_dt = self._parse_district_date(end_date_match.group(1)) if end_date_match else None

            # Skip past events
            check_dt = end_dt if end_dt else start_dt
            if check_dt.date() < now_ist.date():
                continue

            # 3. Venue
            venue_match = re.search(
                r'Venue:\s*</span>\s*(.*?)</p>',
                block_html,
                re.DOTALL | re.IGNORECASE,
            )
            venue = self.clean_text(venue_match.group(1)) if venue_match else "Hyderabad"

            # 4. Strict Hyderabad check
            full_context = f"{title} {venue} {event_url}"
            if not self.is_hyderabad_event(full_context):
                continue

            event_id = hashlib.sha256(f"nic_{title}_{start_dt.isoformat()}".encode()).hexdigest()[:16]

            items.append(
                EventItem(
                    id=event_id,
                    title=title,
                    description=None,
                    start_time=start_dt.isoformat(),
                    end_time=end_dt.isoformat() if end_dt else None,
                    formatted_date=start_dt.strftime("%a, %d %b %Y"),
                    formatted_time="Official Hours",
                    time_label=self.format_time_label(start_dt, now_ist),
                    venue=venue or "Hyderabad District",
                    area=None,
                    category="Official Notice",
                    city="Hyderabad",
                    source=self.source_name,
                    source_url=event_url,
                    source_type=self.source_type,
                )
            )

        return items
