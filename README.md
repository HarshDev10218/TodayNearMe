# TodayNearMe — Hyderabad Local Utility

TodayNearMe is a free, minimalist, and functional local information utility for Hyderabad residents. It aggregates live weather, safety alerts, nearby essential services, local events, and civic notices.

---

## Architecture & Weather Data Flow

The application follows a decoupled client-server architecture:

```
Browser / Default Location
            ↓
React Location Layer (useLocation)
            ↓
React Weather Layer (useWeather / fetchWeather)
            ↓
Vite Dev Proxy (/api/weather)
            ↓
FastAPI Backend (GET /api/weather?latitude=...&longitude=...)
            ↓
Weather Service & In-Memory Cache (10-min TTL)
            ↓
External Provider: Open-Meteo API
            ↓
Response Normalization (Hyderabad units: °C, km/h, WMO translation)
            ↓
React Weather Component (Render live metrics & forecast)
```

**Key Architectural Guarantees:**
- **Zero Provider Leakage**: The React frontend never communicates directly with external weather providers. It interacts exclusively with our `/api/weather` endpoint.
- **Privacy-First**: Coordinates remain in React state for the active session only. Coordinates are never persisted to databases or local storage.
- **Hyderabad Fallback**: When GPS is unavailable or declined, the system automatically uses default Hyderabad coordinates (`17.3850° N, 78.4867° E`).
- **Resilient Caching**: Weather data is cached in-memory on the backend for 10 minutes (keyed by ~1.1 km coordinate grids) to prevent rate-limit exhaustion and reduce latency.

---

## Getting Started

### 1. Prerequisites
- **Node.js**: v18+ (tested on v24.18)
- **Python**: v3.10+ (tested on v3.14)

---

### 2. Backend Setup (FastAPI)

1. Navigate to the project root and create a Python virtual environment:
   ```bash
   python -m venv backend/venv
   ```

2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\backend\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source backend/venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp backend/.env.example backend/.env
   ```
   *(Open-Meteo requires no API key for standard non-commercial use, so default values work out of the box).*

5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```

   The backend will be live at:
   - **API Base**: `http://127.0.0.1:8000`
   - **Health Check**: `http://127.0.0.1:8000/health`
   - **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

---

### 3. Frontend Setup (React + Vite)

1. In a separate terminal, install npm dependencies (if not already installed):
   ```bash
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```

3. Open your browser:
   - **Frontend App**: `http://localhost:5173/`

*(Vite is configured with a development proxy that forwards requests from `/api/*` and `/health` directly to `http://127.0.0.1:8000`).*

---

## API Endpoints

### 1. `GET /health`
Returns service operational health.
```json
{
  "status": "ok",
  "service": "TodayNearMe API",
  "environment": "development",
  "version": "1.0.0"
}
```

### 2. `GET /api/weather`
Returns normalized weather data.

**Query Parameters:**
- `latitude` *(optional, float between -90.0 and 90.0)*
- `longitude` *(optional, float between -180.0 and 180.0)*

*Note: If coordinates are omitted, the backend defaults to Hyderabad (`17.3850, 78.4867`). Both coordinates must be provided together if specified.*

**Example Response:**
```json
{
  "location": {
    "latitude": 17.385,
    "longitude": 78.4867,
    "label": "Hyderabad (Default)"
  },
  "current": {
    "temperature": 28.0,
    "feels_like": 30.4,
    "condition": "Clear Sky",
    "condition_code": "clear",
    "humidity": 57,
    "wind_speed": 5.6,
    "wind_direction": "E",
    "precipitation_probability": 2,
    "surface_pressure": 959.5,
    "temp_high": 33.6,
    "temp_low": 24.7
  },
  "hourly": [
    {
      "time": "12 AM",
      "temperature": 26.9,
      "condition": "Clear Sky",
      "precipitation_probability": 0
    }
  ],
  "forecast": [
    {
      "day": "Today",
      "date": "Thu, Oct 01",
      "condition": "Overcast",
      "temp_max": 33.6,
      "temp_min": 24.7,
      "rain_probability": 2
    }
  ],
  "observed_at": "2026-10-01T22:15",
  "source": "Open-Meteo (Public Meteorological Service)",
  "cached": true
```

### 3. `GET /api/alerts`
Returns active official weather alerts and meteorological advisories.

**Query Parameters:**
- `latitude` *(optional, float between -90.0 and 90.0)*
- `longitude` *(optional, float between -180.0 and 180.0)*

