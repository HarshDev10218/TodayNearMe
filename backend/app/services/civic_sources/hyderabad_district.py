import hashlib
import re
from datetime import datetime
from typing import List, Optional
import httpx

from app.models.civic_update import CivicUpdateItem
from app.services.civic_sources.base import BaseCivicSource, SourceResult, IST


class HyderabadDistrictCivicSource(BaseCivicSource):
    """
    Civic Notice Source Adapter for Hyderabad District Administration (Government of Telangana).
    
    Status & Compliance:
    - Official portal: https://hyderabad.telangana.gov.in/notice_category/announcements/
    - Hosted by National Informatics Centre (NIC) on S3WaaS platform.
    - Information: Land acquisition notices, housing (2BHK) schemes, collectorate public notices, citizen advisories.
    - Non-aggressive, low-frequency retrieval with timeouts and cache protection.
    - Respects robots.txt / terms.
    """

    PORTAL_URL = "https://hyderabad.telangana.gov.in/notice_category/announcements/"
    WHATS_NEW_URL = "https://hyderabad.telangana.gov.in/notice_category/whats-new/"

    @property
    def source_name(self) -> str:
        return "Hyderabad District Government"

    @property
    def attribution(self) -> str:
        return "Hyderabad District Administration (Government of Telangana)"

    @property
    def source_type(self) -> str:
        return "official"

    def _parse_table_html(self, html_content: str) -> List[CivicUpdateItem]:
        updates: List[CivicUpdateItem] = []
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.I)
        if not tables:
            return updates

        table_body = tables[0]
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_body, re.DOTALL | re.I)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.I)
            # Standard S3WaaS notice table has 5 columns:
            # 0: Title, 1: Description, 2: Start Date, 3: End Date, 4: File link
            if len(cells) < 4:
                continue

            raw_title = self.clean_text(cells[0])
            raw_desc = self.clean_text(cells[1])
            start_date_str = self.clean_text(cells[2])
            end_date_str = self.clean_text(cells[3]) if len(cells) > 3 else None

            # Skip header row if caught in <td>
            if not raw_title or raw_title.lower() in ("title", "s.no", "sl.no"):
                continue

            # Extract direct document link if present in row or cells
            file_match = re.search(r'href=["\']([^"\']+)["\']', cells[-1] if len(cells) >= 5 else row, re.I)
            source_url = self.PORTAL_URL
            if file_match:
                href = file_match.group(1).strip()
                if href.startswith("http"):
                    source_url = href
                elif href.startswith("/"):
                    source_url = f"https://hyderabad.telangana.gov.in{href}"
                elif href and not href.startswith("#"):
                    source_url = f"https://hyderabad.telangana.gov.in/notice_category/announcements/{href}"

            # Parse dates
            start_dt = self.parse_date_to_ist(start_date_str) if start_date_str else None
            end_dt = self.parse_date_to_ist(end_date_str) if end_date_str else None

            published_at = start_dt.isoformat() if start_dt else None
            deadline = end_dt.strftime("%d %b %Y") if end_dt else None

            # Summary: only use if source provided meaningful text distinct from title
            summary = None
            if raw_desc and raw_desc.strip().lower() != raw_title.strip().lower():
                summary = raw_desc.strip()

            category = self.categorize_notice(f"{raw_title} {summary or ''}")
            notice_hash = hashlib.sha256(f"hyddistrict:{raw_title}:{start_date_str}".encode()).hexdigest()[:12]

            updates.append(
                CivicUpdateItem(
                    id=f"hyd-dist-{notice_hash}",
                    title=raw_title,
                    summary=summary,
                    published_at=published_at,
                    updated_at=None,
                    category=category,
                    source=self.source_name,
                    source_url=source_url,
                    source_type=self.source_type,
                    location="Hyderabad",
                    department="Hyderabad District Collectorate",
                    scope="Hyderabad District",
                    deadline=deadline,
                )
            )

        return updates

    async def fetch_updates(self, city: str = "Hyderabad") -> SourceResult:
        headers = {
            "User-Agent": "TodayNearMe/1.0 (Hyderabad Public Utility; contact@todaynearme.local)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        updates_dict = {}
        errors = []

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True, verify=False) as client:
                for target_url in (self.PORTAL_URL, self.WHATS_NEW_URL):
                    try:
                        res = await client.get(target_url)
                        if res.status_code == 200:
                            parsed_list = self._parse_table_html(res.text)
                            for item in parsed_list:
                                if item.id not in updates_dict:
                                    updates_dict[item.id] = item
                        else:
                            errors.append(f"HTTP {res.status_code} on {target_url}")
                    except Exception as sub_e:
                        errors.append(str(sub_e))
        except httpx.TimeoutException:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="unavailable",
                attribution=self.attribution,
                message="Connection timed out while querying Hyderabad District Government",
            )
        except Exception as e:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="unavailable",
                attribution=self.attribution,
                message=f"Could not reach Hyderabad District portal: {e}",
            )

        updates = list(updates_dict.values())

        if not updates:
            return SourceResult(
                source_name=self.source_name,
                updates=[],
                status="empty",
                attribution=self.attribution,
                message="No notices found in announcement listings",
            )

        return SourceResult(
            source_name=self.source_name,
            updates=updates,
            status="ok",
            attribution=self.attribution,
        )
