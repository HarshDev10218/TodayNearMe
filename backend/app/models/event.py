from typing import List, Optional
from pydantic import BaseModel, Field


class SourceStatus(BaseModel):
    name: str = Field(..., description="Monitored public source name")
    status: str = Field(..., description="Source status: 'ok' | 'empty' | 'unavailable'")
    message: Optional[str] = Field(None, description="Descriptive status note")


class EventItem(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Official title of the event")
    description: Optional[str] = Field(None, description="Event description or summary")
    start_time: str = Field(..., description="Event start timestamp in ISO format (Asia/Kolkata)")
    end_time: Optional[str] = Field(None, description="Event end timestamp in ISO format (Asia/Kolkata)")
    formatted_date: Optional[str] = Field(None, description="Human-readable event date (e.g. 'Sat, 03 Oct')")
    formatted_time: Optional[str] = Field(None, description="Human-readable event time in IST (e.g. '10:00 AM')")
    time_label: Optional[str] = Field(None, description="Temporal bucket: 'Today' | 'Tomorrow' | 'Upcoming'")
    venue: Optional[str] = Field(None, description="Physical venue or online platform")
    area: Optional[str] = Field(None, description="Locality or area within Hyderabad")
    category: Optional[str] = Field(None, description="Event category (e.g. Technology, Workshop, Cultural)")
    city: str = Field(default="Hyderabad", description="Target city for events")
    source: str = Field(..., description="Authoritative verified source organization")
    source_url: str = Field(..., description="Direct link to verified source event page")
    source_type: str = Field(default="community", description="Source classification: 'official' | 'community'")


class EventResponse(BaseModel):
    events: List[EventItem] = Field(default_factory=list, description="Chronologically sorted upcoming events")
    city: str = Field(default="Hyderabad", description="Target city for events")
    count: int = Field(..., ge=0, description="Total count of upcoming events returned")
    checked_at: str = Field(..., description="ISO timestamp when events were queried")
    source: str = Field(..., description="Authoritative source attribution notice")
    sources: List[SourceStatus] = Field(default_factory=list, description="Status breakdown of monitored sources")
    cached: bool = Field(default=False, description="Whether this response was served from cache")
    message: Optional[str] = Field(None, description="Status or descriptive notice")
    all_unavailable: bool = Field(default=False, description="True if all monitored sources were temporarily unavailable")