*Note: When coordinates are omitted, the endpoint defaults to Hyderabad (`17.3850, 78.4867`).*

**Example Response (No Active Alerts):**
```json
{
  "alerts": [],
  "location": {
    "latitude": 17.385,
    "longitude": 78.4867,
    "label": "Hyderabad (Default)"
  },
  "has_active_alerts": false,
  "source_status": "India Meteorological Department (IMD) — No active weather warnings for Hyderabad / Telangana zone.",
  "checked_at": "2026-10-01T22:32:00.000Z",
  "cached": false
}
```

**Example Response (Active Warning):**
```json
{
  "alerts": [
    {
      "id": "alert-imd-hyd-20261001-01",
      "title": "Heavy Rain & Thunderstorm Advisory",
      "severity": "moderate",
      "description": "Thunderstorms accompanied by lightning and gusty winds (30-40 kmph) likely to occur in parts of Hyderabad and surrounding districts.",
      "start_time": "2026-10-01T15:00:00+05:30",
      "end_time": "2026-10-01T21:00:00+05:30",
      "source": "India Meteorological Department (IMD)",
      "issued_at": "2026-10-01T14:30:00+05:30",
      "area_desc": "Hyderabad, Rangareddy, Medchal-Malkajgiri"
    }
  ],
  "location": {
    "latitude": 17.385,
    "longitude": 78.4867,
    "label": "Hyderabad (Default)"
  },
  "has_active_alerts": true,
  "source_status": "Official Weather Warnings via India Meteorological Department (IMD)",
  "checked_at": "2026-10-01T22:32:00.000Z",
  "cached": false
}
```

### 4. `GET /api/places`
Returns nearby public amenities and essential places sorted by proximity.

**Query Parameters:**
- `latitude` *(optional, float between -90.0 and 90.0)*
- `longitude` *(optional, float between -180.0 and 180.0)*
- `category` *(optional, string, default: `hospital`)*. Allowed values: `hospital`, `pharmacy`, `police`, `atm`, `park`, `college`, `government`, `transport`, `petrol_station`.

*Note: Coordinates default to Hyderabad fallback (`17.3850, 78.4867`) if omitted.*

**Example Response:**
```json
{
  "places": [
    {
      "id": "osm-node-898965110",
      "name": "Fernandez Hospital",
      "category": "hospital",
      "category_label": "Hospitals",
      "latitude": 17.3934,
      "longitude": 78.4812,
      "distance_m": 1120,
      "distance_formatted": "1.1 km",
      "address": "D.No: 4-1-1230, Opp. YWCA, Abids Road, Bogulkunta",
      "source": "OpenStreetMap"
    }
  ],
  "location": {
    "latitude": 17.385,
    "longitude": 78.4867,
    "label": "Hyderabad (Default)"
  },
  "category": "hospital",
  "category_label": "Hospitals",
  "count": 10,
  "source": "© OpenStreetMap contributors",
  "attribution_url": "https://www.openstreetmap.org/copyright",
  "cached": false
}
```

---

## Nearby Places Architecture & Data Source

### 1. Data Flow Architecture
```
Location Layer (Browser Geolocation / Hyderabad Fallback)
                        ↓
            React usePlaces Hook
                        ↓
         Vite Proxy (/api/places)
                        ↓
           FastAPI Backend (/api/places)
                        ↓
            PlacesService & In-Memory Cache (15-min TTL)
                        ↓
      OpenStreetMap Overpass API (Bounding Box Query)
                        ↓
      Haversine Distance Calculation & Normalization
                        ↓
      Response (Closest 10 places sorted by proximity)
                        ↓
      React Frontend (Nearby Places Component)
```

### 2. Data Source, Licensing & Attribution
- **Authoritative Source**: Geographic POI data is sourced from **OpenStreetMap (OSM)** via community Overpass API instances.
- **Licensing**: OpenStreetMap data is licensed under the **Open Data Commons Open Database License (ODbL)** by the OpenStreetMap Foundation (OSMF).
- **Attribution Requirement**: In compliance with the ODbL license, the UI visibly attributes:
  > **Data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) (ODbL)**
- **Honest Data Rule**: TodayNearMe never invents fake places, addresses, or phone numbers. Only verified public attributes mapped in OpenStreetMap are displayed. Missing fields are omitted rather than fabricated.

