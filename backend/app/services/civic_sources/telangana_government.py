import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
import httpx

from app.models.civic_update import CivicUpdateItem
from app.services.civic_sources.base import BaseCivicSource, SourceResult, IST


class TelanganaGovernmentCivicSource(BaseCivicSource):
    """
    Civic Notice Source Adapter for Government of Telangana (Official State Portal).
    
    Status & Compliance:
    - Official state portal feed: https://www.telangana.gov.in/feed/
    - Method: Public structured RSS 2.0 feed provided natively by telangana.gov.in.
    - Information: State cabinet decisions, government orders, state-wide advisories, public utility notifications.
    - Filtering: Strict Hyderabad relevance filter ensures only Hyderabad-specific or genuine statewide
      matters affecting Hyderabad citizens are surfaced. Unrelated district-specific updates are excluded.
    - Respects robots.txt / usage terms with respectful headers and caching.
    """

    FEED_URL = "https://www.telangana.gov.in/feed/"

    @property
    def source_name(self) -> str:
        return "Government of Telangana"

    @property
    def attribution(self) -> str:
        return "Government of Telangana Official Portal (telangana.gov.in)"

    @property
    def source_type(self) -> str:
        return "official"

    def _parse_feed_xml(self, content_bytes: bytes) -> List[CivicUpdateItem]:
        updates: List[CivicUpdateItem] = []
        try:
            root = ET.fromstring(content_bytes)
        except Exception:
            return updates

        channel = root.find("channel")
        if channel is None:
            return updates

        for item in channel.findall("item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            desc_elem = item.find("description")

            title = self.clean_text(title_elem.text) if title_elem is not None else None
            if not title:
                continue

            link = link_elem.text.strip() if link_elem is not None and link_elem.text else self.FEED_URL
            pub_date_str = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else None
            raw_desc = self.clean_text(desc_elem.text) if desc_elem is not None else None

            # Relevance evaluation: must be relevant to Hyderabad or statewide
            full_context = f"{title} {raw_desc or ''}"
            is_relevant, location, scope = self.is_hyderabad_relevant(full_context, is_statewide_source=True)

            if not is_relevant:
                continue

            pub_dt = self.parse_date_to_ist(pub_date_str) if pub_date_str else None
            published_at = pub_dt.isoformat() if pub_dt else None

            # Summary: only display if meaningful and distinct from title
            summary = None
            if raw_desc and len(raw_desc) > 10 and raw_desc.strip().lower() != title.strip().lower():
                # Truncate clean summary to a readable 200 chars if long
                summary = raw_desc[:240].rsplit(" ", 1)[0] + "..." if len(raw_desc) > 240 else raw_desc

            category = self.categorize_notice(full_context)
            notice_hash = hashlib.sha256(f"telangana:{link or title}".encode()).hexdigest()[:12]

            updates.append(
                CivicUpdateItem(
                    id=f"ts-gov-{notice_hash}",
                    title=title,
                    summary=summary,
                    published_at=published_at,
                    updated_at=None,
                    category=category,
                    source=self.source_name,
                    source_url=link,
                    source_type=self.source_type,
                    location=location,
                    department="Government of Telangana",
                    scope=scope,
                    deadline=None,
                )
            )

        return updates

    async def fetch_updates(self, city: str = "Hyderabad") -> SourceResult:
        headers = {
            "User-Agent": "TodayNearMe/1.0 (Hyderabad Public Utility; contact@todaynearme.local)",
            "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True, verify=False) as client:
                res = await client.get(self.FEED_URL)
                if res.status_code != 200:
                    return SourceResult(
                        source_name=self.source_name,
                        updates=[],
                        status="unavailable",
                        attribution=self.attribution,
                        message=f"Telangana state portal returned HTTP {res.status_code}",
                    )
                content_bytes = res.content
        except httpx.TimeoutException:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="unavailable",
                attribution=self.attribution,
                message="Connection timed out while querying Government of Telangana portal",
            )
        except Exception as e:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="unavailable",
                attribution=self.attribution,
                message=f"Could not reach Telangana Government portal: {e}",
            )

        updates = self._parse_feed_xml(content_bytes)

        if not updates:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="empty",
                attribution=self.attribution,
                message="No recent Hyderabad-relevant notices in state portal feed",
            )

        return SourceResult(
            source_name=self.source_name,
            updates=updates,
            status="ok",
            attribution=self.attribution,
        )
