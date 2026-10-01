from typing import List, Optional
from pydantic import BaseModel, Field


class SourceStatus(BaseModel):
    name: str = Field(..., description="Monitored official source name")
    status: str = Field(..., description="Source status: 'ok' | 'empty' | 'unavailable' | 'not_supported'")
    message: Optional[str] = Field(None, description="Descriptive status note")


class CivicUpdateItem(BaseModel):
    id: str = Field(..., description="Unique civic update identifier")
    title: str = Field(..., description="Official title or headline of the civic notice")
    summary: Optional[str] = Field(None, description="Official summary or description if provided by source")
    published_at: Optional[str] = Field(None, description="Publication timestamp in ISO format (Asia/Kolkata)")
    updated_at: Optional[str] = Field(None, description="Update or effective timestamp in ISO format (Asia/Kolkata)")
    category: str = Field(default="Other", description="Controlled category: Civic | Government | Transport | Water | Electricity | Public Safety | Municipal | Public Services | Other")
    source: str = Field(..., description="Authoritative official government organization")
    source_url: str = Field(..., description="Direct link to official notice or document")
    source_type: str = Field(default="official", description="Source classification: strictly 'official'")
    location: str = Field(default="Hyderabad", description="Geographic scope: 'Hyderabad' or 'Telangana (Statewide)'")
    department: Optional[str] = Field(None, description="Department name if explicitly provided by source")
    scope: Optional[str] = Field(None, description="Scope detail: e.g. 'Hyderabad District', 'GHMC Area', 'Statewide'")
    deadline: Optional[str] = Field(None, description="Official end date or deadline if specified by source")


class CivicUpdatesResponse(BaseModel):
    updates: List[CivicUpdateItem] = Field(default_factory=list, description="Sorted list of verified civic updates")
    city: str = Field(default="Hyderabad", description="Target city for civic updates")
    count: int = Field(default=0, ge=0, description="Total count of civic updates returned")
    checked_at: str = Field(..., description="ISO timestamp when official sources were queried")
    source: str = Field(..., description="Authoritative source attribution notice")
    sources: List[SourceStatus] = Field(default_factory=list, description="Status breakdown of monitored sources")
    cached: bool = Field(default=False, description="Whether this response was served from backend cache")
    message: Optional[str] = Field(None, description="Status notice or explanatory text")
    all_unavailable: bool = Field(default=False, description="True if all monitored sources were temporarily unavailable")
