from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Supported controlled categories for Nearby Places
CategoryType = Literal[
    "hospital",
    "pharmacy",
    "police",
    "atm",
    "park",
    "college",
    "government",
    "transport",
    "petrol_station",
]

CATEGORY_LABELS = {
    "hospital": "Hospitals",
    "pharmacy": "Pharmacies",
    "police": "Police Stations",
    "atm": "ATMs",
    "park": "Parks",
    "college": "Colleges & Universities",
    "government": "Government Facilities",
    "transport": "Metro & Transit",
    "petrol_station": "Petrol Stations",
}


class PlaceLocation(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate queried")
    longitude: float = Field(..., description="Longitude coordinate queried")
    label: str = Field(default="Hyderabad (Default)", description="Location description")


class PlaceItem(BaseModel):
    id: str = Field(..., description="Unique place identifier from OpenStreetMap")
    name: str = Field(..., description="Official place / amenity name")
    category: str = Field(..., description="Controlled category identifier")
    category_label: str = Field(..., description="Human-readable category label")
    latitude: float = Field(..., description="Latitude coordinate of the place")
    longitude: float = Field(..., description="Longitude coordinate of the place")
    distance_m: int = Field(..., ge=0, description="Calculated distance from user in meters")
    distance_formatted: str = Field(..., description="Human-readable distance (e.g. '850 m', '1.4 km')")
    address: Optional[str] = Field(None, description="Street / locality address if available in OSM")
    source: str = Field(default="OpenStreetMap", description="Authoritative data source")


class PlacesResponse(BaseModel):
    places: List[PlaceItem] = Field(default_factory=list, description="List of nearby places sorted by distance")
    location: PlaceLocation
    category: str = Field(..., description="Requested category identifier")
    category_label: str = Field(..., description="Human-readable category label")
    count: int = Field(..., ge=0, description="Number of places found")
    source: str = Field(
        default="© OpenStreetMap contributors",
        description="Official OpenStreetMap attribution notice",
    )
    attribution_url: str = Field(
        default="https://www.openstreetmap.org/copyright",
        description="OpenStreetMap license & copyright link",
    )
    cached: bool = Field(default=False, description="Whether this response was served from cache")