### 3. Supported Categories & Tag Mappings
Each category is validated against a strict backend whitelist and mapped to specific OpenStreetMap tag clauses:
| Category Identifier | Category Label | OpenStreetMap Tag Clause | Search Radius |
| :--- | :--- | :--- | :--- |
| `hospital` | Hospitals | `nwr["amenity"="hospital"]["name"]` | ~3.0 km |
| `pharmacy` | Pharmacies | `nwr["amenity"="pharmacy"]["name"]` | ~2.5 km |
| `police` | Police Stations | `nwr["amenity"="police"]["name"]` | ~3.5 km |
| `atm` | ATMs | `nwr["amenity"="atm"]` | ~2.0 km |
| `park` | Parks | `nwr["leisure"="park"]["name"]` | ~3.0 km |
| `college` | Colleges & Universities | `nwr["amenity"~"college\|university"]["name"]` | ~3.5 km |
| `government` | Government Facilities | `nwr["office"="government"]["name"]` | ~3.5 km |
| `transport` | Metro & Transit | `nwr["railway"~"station\|subway_entrance"]["name"]` | ~3.5 km |
| `petrol_station` | Petrol Stations | `nwr["amenity"="fuel"]["name"]` | ~3.0 km |

### 4. Distance Calculation & Sorting
- Straight-line geographic distance is computed on the backend using the spherical **Haversine formula** ($R = 6,371\text{ km}$).
- Results are formatted for human readability (`850 m` for distances under 1 km, `1.4 km` for distances 1 km and above).
- Results are sorted in ascending order of distance, returning the closest 10 mapped facilities.

### 5. Backend Caching & Upstream Courtesy
- Responses are cached in-memory on the backend for **15 minutes (900 seconds)** keyed by grid resolution (`~1.1 km` rounded coordinates + category).
- When a user changes category or revisits a category, cached responses return instantly without making repetitive upstream network calls.
- The frontend only fetches the currently active category (defaulting to Hospitals), never querying all categories simultaneously on initial page load.

### 6. Limitations & Scope Boundaries
- **Not a Navigation / Turn-by-Turn System**: TodayNearMe is a local utility discovery tool. It does not provide routing, GPS tracking, or transit scheduling.
- **Approximate Coordinates**: Browser coordinates are approximate, and OpenStreetMap coordinates represent mapped centroid or entrance points. Distances represent proximity rankings, not exact meter-level guarantees.
- **Public Infrastructure Constraints**: Overpass API instances are community-supported shared resources with load shedding during peak hours. The backend employs multiple official server mirrors (`lz4.overpass-api.de`, `z.overpass-api.de`, `overpass-api.de`) and handles timeouts gracefully with a non-intrusive error state.

### 5. `GET /api/events`
Returns upcoming public and community gatherings, workshops, conferences, and official notices in Hyderabad aggregated from monitored public sources.

> **Important Scope Notice**: TodayNearMe is **NOT** a comprehensive listing of every event happening in Hyderabad. It aggregates upcoming events discovered exclusively from the public sources explicitly monitored by the platform.

**Query Parameters:**
- `city` *(optional, string, default: `Hyderabad`)*. Must strictly be `Hyderabad` in V1 (rejects non-Hyderabad queries with HTTP 400).
- `refresh` *(optional, boolean, default: `false`)*. When `true`, bypasses backend in-memory cache to query upstream sources immediately (powers the user-controlled "Check Again" button).

**Example Response (Empty State — Valid when monitored sources list zero upcoming Hyderabad events):**
```json
{
  "events": [],
  "city": "Hyderabad",
  "count": 0,
  "checked_at": "2026-10-02T00:14:56.123456+05:30",
  "source": "Aggregated from public sources: FOSS United, Telangana Tourism, Hyderabad District Government",
  "sources": [
    {
      "name": "FOSS United",
      "status": "empty",
      "message": "No upcoming events scheduled"
    },
    {
      "name": "Telangana Tourism",
      "status": "empty",
      "message": "No upcoming events listed on official portal"
    },
    {
      "name": "Hyderabad District Government",
      "status": "empty",
      "message": "No current events listed on district portal"
    }
  ],
  "cached": false,
  "message": "We couldn't find upcoming Hyderabad events in the public sources currently monitored by TodayNearMe.",
  "all_unavailable": false
}
```

