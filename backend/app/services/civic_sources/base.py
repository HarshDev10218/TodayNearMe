from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional, Tuple
import html
import re

from app.models.civic_update import CivicUpdateItem

# India Standard Time (UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30), name="IST")

CONTROLLED_CATEGORIES = {
    "Civic",
    "Government",
    "Transport",
    "Water",
    "Electricity",
    "Public Safety",
    "Municipal",
    "Public Services",
    "Other",
}


@dataclass
class SourceResult:
    """Encapsulates the result of querying an individual civic source adapter."""
    source_name: str
    updates: List[CivicUpdateItem] = field(default_factory=list)
    status: str = "ok"  # "ok" | "empty" | "unavailable" | "not_supported"
    attribution: str = ""
    message: Optional[str] = None


class BaseCivicSource(ABC):
    """
    Abstract interface for official civic notice and public update source adapters.
    Enforces ₹0 budget, privacy-first, and resilient source isolation.
    A failure in any one source adapter must never crash the service or block others.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the official source."""
        pass

    @property
    @abstractmethod
    def attribution(self) -> str:
        """Attribution label honoring source terms."""
        pass

    @property
    def source_type(self) -> str:
        """Classification: strictly 'official'."""
        return "official"

    @abstractmethod
    async def fetch_updates(self, city: str = "Hyderabad") -> SourceResult:
        """
        Fetch, parse, and normalize public updates from this official source.
        Returns a SourceResult with status ('ok', 'empty', 'unavailable', or 'not_supported').
        Never raises unhandled network or parsing exceptions.
        """
        pass

    @staticmethod
    def clean_text(text: Optional[str]) -> Optional[str]:
        """Strip HTML tags, repair broken CMS characters, and normalize whitespace."""
        if not text:
            return None
        unescaped = html.unescape(text)
        # Normalize non-standard whitespace (NBSP, zero-width space)
        cleaned = re.sub(r"[\u00a0\u200b\u200c\u200d]", " ", unescaped)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        # Normalize typographic quotes and dashes
        cleaned = re.sub(r"[\u2018\u2019\u201b]", "'", cleaned)
        cleaned = re.sub(r"[\u201c\u201d\u201f]", '"', cleaned)
        cleaned = re.sub(r"[\u2013\u2014]", " - ", cleaned)
        # Repair broken CMS unicode replacement characters (\ufffd or ?)
        cleaned = re.sub(r"Hon[\ufffd?]ble", "Hon'ble", cleaned, flags=re.I)
        cleaned = re.sub(r"(\w)[\ufffd?]s\b", r"\1's", cleaned, flags=re.I)
        cleaned = re.sub(r"(\w)\s*[\ufffd]\s*(\w)", r"\1 - \2", cleaned)
        cleaned = cleaned.replace("\ufffd", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if cleaned else None

    @staticmethod
    def categorize_notice(text: str) -> str:
        """
        Deterministic, rule-based classification into controlled categories.
        No AI used in V1. Defaults to 'Other' if classification is uncertain.
        """
        if not text:
            return "Other"
        norm = text.lower()

        # Water
        if any(k in norm for k in ["water", "drainage", "sewerage", "hmwssb", "pipeline", "drinking water", "water supply"]):
            return "Water"

        # Electricity
        if any(k in norm for k in ["electricity", "power supply", "tgspdcl", "tsspdcl", "substation", "grid", "load shedding", "power cut"]):
            return "Electricity"

        # Transport
        if any(k in norm for k in ["traffic", "metro", "tsrtc", "tgrtc", "rtc bus", "road closure", "diversion", "flyover", "transit", "corridor", "mrdcl"]):
            return "Transport"

        # Municipal
        if any(k in norm for k in ["ghmc", "property tax", "trade license", "sanitation", "garbage", "delimitation", "ward", "parks", "swimming pool", "street light", "urban biodiversity"]):
            return "Municipal"

        # Public Safety
        if any(k in norm for k in ["police", "fire service", "emergency", "flood", "disaster", "curfew", "advisory", "weather warning", "monsoon warning"]):
            return "Public Safety"

        # Civic (housing, land acquisition, citizen rights, voting)
        if any(k in norm for k in ["land acquisition", "2bhk", "housing", "polling station", "voter", "election", "pension", "ration", "encroachment"]):
            return "Civic"

        # Government (cabinet, orders, recruitment, gazette)
        if any(k in norm for k in ["cabinet", "government order", "gazette", "recruitment", "notification", "g.o.", "minister", "collectorate", "secretariat"]):
            return "Government"

        # Public Services (civil supplies, registration, meeseva, health)
        if any(k in norm for k in ["aadhaar", "meeseva", "certificate", "health center", "hospital", "clinic", "vaccination", "civil supplies"]):
            return "Public Services"

        return "Other"

    @staticmethod
    def _is_primarily_non_english(text: str) -> bool:
        """Return True if the text is predominantly non-ASCII (e.g., Telugu script)."""
        if not text:
            return False
        non_ascii = sum(1 for c in text if ord(c) > 127)
        return non_ascii > len(text) * 0.4

    @staticmethod
    def is_hyderabad_relevant(text: str, is_statewide_source: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Evaluates whether notice text is relevant to Hyderabad.
        Returns: (is_relevant, location, scope)
        - Excludes updates specifically localized to other non-Hyderabad districts.
        - Excludes non-English (e.g., Telugu-script-only) titles with no civic info extractable.
        - Accepts statewide updates from state portals only if they affect Hyderabad citizens specifically.
        """
        # Filter out predominantly non-ASCII/Telugu-script titles from state feeds
        non_ascii_count = sum(1 for c in text if ord(c) > 127)
        if len(text) > 0 and (non_ascii_count / len(text)) > 0.4:
            return (False, "Other", None)

        norm = text.lower()

        # Non-Hyderabad Telangana districts to strictly filter out
        other_districts = [
            "warangal", "hanumakonda", "karimnagar", "nizamabad", "khammam",
            "nalgonda", "mahabubnagar", "mahabubabad", "siddipet", "suryapet",
            "adilabad", "mancherial", "nirmal", "asifabad", "jagtial", "peddapalli",
            "sircilla", "rajanna sircilla", "bhadradri", "kothagudem", "kamareddy",
            "sangareddy", "medak", "vikarabad", "wanaparthy", "nagarkurnool",
            "jogulamba", "gadwal", "narayanpet", "mulugu", "jayashankar", "bhupalpally",
            "jangaon", "yadadri", "bhuvanagiri"
        ]

        # Explicit Hyderabad markers
        hyderabad_markers = [
            "hyderabad", "secunderabad", "cyberabad", "ghmc",
            "hitec city", "gachibowli", "madhapur", "kondapur",
            "begumpet", "banjara hills", "jubilee hills", "charminar",
            "somajiguda", "khairatabad", "saifabad", "nampally", "abids",
            "koti", "mehdipatnam", "ameerpet", "kukatpally", "miyapur",
            "dilsukhnagar", "lb nagar", "uppal", "tarnaka", "golconda",
            "langer house", "bholakpur", "tirumalagiri", "machabollaram",
            "mrdcl", "musheerabad", "malakpet", "sanathnagar"
        ]

        has_hyd = any(k in norm for k in hyderabad_markers)
        mentioned_other_district = any(re.search(r'\b' + re.escape(d) + r'\b', norm) for d in other_districts)

        # If it specifically names another district and does NOT mention Hyderabad
        if mentioned_other_district and not has_hyd:
            return (False, "Other", None)

        if has_hyd:
            return (True, "Hyderabad", "Hyderabad Area")

        # For state-level sources, use a strict set of genuinely statewide civic matters
        # that directly affect Hyderabad residents. Avoid political news, inaugurations elsewhere.
        if is_statewide_source:
            strict_statewide_civic = [
                "public holiday", "state cabinet", "cabinet approves",
                "power cut", "water supply", "load shedding",
                "citizens of telangana", "flood alert", "cyclone",
                "disaster management", "statewide advisory", "all districts",
                "transport strike", "fuel price", "curfew"
            ]
            if any(k in norm for k in strict_statewide_civic):
                return (True, "Telangana (Statewide)", "Statewide")

        return (False, "Unknown", None)

    @staticmethod
    def parse_date_to_ist(date_str: str) -> Optional[datetime]:
        """
        Parses various date string representations into an Asia/Kolkata datetime.
        Supports RFC 2822, ISO 8601, and Indian standard DD/MM/YYYY.
        """
        if not date_str or not date_str.strip():
            return None
        cleaned = date_str.strip()

        # 1. Try RFC 2822 (e.g., "Wed, 30 Sep 2026 09:56:00 +0000")
        try:
            dt = parsedate_to_datetime(cleaned)
            return dt.astimezone(IST)
        except Exception:
            pass

        # 2. Try standard Indian formats DD/MM/YYYY or DD-MM-YYYY with optional time
        for fmt in (
            "%d-%m-%Y - %I:%M %p",
            "%d/%m/%Y - %I:%M %p",
            "%d-%m-%Y %I:%M %p",
            "%d/%m/%Y %I:%M %p",
            "%d-%m-%Y - %H:%M",
            "%d/%m/%Y - %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.replace(tzinfo=IST)
            except ValueError:
                continue

        # 3. Try ISO formats
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.replace(tzinfo=IST)
            except ValueError:
                continue

        return None
