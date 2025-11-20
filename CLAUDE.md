# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FamilyDash is a Python Dash-based family dashboard application that displays real-time home automation data, energy prices, calendar events, and appliance statuses. The app runs on a Raspberry Pi in kiosk mode and integrates with Home Assistant via MQTT.

## Architecture

### Data Flow Pattern

The application uses a **dual-update strategy** with two distinct data pipelines:

1. **MQTT Real-time Updates** (5-second intervals)
   - MQTT subscriber (`mqtt_subscriber.py`) maintains a background thread that listens to MQTT topics
   - Incoming messages are parsed and stored in a thread-safe in-memory snapshot (`_snapshot` dict with `_lock`)
   - Dash callbacks poll this snapshot every 5 seconds via `get_snapshot()` (copy.deepcopy for safety)
   - Used for: appliance statuses (washer/dryer), sensors (temperature, humidity, VOC), car data, power usage, calendar, weather

2. **Scheduled API Fetches** (via cron in scheduler container)
   - Separate fetch scripts pull data from external APIs and write to `data/` directory
   - Dash callbacks read these files on 2-minute intervals
   - Used for: Tibber energy prices (fetched 12:30-13:59 daily, every 15 min)

### Key Components

**`app.py`** - Main Dash application
- Sets up layout with calendar, widgets, and Tibber graph
- Defines two intervals: 2-minute for API-based updates, 5-second for MQTT updates
- Each widget has its own callback with de-duplication logic using `dcc.Store` for timestamps
- Returns `no_update` when data hasn't changed to minimize re-renders

**`mqtt_subscriber.py`** - MQTT client manager
- Starts background thread via `mqtt_start()` (idempotent, called once from app.py)
- Implements Last Will and Testament (LWT) for presence detection
- Publishes "online/offline" to `clients/{MQTT_CLIENT}/status`
- Topic parsers extract data from JSON or plain text payloads and update `_snapshot`
- Thread-safe access to snapshot via `get_snapshot()`

**`components/*_box.py`** - Widget rendering modules
- Each component follows pattern: `<name>_compute(snapshot, tz, last_ts)` returns `(children, className, updated_last_ts)`
- Returns `no_update` when timestamp hasn't changed (de-duplication)
- SVG graphics use CSS classes for styling, animations driven by class changes (e.g., `active` class)
- Components are stateless; all state lives in MQTT snapshot or Store components

**`fetch/fetch_*.py`** - API data fetchers
- Standalone scripts that fetch from external APIs and write to `data/` directory
- Run on cron schedules defined in `crontab` file (executed by scheduler container)
- Log to `data/logs/fetch_*.log`

## Development Commands

### Local Development (Mac)
```bash
# Start with local code mounted (uses docker-compose.override.yml)
docker compose up --build -d

# View logs
make logs
# or
docker compose logs -f --tail=200

# Clean Python cache
make clean_cache
```

### Production Deployment (Raspberry Pi)
```bash
# Build and push images to GHCR
make push-dash          # Build & push dashboard image
make push-scheduler     # Build & push scheduler image
make push-all          # Push both

# Deploy to Pi (pulls images, no local code)
make deploy-pi         # Pull latest images & start containers
make restart-pi        # Restart without pulling

# Start kiosk mode on Pi
make kiosk            # Launch Chromium in kiosk mode via tmux

# Complete deployment
make do_all           # push-dash + deploy-pi + kiosk
```

### Docker Compose Files
- `docker-compose.yml` - Production (uses GHCR images, minimal volumes)
- `docker-compose.override.yml` - Local dev (builds from Dockerfile, mounts code, uses Mac-specific MQTT credentials)

## Environment Variables

Required in `.env` file (not in git):
- `TIBBER_TOKEN` - Tibber API token
- `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASS` - MQTT broker credentials
- `MQTT_CLIENT` - Unique client ID (e.g., `familydash-default`)
- `LOCAL_TZ` - Timezone for date/time display (default: `Europe/Stockholm`)