**Example Response (Populated & Deduplicated Across Sources):**
```json
{
  "events": [
    {
      "id": "c7a8b9f1d2e34567",
      "title": "Hyderabad Open Source Tech Meetup",
      "description": "Monthly community gathering of developers discussing Python, Rust and open-source tooling in Hyderabad.",
      "start_time": "2026-10-05T18:30:00+05:30",
      "end_time": "2026-10-05T20:30:00+05:30",
      "formatted_date": "Mon, 05 Oct 2026",
      "formatted_time": "06:30 PM",
      "time_label": "Upcoming",
      "venue": "T-Hub Phase 2, Madhapur, Hyderabad",
      "area": "Madhapur",
      "category": "Technology",
      "city": "Hyderabad",
      "source": "FOSS United",
      "source_url": "https://fossunited.org/c/hyderabad",
      "source_type": "community"
    },
    {
      "id": "f2d3e4a5b6c78901",
      "title": "Hyderabad Heritage & Tourism Walk",
      "description": null,
      "start_time": "2026-10-10T09:00:00+05:30",
      "end_time": null,
      "formatted_date": "Sat, 10 Oct 2026",
      "formatted_time": "Time TBA",
      "time_label": "Upcoming",
      "venue": "Golconda Fort, Hyderabad",
      "area": null,
      "category": "Cultural",
      "city": "Hyderabad",
      "source": "Telangana Tourism",
      "source_url": "https://www.tourism.telangana.gov.in/events",
      "source_type": "official"
    }
  ],
  "city": "Hyderabad",
  "count": 2,
  "checked_at": "2026-10-02T00:14:56.123456+05:30",
  "source": "Aggregated from public sources: FOSS United, Telangana Tourism, Hyderabad District Government",
  "sources": [
    { "name": "FOSS United", "status": "ok", "message": null },
    { "name": "Telangana Tourism", "status": "ok", "message": null },
    { "name": "Hyderabad District Government", "status": "empty", "message": "No current events listed on district portal" }
  ],
  "cached": true,
  "message": null,
  "all_unavailable": false
}
```

### 6. `GET /api/civic-updates`
Returns verified official civic notices, municipal advisories, district administrative announcements, and government updates relevant to Hyderabad.

> **Important Scope & Non-Affiliation Notice**: TodayNearMe is **NOT** an official government agency, portal, or representative. It is a community utility that aggregates publicly available notices exclusively from selected monitored official public sources. It does not claim to provide a complete or exhaustive list of every civic update in Hyderabad. Always verify important details on the original official source.

**Query Parameters:**
- `city` *(optional, string, default: `Hyderabad`)*. Must strictly be `Hyderabad` in V1 (rejects non-Hyderabad queries with HTTP 400).
- `refresh` *(optional, boolean, default: `false`)*. When `true`, bypasses backend in-memory cache to query upstream official sources immediately (powers the user-controlled "Check Again" button).

**Example Response (Active Civic Notices from Monitored Sources):**
```json
{
  "updates": [
    {
      "id": "ghmc-work-a1b2c3d4e5f6",
      "title": "Providing and Fixing of Chainlink Mesh to Open Spaces in GHMC Ward 98",
      "summary": null,
      "published_at": "2026-09-30T10:00:00+05:30",
      "updated_at": null,
      "category": "Municipal",
      "source": "GHMC",
      "source_url": "https://www.ghmc.gov.in/Tenderspage.aspx",
      "source_type": "official",
      "location": "Hyderabad",
      "department": "Greater Hyderabad Municipal Corporation",
      "scope": "GHMC Area",
      "deadline": "15 Oct 2026, 05:00 PM"
    },
    {
      "id": "hyd-dist-f1e2d3c4b5a6",
      "title": "Final Notice- UnOccupied 2BHK Houses in Hyderabad District",
      "summary": "Verification and cancellation proceedings for allotted 2BHK houses found unoccupied during field inspection.",
      "published_at": "2026-09-22T00:00:00+05:30",
      "updated_at": null,
      "category": "Civic",
      "source": "Hyderabad District Government",
      "source_url": "https://cdn.s3waas.gov.in/s36c524f9d5d7027454a783c841250ba71/uploads/2026/09/17901411858278.pdf",
      "source_type": "official",
      "location": "Hyderabad",
      "department": "Hyderabad District Collectorate",
      "scope": "Hyderabad District",
      "deadline": "30 Sep 2026"
    },
    {
      "id": "ts-gov-7b8c9d0e1f2a",
      "title": "Telangana State Cabinet Approves Public Holiday for All Educational Institutions",
      "summary": "Official notification from the General Administration Department regarding state-wide public holiday observances.",
      "published_at": "2026-09-26T09:56:50+05:30",
      "updated_at": null,
      "category": "Government",
      "source": "Government of Telangana",
      "source_url": "https://www.telangana.gov.in/news/cabinet-notification-2026",
      "source_type": "official",
      "location": "Telangana (Statewide)",
      "department": "Government of Telangana",
      "scope": "Statewide",
      "deadline": null
    }
  ],
  "city": "Hyderabad",
  "count": 3,
  "checked_at": "2026-10-02T03:15:00+05:30",
  "source": "Aggregated from official public sources: GHMC, Hyderabad District Government, Government of Telangana",
  "sources": [
    { "name": "GHMC", "status": "ok", "message": null },
    { "name": "Hyderabad District Government", "status": "ok", "message": null },
    { "name": "Government of Telangana", "status": "ok", "message": null }
  ],
  "cached": true,
  "message": null,
  "all_unavailable": false
}
```

