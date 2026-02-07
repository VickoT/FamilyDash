# FamilyDash

A Python Dash-based family dashboard displaying real-time home automation data, energy prices, calendar events, and appliance statuses. Runs on Raspberry Pi in kiosk mode and integrates with Home Assistant via MQTT.

## Architecture

### Data Flow

```
Home Assistant (Central Hub)
    ↓ (publishes to MQTT)
MQTT Broker (Mosquitto)
    ↓ (subscribes)
FamilyDash MQTT Client
    ↓ (updates in-memory snapshot every 5s)
Dash Callbacks
    ↓ (renders)
Dashboard UI
```

**Home Assistant** acts as the central data hub, collecting data from:
- Tibber (energy prices)
- Weather services
- Shelly H&T sensors (temperature, humidity)
- VOC/Air quality sensors
- Appliances (washer, dryer via integrations)
- Kia EV (car battery, range)
- Calendar integrations
- System heartbeat

**MQTT Broker** receives all data from Home Assistant and distributes it to subscribers.

**FamilyDash** subscribes to MQTT topics, maintains a thread-safe in-memory snapshot of the latest data, and updates the dashboard in real-time.

### Key Components

- **Single Docker container** - Simplified from previous dual-container setup
- **MQTT subscriber** (`mqtt_subscriber.py`) - Background thread maintaining data snapshot
- **Dash application** (`app.py`) - Web UI with callbacks polling snapshot every 5 seconds
- **Widget components** (`components/*.py`) - Modular widgets for different data types
- **CSS grid layout** (`assets/style.css`) - Responsive dashboard layout

## Widgets

- **Calendar** - Family events and birthdays (7/370 day views)
- **Weather** - Current conditions, forecast, UV, precipitation
- **Stue (Living Room)** - Temperature, humidity, TVOC air quality with AQI indicator
- **Appliances** - Washer and dryer status with time remaining
- **Kia EV** - Battery level and range
- **Power Usage** - Real-time electricity consumption
- **Tibber Prices** - Hourly electricity price forecast graph
- **Heartbeat** - System status monitoring
- **Anne Button** - Triggers a Home Assistant script via REST

## Hardware

- **Raspberry Pi 5** (4GB)
- **Raspberry Pi Touch Display 2** - 7" touchscreen in kiosk mode

## Development

### Local Development (Mac)

```bash
# Start with local code mounted (uses docker-compose.override.yml)
docker compose up --build -d

# View logs
docker compose logs -f --tail=200

# Clean Python cache
make clean_cache
```

The local override mounts your code directory and uses Mac-specific MQTT credentials.

### Production Deployment (Raspberry Pi)

```bash
# Build and push image to GHCR
make push-dash

# Deploy to Pi (pulls image, starts container)
make deploy-pi

# Start kiosk mode on Pi
make kiosk

# Complete deployment (build + deploy + kiosk)
make do_all
```

Production uses pre-built images from GitHub Container Registry with no local code mounts.

## Configuration

Create a `.env` file with:

```bash
TIBBER_TOKEN=your_tibber_token
MQTT_HOST=192.168.x.x
MQTT_PORT=1883
MQTT_USER=your_mqtt_user
MQTT_PASS=your_mqtt_password
MQTT_CLIENT=familydash-default
LOCAL_TZ=Europe/Stockholm
HA_BASE_URL=https://homeassistant.local:8123
HA_TOKEN=your_long_lived_token
HA_SCRIPT_ANNE=script.anne_notify
# Optional override (seconds)
HA_TIMEOUT=5
```

`HA_TOKEN` should be a Home Assistant long-lived access token. The dashboard uses `HA_BASE_URL`, `HA_SCRIPT_ANNE`, and the token to call `POST /api/services/script/turn_on` whenever the Anne button is pressed. If you skip these variables the button stays inactive and shows a configuration warning.

## MQTT Topics

All topics are published by Home Assistant automations/integrations:

- `home/calendar/familie/next7d` - Family calendar events
- `home/calendar/fodelsedagar/next370d` - Birthday reminders
- `home/weather` - Weather forecast data
- `home/tibber/forecast/json` - Hourly electricity prices
- `home/tibber/power` - Current power consumption
- `home/appliance/washer/state` - Washer status
- `home/appliance/dryer/state` - Dryer status
- `home/car/state` - Kia EV data
- `home/env/livingroom/ht/state` - Climate sensor
- `home/env/livingroom/airquality_raw` - VOC/AQI sensor
- `home/system/heartbeat` - System health check

## Kiosk Mode

The dashboard runs in Chromium kiosk mode on the Raspberry Pi:

```bash
ssh dashpi
tmux new -d -s kiosk 'chromium-browser --kiosk http://localhost:8050'
```

Or use `make kiosk` to deploy remotely.

## Development Notes

- See `CLAUDE.md` for detailed architecture documentation and code patterns
- Widget components follow a compute pattern: `widget_compute(snapshot, tz, last_ts)`
- De-duplication via timestamp checking prevents unnecessary re-renders
- All state lives in MQTT snapshot or Dash Store components (stateless widgets)

## License

Private project
