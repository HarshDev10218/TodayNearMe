import email.utils
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

import httpx

from app.models.event import EventItem
from app.services.event_sources.base import BaseEventSource, SourceResult, IST


class FossUnitedSource(BaseEventSource):
    """
    Event Source Adapter for FOSS United (Free and Open Source Software United Foundation).
    
    Status & ₹0 Compliance:
    - Registered non-profit in India organizing open-source meetups, workshops, hackathons.
    - Feeds utilized:
      1. Upcoming events iCal feed: https://fossunited.org/api/method/fossunited.api.chapter.upcoming_events_ics
      2. Hyderabad chapter RSS: https://fossunited.org/c/hyderabad/rss.xml
      3. Timeline RSS: https://fossunited.org/events/timeline/rss.xml
    - Genuinely ₹0: No API keys, no billing, standard public syndication feeds (iCal RFC 5545 & RSS 2.0).
    - Returns empty list if no upcoming events scheduled for Hyderabad.
    """

    ICS_FEED_URL = "https://fossunited.org/api/method/fossunited.api.chapter.upcoming_events_ics"
    HYD_RSS_URL = "https://fossunited.org/c/hyderabad/rss.xml"
    TIMELINE_RSS_URL = "https://fossunited.org/events/timeline/rss.xml"

    @property
    def source_name(self) -> str:
        return "FOSS United"

    @property
    def attribution(self) -> str:
        return "FOSS United Foundation (Public RSS & Calendar Syndication)"

    @property
    def source_type(self) -> str:
        return "community"

    def _parse_ics_datetime(self, val: str) -> Optional[datetime]:
        """Parse ICS datetime strings into Asia/Kolkata timezone."""
        val = val.strip()
        try:
            if val.endswith("Z"):
                dt = datetime.strptime(val, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                return dt.astimezone(IST)
            if "T" in val:
                dt = datetime.strptime(val[:15], "%Y%m%dT%H%M%S")
                return dt.replace(tzinfo=IST)
            dt = datetime.strptime(val[:8], "%Y%m%d")
            return dt.replace(tzinfo=IST)
        except Exception:
            return None

    def _parse_rss_datetime(self, val: str) -> Optional[datetime]:
        """Parse RFC 822 / 2822 RSS pubDate strings into Asia/Kolkata timezone."""
        try:
            dt = email.utils.parsedate_to_datetime(val)
            return dt.astimezone(IST)
        except Exception:
            return None

    def _unescape_ics(self, text: Optional[str]) -> str:
        """Unescape standard iCalendar RFC 5545 escaped characters."""
        if not text:
            return ""
        return (
            text.replace(r"\,", ",")
            .replace(r"\;", ";")
            .replace(r"\n", " ")
            .replace(r"\N", " ")
            .replace(r"\\", "\\")
        )

    async def fetch_events(self, city: str = "Hyderabad") -> SourceResult:
        events: List[EventItem] = []
        now_ist = datetime.now(IST)

        headers = {
            "User-Agent": "TodayNearMe/1.0 (Hyderabad Local Public Utility; contact@todaynearme.local)",
            "Accept": "text/calendar, application/rss+xml, text/xml, */*",
        }

        success_count = 0
        error_msg = None

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True) as client:
                # 1. Fetch upcoming events iCalendar feed
                try:
                    res_ics = await client.get(self.ICS_FEED_URL)
                    if res_ics.status_code == 200 and "BEGIN:VCALENDAR" in res_ics.text:
                        events.extend(self._parse_ics_content(res_ics.text, now_ist))
                        success_count += 1
                except Exception as e:
                    error_msg = f"ICS feed error: {e}"

                # 2. Fetch Hyderabad Chapter RSS feed
                try:
                    res_hyd_rss = await client.get(self.HYD_RSS_URL)
                    if res_hyd_rss.status_code == 200:
                        events.extend(self._parse_rss_content(res_hyd_rss.text, now_ist, force_hyderabad=True))
                        success_count += 1
                except Exception as e:
                    if not error_msg:
                        error_msg = f"Chapter RSS error: {e}"

                # 3. If no events yet, inspect timeline RSS for Hyderabad events
                if not events:
                    try:
                        res_timeline = await client.get(self.TIMELINE_RSS_URL)
                        if res_timeline.status_code == 200:
                            events.extend(self._parse_rss_content(res_timeline.text, now_ist, force_hyderabad=False))
                            success_count += 1
                    except Exception:
                        pass
        except Exception as e:
            return SourceResult(
                source_name=self.source_name,
                events=[],
                status="unavailable",
                attribution=self.attribution,
                message=f"Failed to connect to FOSS United feeds: {e}",
            )

        if success_count == 0:
            return SourceResult(
                source_name=self.source_name,
                events=[],
                status="unavailable",
                attribution=self.attribution,
                message=error_msg or "All FOSS United syndication feeds were unreachable.",
            )

        # Deduplicate within source by title + start_time
        unique_events: Dict[str, EventItem] = {}
        for ev in events:
            dedup_key = f"{ev.title.strip().lower()}:{ev.start_time}"
            if dedup_key not in unique_events:
                unique_events[dedup_key] = ev

        event_list = list(unique_events.values())
        status = "ok" if event_list else "empty"

        return SourceResult(
            source_name=self.source_name,
            events=event_list,
            status=status,
            attribution=self.attribution,
            message="No upcoming events scheduled" if not event_list else None,
        )

    def _parse_ics_content(self, ics_text: str, now_ist: datetime) -> List[EventItem]:
        items: List[EventItem] = []
        raw_events = ics_text.split("BEGIN:VEVENT")

        for block in raw_events[1:]:
            raw_lines = block.strip().splitlines()
            unfolded_lines: List[str] = []
            for line in raw_lines:
                if (line.startswith(" ") or line.startswith("\t")) and unfolded_lines:
                    unfolded_lines[-1] += line[1:]
                else:
                    unfolded_lines.append(line)

            props: Dict[str, str] = {}
            for line in unfolded_lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].split(";")[0].strip()
                    val = parts[1].strip()
                    props[key] = val

            summary = self._unescape_ics(props.get("SUMMARY", ""))
            location = self._unescape_ics(props.get("LOCATION", ""))
            description = self._unescape_ics(props.get("DESCRIPTION", ""))
            dtstart_raw = props.get("DTSTART")
            dtend_raw = props.get("DTEND")
            url = props.get("URL") or "https://fossunited.org/events/timeline"
            category = props.get("CATEGORIES") or "Technology"

            if not summary or not dtstart_raw:
                continue

            full_context = f"{summary} {location} {description} {url}"
            if not self.is_hyderabad_event(full_context):
                continue

            start_dt = self._parse_ics_datetime(dtstart_raw)
            if not start_dt:
                continue

            end_dt = self._parse_ics_datetime(dtend_raw) if dtend_raw else None

            # Skip past events
            check_dt = end_dt if end_dt else (start_dt + timedelta(hours=3))
            if check_dt < now_ist:
                continue

            event_id = hashlib.sha256(f"foss_{summary}_{start_dt.isoformat()}".encode()).hexdigest()[:16]

            # Detect specific Hyderabad locality if present
            area = None
            for locality in ["Gachibowli", "Madhapur", "HITEC City", "Kondapur", "Begumpet", "Banjara Hills", "Jubilee Hills"]:
                if locality.lower() in location.lower():
                    area = locality
                    break

            items.append(
                EventItem(
                    id=event_id,
                    title=summary.strip(),
                    description=self.clean_text(description),
                    start_time=start_dt.isoformat(),
                    end_time=end_dt.isoformat() if end_dt else None,
                    formatted_date=start_dt.strftime("%a, %d %b %Y"),
                    formatted_time=start_dt.strftime("%I:%M %p"),
                    time_label=self.format_time_label(start_dt, now_ist),
                    venue=location.strip() if location else "Hyderabad",
                    area=area,
                    category=category.strip(),
                    city="Hyderabad",
                    source=self.source_name,
                    source_url=url.strip(),
                    source_type=self.source_type,
                )
            )

        return items

    def _parse_rss_content(self, xml_text: str, now_ist: datetime, force_hyderabad: bool = False) -> List[EventItem]:
        items: List[EventItem] = []
        try:
            root = ET.fromstring(xml_text)
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date_raw = item.findtext("pubDate", "")
                desc_raw = item.findtext("description", "")
                cat_raw = item.findtext("category", "") or "Technology"

                if not title:
                    continue

                full_context = f"{title} {desc_raw} {link}"
                if not force_hyderabad and not self.is_hyderabad_event(full_context):
                    continue

                start_dt = self._parse_rss_datetime(pub_date_raw) if pub_date_raw else None
                if start_dt and start_dt < now_ist:
                    continue

                clean_desc = self.clean_text(desc_raw)
                event_id = hashlib.sha256(f"foss_{title}_{link}".encode()).hexdigest()[:16]

                items.append(
                    EventItem(
                        id=event_id,
                        title=title.strip(),
                        description=clean_desc,
                        start_time=start_dt.isoformat() if start_dt else now_ist.isoformat(),
                        end_time=None,
                        formatted_date=start_dt.strftime("%a, %d %b %Y") if start_dt else "Upcoming",
                        formatted_time=start_dt.strftime("%I:%M %p") if start_dt else "Time TBA",
                        time_label=self.format_time_label(start_dt, now_ist) if start_dt else "Upcoming",
                        venue="Hyderabad",
                        area=None,
                        category=cat_raw.strip(),
                        city="Hyderabad",
                        source=self.source_name,
                        source_url=link.strip() if link else "https://fossunited.org/c/hyderabad",
                        source_type=self.source_type,
                    )
                )
        except Exception:
            pass

        return items
