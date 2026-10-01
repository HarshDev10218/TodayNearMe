import hashlib
import re
from datetime import datetime
from typing import List, Optional
import httpx

from app.models.civic_update import CivicUpdateItem
from app.services.civic_sources.base import BaseCivicSource, SourceResult, IST


class GhmcCivicSource(BaseCivicSource):
    """
    Civic Notice Source Adapter for Greater Hyderabad Municipal Corporation (GHMC).
    
    Status & Compliance:
    - Official portal: https://www.ghmc.gov.in/
    - Tenders/Notices page: https://www.ghmc.gov.in/Tenderspage.aspx
    - Information: Municipal notices, ward delimitations, property tax advisories, civic public works, sports/amenity notices.
    - Low-frequency, cached retrieval with respectful User-Agent.
    - Strictly non-blocking, isolated error handling.
    """

    PORTAL_URL = "https://www.ghmc.gov.in/"
    TENDERS_URL = "https://www.ghmc.gov.in/Tenderspage.aspx"

    @property
    def source_name(self) -> str:
        return "GHMC"

    @property
    def attribution(self) -> str:
        return "Greater Hyderabad Municipal Corporation (GHMC)"

    @property
    def source_type(self) -> str:
        return "official"

    def _normalize_ghmc_url(self, href: str) -> str:
        if not href or href == "#":
            return self.PORTAL_URL
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return f"https://www.ghmc.gov.in{href}"
        return f"https://www.ghmc.gov.in/{href}"

    def _parse_ticker_items(self, html_text: str) -> List[CivicUpdateItem]:
        updates: List[CivicUpdateItem] = []
        
        # Target the specific Flash News / Breaking News ticker container on GHMC portal
        ticker_containers = re.findall(
            r'(?:class=["\'][^"\']*(?:breaking-news-ticker|bn-news)[^"\']*["\']|id=["\'][^"\']*LstFlashNews[^"\']*["\'])[\s\S]*?<ul[^>]*>([\s\S]*?)</ul>',
            html_text,
            re.I,
        )

        ul_blocks = ticker_containers if ticker_containers else [html_text]

        for block in ul_blocks:
            items = re.findall(
                r'<li[^>]*>\s*<a\s+[^>]*href\s*=\s*["\']?([^"\'>\s]+)["\']?[^>]*>(.*?)</a>\s*</li>',
                block,
                re.DOTALL | re.I,
            )

            for raw_href, raw_text in items:
                title = self.clean_text(raw_text)
                if not title or len(title) < 6:
                    continue

                # Skip generic navigation actions
                if title.lower() in ("home", "about us", "contact us", "citizen login", "pay online", "login"):
                    continue

                # Extract any embedded date if present in title (e.g., "dt: 25.12.2025" or "2026")
                pub_date = None
                date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', title)
                if date_match:
                    d_str = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
                    parsed = self.parse_date_to_ist(d_str)
                    if parsed:
                        pub_date = parsed.isoformat()

                source_url = self._normalize_ghmc_url(raw_href)
                category = self.categorize_notice(title)
                notice_hash = hashlib.sha256(f"ghmc:{title}".encode()).hexdigest()[:12]

                updates.append(
                    CivicUpdateItem(
                        id=f"ghmc-notice-{notice_hash}",
                        title=title,
                        summary=None,
                        published_at=pub_date,
                        updated_at=None,
                        category=category,
                        source=self.source_name,
                        source_url=source_url,
                        source_type=self.source_type,
                        location="Hyderabad",
                        department="Greater Hyderabad Municipal Corporation",
                        scope="GHMC Area",
                        deadline=None,
                    )
                )

        return updates

    # Pattern to detect if a string is just a date/datetime (e.g. "11-09-2026 - 05:00 pm")
    _DATE_ONLY_PATTERN = re.compile(
        r'^[\d/.\-\s:]+(?:am|pm)?$',
        re.IGNORECASE
    )

    def _parse_tenders_table(self, html_text: str) -> List[CivicUpdateItem]:
        updates: List[CivicUpdateItem] = []
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_text, re.DOTALL | re.I)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.I)
            # Tenders table structure on GHMC portal:
            # 0: T.Type, 1: Name of the Work, 2: Start Date, 3: End Date, 4: Bid Opening Date
            if len(cells) < 4:
                continue

            raw_work = self.clean_text(cells[1])
            # Strip trailing "Download \d+" artifact if captured
            if raw_work:
                raw_work = re.sub(r'Download\s*\d+', '', raw_work, flags=re.I).strip()

            start_date_str = self.clean_text(cells[2])
            end_date_str = self.clean_text(cells[3])

            # Skip table headers and generic noise
            if not raw_work or raw_work.lower() in ("name of the work", "t.type", "general", "s.no", "type"):
                continue

            # Must be a substantive title of at least 12 characters and 2 words
            if len(raw_work) < 12 or self._DATE_ONLY_PATTERN.match(raw_work):
                continue
            words = [w for w in raw_work.split() if len(w) > 1]
            if len(words) < 2:
                continue

            # Extract direct document download link if present in row
            doc_match = re.search(r'href=(?:["\']?)([^"\'\s>]+)', row, re.I)
            source_url = self.TENDERS_URL
            if doc_match:
                href = doc_match.group(1).strip()
                if href.startswith("http"):
                    source_url = href
                elif href.startswith("/"):
                    source_url = f"https://www.ghmc.gov.in{href}"
                elif not href.startswith("#"):
                    source_url = f"https://www.ghmc.gov.in/{href}"

            start_dt = self.parse_date_to_ist(start_date_str) if start_date_str else None
            end_dt = self.parse_date_to_ist(end_date_str) if end_date_str else None

            published_at = start_dt.isoformat() if start_dt else None
            deadline = end_dt.strftime("%d %b %Y, %I:%M %p") if end_dt else None

            category = self.categorize_notice(raw_work)
            notice_hash = hashlib.sha256(f"ghmc-work:{raw_work}".encode()).hexdigest()[:12]

            updates.append(
                CivicUpdateItem(
                    id=f"ghmc-work-{notice_hash}",
                    title=raw_work,
                    summary=None,
                    published_at=published_at,
                    updated_at=None,
                    category=category,
                    source=self.source_name,
                    source_url=source_url,
                    source_type=self.source_type,
                    location="Hyderabad",
                    department="Greater Hyderabad Municipal Corporation",
                    scope="GHMC Area",
                    deadline=deadline,
                )
            )

        return updates

    async def fetch_updates(self, city: str = "Hyderabad") -> SourceResult:
        headers = {
            "User-Agent": "TodayNearMe/1.0 (Hyderabad Public Utility; contact@todaynearme.local)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        updates: List[CivicUpdateItem] = []
        errors = []

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True, verify=False) as client:
                # Query homepage ticker
                res_home = await client.get(self.PORTAL_URL)
                if res_home.status_code == 200:
                    updates.extend(self._parse_ticker_items(res_home.text))
                else:
                    errors.append(f"GHMC home returned HTTP {res_home.status_code}")

                # Query tenders / works page
                try:
                    res_tenders = await client.get(self.TENDERS_URL)
                    if res_tenders.status_code == 200:
                        updates.extend(self._parse_tenders_table(res_tenders.text))
                except Exception as te:
                    errors.append(f"Tenders page error: {te}")
        except httpx.TimeoutException:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="unavailable",
                attribution=self.attribution,
                message="Connection timed out while querying GHMC portal",
            )
        except Exception as e:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="unavailable",
                attribution=self.attribution,
                message=f"Could not reach GHMC portal: {e}",
            )

        if not updates:
            if errors:
                return SourceResult(
                    source_name=self.source_name,
                    updates=[],
                    status="unavailable",
                    attribution=self.attribution,
                    message="; ".join(errors),
                )
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="empty",
                attribution=self.attribution,
                message="No current public notices listed on GHMC portal",
            )

        return SourceResult(
            source_name=self.source_name,
            updates=updates,
            status="ok",
            attribution=self.attribution,
        )
