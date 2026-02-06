# AGENTS.md

This file provides guidance for agentic coding agents working on FamilyDash.

## Build/Lint/Test Commands

### Docker Commands
```bash
# Build and run locally (development mode)
docker compose up --build -d

# View logs
docker compose logs -f --tail=200
make logs

# Clean Python cache
make clean_cache
find . -name "__pycache__" -type d -exec rm -r {} +
```

### Python Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application locally
python app.py

# Check Python syntax (basic)
python -m py_compile app.py
python -m py_compile mqtt_subscriber.py
python -m py_compile components/*.py
```

### Testing
No formal test suite exists. Manual testing is performed by:
1. Running the app and checking widgets update within 5 seconds of MQTT messages
2. Verifying fetch scripts run via cron logs in `data/logs/`
3. Visual inspection in browser/kiosk mode

To run a specific component check:
```bash
python -c "from components.washer_box import washer_compute; print('OK')"
```

## Code Style Guidelines

### File Organization
- `app.py` - Main Dash application with layout and callbacks
- `mqtt_subscriber.py` - MQTT client and topic parsers
- `components/*_box.py` - Widget rendering modules (stateless compute functions)
- `components/*_modal.py` - Modal/popup components
- `fetch/fetch_*.py` - API data fetchers (scheduled via cron)
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies

### Import Style
```python
# Standard library imports first
from __future__ import annotations
import copy
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Third-party imports
import paho.mqtt.client as mqtt
from dash import Dash, html, dcc, no_update
from dash.dependencies import Input, Output, State

# Local imports
from components.calendar_box import calendar_box
from mqtt_subscriber import start as mqtt_start
```

### Type Annotations
- Use `from __future__ import annotations` for forward references
- Basic type hints: `dict | None`, `str`, `int`, `bool`
- Use `Optional[str]` for nullable strings
- Functions should have type hints for parameters and returns

### Component Pattern
All widget components follow this compute pattern:

```python
def widget_compute(snapshot: dict | None, tz, last_ts: dict | None):
    """
    Return (children|no_update, className|no_update, updated_last_ts)
    """
    last_ts = (last_ts or {}).copy()
    w = (snapshot or {}).get("widget") or {}
    ts = w.get("ts")

    # 1) No data yet → placeholder
    if not ts:
        return _placeholder_children(), "box widget-card", last_ts

    # 2) De-duplicate (same timestamp)
    if last_ts.get("widget") == ts:
        return no_update, no_update, last_ts

    # 3) New data → render
    children, klass = _render(w, tz)
    last_ts["widget"] = ts
    return children, klass, last_ts
```

### Naming Conventions
- **Files**: `snake_case.py` (e.g., `washer_box.py`)
- **Functions**: `snake_case()` (e.g., `washer_compute()`)
- **Variables**: `snake_case` (e.g., `last_ts`, `snapshot`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `TOPIC_WASHER`)
- **Classes**: `PascalCase` (rare in this codebase)
- **CSS Classes**: `kebab-case` (e.g., `washer-card`, `appliance-svg`)

### Error Handling
- Use try/except for data parsing and formatting functions
- Return fallback values (e.g., "–", 0, empty dict) on errors
- Don't let exceptions propagate to UI layer
- Log errors to console for debugging

### MQTT Integration
- Topic constants at top of `mqtt_subscriber.py`: `TOPIC_WASHER = "home/appliance/washer/state"`
- Parser functions: `_parse_washer(payload: str)` updating `_snapshot["washer"]`
- Thread-safe access via `get_snapshot()` (returns copy.deepcopy)
- All MQTT data includes timestamp `ts` for de-duplication

### Dash Callback Pattern
```python
@app.callback(
    [Output("washer-box", "children"), Output("washer-box", "className"), Output("last-ts-washer", "data")],
    [Input("interval-component", "n_intervals")],
    [State("last-ts-washer", "data")]
)
def update_washer(n, last_ts):
    snapshot = get_snapshot()
    return washer_compute(snapshot, LOCAL_TZ, last_ts)
```

### CSS and Styling
- Use semantic class names: `box`, `tile`, `appliance-card`, `active`
- Component-specific modifiers: `washer-card`, `dryer-card`
- SVG icons use CSS classes for styling: `appliance-svg`, `washer-svg`
- Grid layout via `span-2r`, `span-3r` classes
- Animations driven by class changes (e.g., `active` class)

### Environment Variables
Required in `.env` (not in git):
- `TIBBER_TOKEN` - API token
- `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASS` - MQTT credentials
- `MQTT_CLIENT` - Unique client ID
- `LOCAL_TZ` - Timezone (default: Europe/Stockholm)

### Code Comments
- Use Swedish for user-facing strings and comments
- Keep comments concise and relevant
- Don't comment obvious code
- Use block comments for complex logic sections

### SVG Graphics
- Use raw SVG strings with `class` attributes for CSS targeting
- Include `aria-hidden="true"` for decorative icons
- Structure: frame, panel, door groups for consistent styling
- Scale to 64x64 viewBox for consistency

### When Adding New Features
1. MQTT widgets: Add topic → parser → compute function → layout → callback
2. API widgets: Create fetch script → cron schedule → file reader component
3. Follow existing patterns for consistency
4. Test with MQTT messages or file updates
5. Verify de-duplication works (no unnecessary re-renders)