**Example Response (Empty State — Valid when monitored sources have 0 recent Hyderabad notices):**
```json
{
  "updates": [],
  "city": "Hyderabad",
  "count": 0,
  "checked_at": "2026-10-02T03:15:00+05:30",
  "source": "Aggregated from official public sources: GHMC, Hyderabad District Government, Government of Telangana",
  "sources": [
    { "name": "GHMC", "status": "empty", "message": "No current public notices listed on GHMC portal" },
    { "name": "Hyderabad District Government", "status": "empty", "message": "No notices found in announcement listings" },
    { "name": "Government of Telangana", "status": "empty", "message": "No recent Hyderabad-relevant notices in state portal feed" }
  ],
  "cached": false,
  "message": "We couldn't find recent Hyderabad-relevant civic notices in the official public sources currently monitored by TodayNearMe.",
  "all_unavailable": false
}
```

---

## Events Architecture & Multi-Source Public Aggregation

### 1. Data Flow Architecture
```
FOSS United (iCal / RSS Syndication)
Telangana Tourism (Official Portal GET)
Hyderabad District Government (Official Portal GET)
                   ↓
   Event Source Adapters (Concurrent Isolation)
                   ↓
               Normalize (Canonical EventItem Model)
                   ↓
               Validate (Strict Date & Context Verification)
                   ↓
               Deduplicate (Title & Date Canonical Keys)
                   ↓
               Filter Hyderabad (Strict Metropolitan Boundary)
                   ↓
               Sort by Date (Asia/Kolkata Chronological)
                   ↓
               Backend In-Memory Cache (30-min TTL)
                   ↓
               FastAPI GET /api/events
                   ↓
               React Frontend (useEvents Hook → Events Component)
```

### 2. Monitored Public Sources & Contributions

| Source Name | Portal / Feed URL | Contribution & Focus | Source Classification |
| :--- | :--- | :--- | :--- |
| **FOSS United** | `https://fossunited.org/api/method/fossunited.api.chapter.upcoming_events_ics`<br>`https://fossunited.org/c/hyderabad/rss.xml` | Open-source developer meetups, workshops, hackathons, and tech community gatherings. | `community` |
| **Telangana Tourism** | `https://www.tourism.telangana.gov.in/events` | Official state cultural programs, festivals, public gatherings, and tourism events. | `official` |
| **Hyderabad District Government** | `https://hyderabad.telangana.gov.in/events/` | Official district-level public notices, administrative events, and government programs. | `official` |

### 3. Transparent Attribution & Respectful Access Policy
- **Attribution Transparency**: Every listed event identifies its exact source name (`Source: FOSS United`, `Source: Telangana Tourism`, or `Source: Hyderabad District Government`) with a direct external link (`View Event`) to the authoritative publication page. TodayNearMe makes no claim of ownership or organization over listed events.
- **₹0 Budget & Automated-Access Compliance**:
  - **No Paid APIs or Services**: Operates without Google Places, Google Maps, proxies, paid scraping tools, billing accounts, or AI services.
  - **Single Respectful Requests**: Uses isolated, low-frequency HTTP GET requests protected by a backend 30-minute in-memory cache.
  - **No Aggressive Crawling**: No deep recursive crawling, form scraping, or automated logins.
  - **Standard Machine-Readable Feeds**: Prefers standard RFC 5545 iCalendar and RSS 2.0 feeds where available.

### 4. Data Integrity & Filtering Rules
- **No Fabricated Information**: Venues, times, organizers, descriptions, or ticket links are never invented or guessed. Missing fields remain `null`.
- **Strict Hyderabad Metropolitan Filtering**:
  - Every event must demonstrate clear Hyderabad geographic relevance (e.g. Hyderabad, Secunderabad, Cyberabad, HITEC City, Gachibowli, Madhapur, Kondapur, Begumpet, Banjara Hills, Jubilee Hills, etc.).
  - Non-Hyderabad locations (Warangal, Karimnagar, Nizamabad, Bengaluru, Chennai, Delhi, etc.) are strictly excluded.
  - Ambiguous locations that cannot be reliably established as Hyderabad are excluded rather than guessed.
