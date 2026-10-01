from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AlertLocation(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    label: str = Field(default="Hyderabad (Default)", description="Location description")


class AlertItem(BaseModel):
    id: str = Field(..., description="Unique alert identifier")
    title: str = Field(..., description="Headline / title of the alert")
    severity: Literal["low", "moderate", "severe", "extreme"] = Field(
        ..., description="Standardized severity level"
    )
    description: str = Field(..., description="Official alert guidance and details")
    start_time: Optional[str] = Field(None, description="Alert onset / effective time")
    end_time: Optional[str] = Field(None, description="Alert expiration time")
    source: str = Field(
        default="India Meteorological Department (IMD)",
        description="Official issuing meteorological authority",
    )
    issued_at: Optional[str] = Field(None, description="Timestamp when the warning was published")
    area_desc: Optional[str] = Field(None, description="Affected geographic districts/zones")


class AlertResponse(BaseModel):
    alerts: List[AlertItem] = Field(default_factory=list, description="List of active weather alerts")
    location: AlertLocation
    has_active_alerts: bool = Field(default=False, description="Flag indicating if any alerts are active")
    source_status: str = Field(
        default="Official Meteorological Authority (IMD)",
        description="Official source attribution and status notes",
    )
    checked_at: str = Field(..., description="Timestamp of when alerts were checked")
    cached: bool = Field(default=False, description="Whether this response was served from cache")