## MQTT Topics

Calendar events:
- `home/calendar/familie/next7d` - Family calendar (7-day JSON events array)
- `home/calendar/fodelsedagar/next370d` - Birthdays (370-day JSON events array)

Appliances & sensors:
- `home/appliance/washer/state` - Washer status (JSON: `{status, time_to_end_min}`)
- `home/appliance/dryer/state` - Dryer status (JSON: `{status, time_left}`)
- `home/tibber/power` - Current power usage (JSON: `{power}`)
- `home/car/state` - Kia EV data (JSON: `{battery, range}`)
- `home/env/livingroom/ht/state` - Climate sensor (JSON: `{t, rh}`)
- `home/env/livingroom/airquality_raw` - Air quality from Pico (JSON: `{eco2_ppm, tvoc_ppb, aqi, ...}`)
- `shelly-htg3/#` - Shelly H&T Gen3 sensor (various subtopics)
- `home/weather` - Weather data from HA (JSON with condition, temperature, wind, etc.)
- `home/system/heartbeat` - Heartbeat signal

## Code Patterns

### Adding a New MQTT Widget

1. Add topic constant in `mqtt_subscriber.py` (e.g., `TOPIC_NEWWIDGET = "home/new/topic"`)
2. Create parser function `_parse_newwidget(payload: str)` that updates `_snapshot["newwidget"]`
3. Add snapshot structure to `_snapshot` dict initialization
4. Subscribe in `_on_connect()`: `cli.subscribe(TOPIC_NEWWIDGET, qos=0)`
5. Route in `_on_message()`: `if msg.topic == TOPIC_NEWWIDGET: _parse_newwidget(payload); return`
6. Create `components/newwidget_box.py` with `newwidget_compute(snapshot, tz, last_ts)` function
7. Add widget div to `app.layout` in `app.py`
8. Add `dcc.Store(id="last-ts-newwidget", data={})` to layout
9. Create callback in `app.py` with de-duplication pattern

### Component Compute Function Pattern

```python
def widget_compute(snapshot: dict | None, tz, last_ts: dict | None):
    last_ts = (last_ts or {}).copy()
    w = (snapshot or {}).get("widget") or {}
    ts = w.get("ts")

    # 1. No data yet
    if not ts:
        return _placeholder_children(), "box widget-card", last_ts

    # 2. De-duplicate (same timestamp)
    if last_ts.get("widget") == ts:
        return no_update, no_update, last_ts

    # 3. New data - render
    children, klass = _render(w, tz)
    last_ts["widget"] = ts
    return children, klass, last_ts
```

### Adding a New API Fetch Script

1. Create `fetch/fetch_newapi.py` following the pattern in `fetch_tibber.py`
2. Fetch data, process, and save to `data/newapi_data.csv` (or similar)
3. Add cron schedule to `crontab` file
4. Create component that reads from the data file
5. Add callback in `app.py` triggered by `interval-component` (2-minute interval)

## Deployment Architecture

- **Production**: Two containers on Raspberry Pi (dash + scheduler) pulling images from GHCR
- **Local Dev**: Same two containers but building from local Dockerfile with code mounted
- **Kiosk Mode**: Chromium browser in kiosk mode pointing to `localhost:8050`, managed via tmux session
- **Data Persistence**: `./data` directory mounted in both containers for shared state

## Calendar Event Formatting

Special handling for:
- **Birthdays**: Format `Name, YYYY` is parsed to show "Name – XX år!" in pink
- **Trash collection**: Events containing "tömning tunna" are highlighted in green
- **Sundays**: Day labels for Sundays have special styling
- Events are sorted by time (all-day events first, then by start time)

## Testing

No formal test suite currently. Manual testing involves:
1. Verifying MQTT messages are received (check `[mqtt]` debug logs in dash container)
2. Confirming widget updates occur within 5 seconds of MQTT message
3. Checking fetch scripts run successfully via cron logs in `data/logs/`
4. Visual inspection of dashboard in kiosk mode