- **General Articles & Retrospectives Excluded**:
  - Informational articles about tourist spots, historical celebrations, or holiday calendars are not treated as upcoming events.
  - Retrospective photo galleries (e.g., `"Glimpses from..."` or past celebrations) are filtered out.
  - Only occurrences with verified upcoming dates are published.

### 5. Deduplication & Completeness Scoring
- When multiple sources report the same event, TodayNearMe deduplicates by normalizing the alphanumeric title and matching the event start date (`YYYY-MM-DD`).
- Rather than discarding records arbitrarily, a **completeness scoring algorithm** retains the version with the richest metadata (e.g., preferring records with descriptions, specific venue addresses, or official source backing).

### 6. Timezone Handling & Chronological Sorting
- All event times and dates are normalized to **Asia/Kolkata** (IST, UTC+05:30).
- UTC timestamps are explicitly shifted to Indian Standard Time before rendering.
- Past events are eliminated (`end_time < now_ist`).
- The resulting event stream is sorted chronologically ascending by start time.

### 7. Caching & "Check Again" Controlled Refresh
- **Cache Duration**: 30 minutes (1,800 seconds) in-memory cache on the FastAPI backend.
- **Controlled Refresh**: The "Check Again" button in the frontend triggers a forced upstream check (`?refresh=true`), re-querying available sources, re-normalizing, re-deduplicating, and updating the UI timestamp without creating uncontrolled request loops.

