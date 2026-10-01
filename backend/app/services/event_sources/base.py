from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import html
import re

from app.models.event import EventItem, SourceStatus

# India Standard Time (UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


@dataclass
class SourceResult:
    """Encapsulates the result of querying an individual event source adapter."""
    source_name: str
    events: List[EventItem] = field(default_factory=list)
    status: str = "ok"  # "ok" | "empty" | "unavailable"
    attribution: str = ""
    message: Optional[str] = None


class BaseEventSource(ABC):
    """
    Abstract interface for public event source adapters.
    Enforces ₹0 budget, privacy-first, and resilient source isolation.
    A failure in any one source adapter must never crash the service.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the source."""
        pass

    @property
    @abstractmethod
    def attribution(self) -> str:
        """Attribution label honoring source terms."""
        pass

    @property
    def source_type(self) -> str:
        """Classification: 'official' or 'community'."""
        return "official"

    @abstractmethod
    async def fetch_events(self, city: str = "Hyderabad") -> SourceResult:
        """
        Fetch and parse events from this public source.
        Returns a SourceResult with status ('ok', 'empty', or 'unavailable').
        Never raises unhandled network or parsing exceptions.
        """
        pass

    # Common utility helpers
    @staticmethod
    def clean_text(text: Optional[str]) -> Optional[str]:
        """Strip HTML tags and normalize whitespace."""
        if not text:
            return None
        unescaped = html.unescape(text)
        cleaned = re.sub(r"<[^>]+>", " ", unescaped)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if cleaned else None

    @staticmethod
    def format_time_label(event_dt: datetime, now_ist: datetime) -> str:
        """Assign temporal bucket: Today | Tomorrow | Upcoming."""
        event_date = event_dt.date()
        today_date = now_ist.date()
        tomorrow_date = today_date + timedelta(days=1)

        if event_date == today_date:
            return "Today"
        elif event_date == tomorrow_date:
            return "Tomorrow"
        else:
            return "Upcoming"

    @staticmethod
    def is_hyderabad_event(text: str) -> bool:
        """
        Checks whether the event text or venue has clear Hyderabad relevance
        and excludes non-Hyderabad cities/districts.
        """
        norm = text.lower()
        
        # Explicit non-Hyderabad exclusion list
        non_hyderabad = [
            "warangal", "karimnagar", "nizamabad", "khammam", "nalgonda",
            "mahabubnagar", "ramagundam", "siddipet", "suryapet", "adilabad",
            "vijayawada", "visakhapatnam", "vizag", "guntur", "tirupati",
            "bengaluru", "bangalore", "chennai", "delhi", "mumbai", "pune",
            "kolkata", "kerala", "kochi", "trivandrum"
        ]
        
        # Positive Hyderabad keywords & localities
        hyderabad_markers = [
            "hyderabad", "secunderabad", "cyberabad",
            "t-hub", "t-works", "hitec city", "gachibowli", "madhapur",
            "kondapur", "iiit-h", "iiith", "ravindra bharathi", "shilparamam",
            "begumpet", "banjara hills", "jubilee hills", "charminar",
            "somajiguda", "khairatabad", "saifabad", "nampally", "abids",
            "koti", "mehdipatnam", "ameerpet", "kukatpally", "miyapur",
            "dilsukhnagar", "lb nagar", "uppal", "tarnaka", "osmania"
        ]

        has_hyd = any(k in norm for k in hyderabad_markers)
        has_non_hyd = any(re.search(r'\b' + re.escape(n) + r'\b', norm) for n in non_hyderabad)

        # If it specifically mentions another city without mentioning Hyderabad, exclude
        if has_non_hyd and not has_hyd:
            return False

        return has_hyd