### 8. Resilient Failure Isolation & Empty States
- **Independent Source Adapters**: A failure or timeout in one source (e.g. Telangana Tourism temporarily unreachable) does not affect or degrade other sources.
- **Valid Empty States**: If an official portal reports zero current events (such as Hyderabad District Government's *"There is no Event."* notice), this is treated as valid data (`status: "empty"`), not an application crash.
- **Transparent Empty State UI**: When zero upcoming events are found across all sources, the app clearly displays:
  > *"We couldn't find upcoming Hyderabad events in the public sources currently monitored by TodayNearMe."*
  along with a status breakdown of each monitored source.
- **Total Failure Fallback**: If all monitored sources fail simultaneously due to external network loss, the system reports an explicit temporary-unavailable state (`all_unavailable: true`) rather than misrepresenting the outage as zero events:
  > *"We couldn't retrieve the monitored public event sources right now. Please try again later."*

---

## Civic Notices & Public Updates Architecture & Multi-Source Official Aggregation

### 1. Data Flow Architecture
```
GHMC (Flash News Ticker & Public Works Table)
Hyderabad District Government (NIC / S3WaaS Announcements)
Government of Telangana (Official State Portal RSS 2.0)
                   ↓
   Civic Source Adapters (Concurrent Non-Blocking Execution)
                   ↓
               Normalize (Canonical CivicUpdateItem Model)
                   ↓
               Validate (Strict Official Field Verification)
                   ↓
               Filter Hyderabad Relevance (Local & Statewide Boundary)
                   ↓
               Deduplicate (Title Keying & Completeness Scoring)
                   ↓
               Recency Filter (Active Window & Deadline Verification)
                   ↓
               Sort by Date (Asia/Kolkata IST Chronological)
                   ↓
               Backend In-Memory Cache (30-min TTL)
                   ↓
               FastAPI GET /api/civic-updates
                   ↓
               React Frontend (useCivicUpdates Hook → CivicUpdates Component)
```

### 2. Monitored Official Public Sources & Contributions

| Source Name | Portal / Feed URL | Contribution & Focus | Retrieval Method | Access & Policy Status |
| :--- | :--- | :--- | :--- | :--- |
| **Greater Hyderabad Municipal Corporation (GHMC)** | `https://www.ghmc.gov.in/`<br>`https://www.ghmc.gov.in/Tenderspage.aspx` | Municipal notices, ward delimitations, property tax advisories, sports/amenity notices, and public civic works. | Respectful HTTP GET; parses official homepage Flash News / breaking news ticker (`.breaking-news-ticker` / `LstFlashNews`) and active public works table. | Public portal; low-frequency read-only requests protected by 30-min backend cache. `robots.txt` returns 404 (standard ASP.NET setup). |
| **Hyderabad District Government** | `https://hyderabad.telangana.gov.in/notice_category/announcements/`<br>`https://hyderabad.telangana.gov.in/notice_category/whats-new/` | Land acquisition proceedings, 2BHK housing scheme notices, collectorate citizen advisories, official notifications. | Respectful HTTP GET; parses standard NIC S3WaaS notice tables (columns: Title, Description, Start Date, End Date, File Link). | Hosted on NIC S3WaaS platform. `robots.txt` returns 204 (permitted, no restrictions on public notice categories). |
| **Government of Telangana** | `https://www.telangana.gov.in/feed/` | State cabinet orders, government notifications, disaster management advisories, and statewide public utility announcements affecting Hyderabad. | Standard RSS 2.0 XML feed (`/feed/`) provided natively by the state portal. | Official public syndication feed. `robots.txt` returns 200 (permitted standard RSS feed). |

### 3. Department Source Investigations & Limitations
During implementation, additional official Telangana/Hyderabad public departments were systematically investigated for automated civic retrieval:
- **HMWSSB (Hyderabad Metro Water Supply & Sewerage Board, `hyderabadwater.gov.in`)**: The public portal's marquee contains static promotional and form links (*"Apply for New Connection Feasibility"*, *"Telangana Rising 2047"*). No machine-readable public feed or clean announcement stream is provided without navigating dynamic ASP.NET session state forms.
- **TGSPDCL (Telangana Southern Power Distribution Company Ltd, `tgspdcl.com`)**: Scheduled power shutdown and outage notifications are localized behind consumer authentication (requiring Service Number / Unique Service Identifier (USC) login) and are not published as a machine-readable, unauthenticated public feed.
- **TSRTC & Hyderabad Metro Rail**: Transit agencies do not publish an open RSS feed or machine-readable API for operational delays or bus diversions. Advisories are distributed ad-hoc across commercial social media (X/Twitter), which requires paid commercial API subscriptions—violating TodayNearMe's strict **₹0 budget** rule.

### 4. Transparent Attribution & Non-Affiliation Notice
- **Clear Attribution Badge**: Every notice displays an **`Official Government Source`** badge, alongside the exact source name (`Source: GHMC`, `Source: Hyderabad District Government`, or `Source: Government of Telangana`).
- **Direct Official Document Links**: A **`View official notice`** button links directly to the original government notice or official PDF on `gov.in` domains.
- **Explicit Non-Affiliation Disclaimer**: The application visibly displays:
  > *"TodayNearMe aggregates publicly available information from official sources. Always verify important details on the original source."*
- **Non-Government Status**: TodayNearMe is an independent community utility, **NOT** an official government agency, department, or representative, and does **NOT** claim to provide a complete or exhaustive catalog of every civic notice.

### 5. ₹0 Budget & Access Compliance
- **No Paid APIs or Services**: Zero budget spent. No paid news APIs, Google billing, proxy services, scraping subscriptions, or commercial feeds.
- **No Anti-Bot Bypassing**: Respects all access controls, rate limits, and server policies. Never bypasses CAPTCHA, authentication, or login walls.
- **Non-Aggressive Retrieval**: Each source is queried at low frequency (maximum once per 30 minutes per server instance) with reasonable timeouts (8 seconds) and descriptive `User-Agent` headers identifying TodayNearMe as a Hyderabad public information utility.

### 6. Data Integrity & Anti-Hallucination Rules
- **Zero Fabrication**: TodayNearMe strictly never fabricates or hallucinates publication dates, deadlines, summaries, departments, or contact numbers.
- **Summary Handling**: Summaries are only displayed when explicitly provided by the official source and genuinely distinct from the title. If the source only provides a title, `summary` remains `null`.
- **Text Cleansing**: CMS character artifacts, non-breaking spaces, zero-width characters, and HTML tags are stripped safely using standard HTML entity decoders.

### 7. Controlled Categorization (Rule-Based, No AI)
To guarantee 100% deterministic operation at ₹0 cost, categorizations are performed rule-based without AI or LLM dependencies:
- **Civic**: Land acquisition, 2BHK housing, citizen rights, voting, elections.
- **Government**: Cabinet decisions, government orders (G.O.), gazettes, recruitment, collectorate orders.
- **Transport**: Road closures, diversions, metro rail, RTC transit, flyover construction.
- **Water**: HMWSSB maintenance, drinking water supply, pipeline repairs, sewerage.
- **Electricity**: TGSPDCL power outages, grid maintenance, load shedding advisories.
- **Public Safety**: Police advisories, disaster alerts, flood warnings, emergency curfews.
- **Municipal**: GHMC property tax, trade licenses, sanitation, ward delimitation, parks, streetlights.
- **Public Services**: MeeSeva, Aadhaar, civil supplies, public health vaccination clinics.
- **Other**: Fallback category for any unclassified or general official notices.

### 8. Hyderabad Relevance Rules
- **Metropolitan Focus**: Prioritizes notices explicitly mentioning Hyderabad, Secunderabad, Cyberabad, GHMC zones, or Hyderabad localities (e.g. Begumpet, Banjara Hills, Jubilee Hills, Charminar, Madhapur, Gachibowli, Kukatpally, Langer House, Bholakpur).
- **Strict Non-Hyderabad District Exclusion**: Notices specifically localized to other Telangana districts (e.g., Warangal, Karimnagar, Nizamabad, Khammam, Nalgonda, Sircilla, Adilabad, Medak) without mentioning Hyderabad are strictly filtered out.
- **Non-English Title Filtering**: State RSS feed entries that are predominantly non-ASCII (e.g. Telugu script without an extractable English title) are excluded from the main feed to ensure legible display across all devices.
- **Telangana-Wide Handling**: Announcements from state-level portals are accepted only if they represent genuine statewide matters directly affecting Hyderabad residents (e.g., public holidays, statewide cabinet orders, disaster management alerts), and are explicitly badged with a **`Telangana-wide`** indicator.

### 9. Recency Rules & Asia/Kolkata Timezone Handling
- **Timezone**: All timestamps and date comparisons are strictly evaluated in **Asia/Kolkata** (IST, UTC+05:30).
- **Recent Display Window**: Notices published within the latest 60 days are prioritized.
- **Ongoing Deadlines**: Older notices (e.g. land acquisition claims or housing verifications) are retained if they specify an active upcoming deadline.
- **Active Homepage Notices**: Active homepage ticker announcements without explicit timestamps are retained as current notices.
- **Sorting**: Notices are sorted descending by:
  1. Most recently published/updated date (`published_at`)
  2. Upcoming deadline date (`deadline`)
  3. Active portal announcements

### 10. Deduplication & Completeness Scoring
When the same government order or notice is published across both district and state portals:
- Alphanumeric title keys are compared (`re.sub(r'[^a-z0-9]', '', title.lower())`).
- A **completeness scoring algorithm** preserves the richest record:
  - Prefers direct PDF/document download links over generic portal URLs (+2)
  - Prefers local district-level scope over state-level scope (+2)
  - Prefers notices with an active deadline (+2)
  - Prefers notices with an official summary (+3)

### 11. Backend Caching & Controlled "Check Again" Refresh
- **Cache TTL**: 30 minutes (1,800 seconds) in-memory cache on the FastAPI backend.
- **Controlled Refresh**: Clicking the "Check Again" button in the frontend sends `?refresh=true`, which bypasses the cache, queries all monitored sources concurrently, runs deduplication and filtering, updates the UI, and resets the "Checked at" timestamp without creating runaway loops.

### 12. Failure Handling & Source Breakdown
- **Independent Failure Isolation**: Each source adapter executes independently within `asyncio.gather(..., return_exceptions=True)`. A failure or network timeout on one portal never crashes or blocks the others.
- **Status Breakdown**: Every response returns the operational state of each monitored source:
  - `ok`: Source queried successfully with updates found.
  - `empty`: Source queried successfully, but 0 relevant Hyderabad notices currently listed.
  - `unavailable`: Source temporarily unreachable (network timeout or server error).
  - `not_supported`: Automated retrieval is not currently available.
- **Empty State**: When 0 notices are found across all sources, TodayNearMe renders:
  > *"No recent public updates found"* — *"We couldn't find recent Hyderabad-relevant civic notices in the official public sources currently monitored by TodayNearMe."*
  along with the status of each checked source.
- **Total Outage State**: If all monitored sources fail simultaneously, the UI displays:
  > *"Public updates temporarily unavailable"* — *"We couldn't retrieve the monitored official sources right now. Please try again later."*

---

## Testing & Verification

1. **Frontend Code Quality & Production Build**:
   ```bash
   npm run lint
   npm run build
   ```

2. **Backend Civic Notices & Public Updates Test Suite**:
   ```bash
   backend\venv\Scripts\python backend\test_api_civic.py
   ```

3. **Backend Events Integration & Unit Test Suite**:
   ```bash
   backend\venv\Scripts\python backend\test_api_events.py
   ```

4. **Backend Places Integration Test Suite**:
   ```bash
   backend\venv\Scripts\python backend\test_api_places.py
   ```

