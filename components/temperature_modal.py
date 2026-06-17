# components/temperature_modal.py
"""
Temperature Modal Component

Displays a modal with temperature and humidity tiles for all rooms.
Uses MQTT snapshot data to show real-time sensor readings.
"""

from dash import html
from datetime import datetime, timezone
import time

_STALE_SECONDS = 3600  # 1 hour -> tidsstämpeln blir röd om mätningen är äldre


# Room configuration
ROOMS = [
    {"key": "shelly_bht", "name": "Stue", "icon": "🛋️"},
    {"key": "env_office", "name": "Kontor", "icon": "💼"},
    {"key": "env_laundry", "name": "Vaskerum", "icon": "🧺"},
    {"key": "env_bedroom", "name": "Soveværelse", "icon": "🛏️"},
]


def create_temperature_tile(room_name: str, icon: str, temperature: float | None,
                            humidity: float | None, ts: int | None = None,
                            local_tz=None) -> html.Div:
    """
    Create a single temperature tile.

    Args:
        room_name: Display name of the room
        icon: Emoji icon for the room
        temperature: Temperature in Celsius (None if no data)
        humidity: Relative humidity percentage (None if no data)
        ts: Epoch seconds when the reading was received (None if no data)
        local_tz: Timezone for formatting the timestamp

    Returns:
        html.Div: Temperature tile component
    """
    # Format display values
    temp_txt = f"{temperature:.1f}°C" if isinstance(temperature, (int, float)) else "–°C"
    humidity_txt = f"{humidity:.0f}%" if isinstance(humidity, (int, float)) else "–%"

    # Determine tile class based on data availability
    has_data = isinstance(temperature, (int, float))
    tile_class = "temp-tile" if has_data else "temp-tile no-data"

    children = [
        html.Div(icon, className="room-icon"),
        html.Div(room_name, className="room-name"),
        html.Div(temp_txt, className="room-temp"),
        html.Div(humidity_txt, className="room-humidity"),
    ]

    # Diskret tidsstämpel (när mätningen är ifrån), som på övriga tiles
    if ts:
        when = datetime.fromtimestamp(ts, tz=timezone.utc)
        if local_tz is not None:
            when = when.astimezone(local_tz)
        stale = (time.time() - ts) > _STALE_SECONDS
        ts_class = "timestamp wx-ts-stale" if stale else "timestamp"
        children.append(html.Div(when.strftime("%Y-%m-%d, %H:%M"), className=ts_class))

    return html.Div(className=tile_class, children=children)


# --- Heat pump (luftvärmepump) control ----------------------------------
# Daikin climate entity, styrs direkt via climate-tjänsterna.
HEATPUMP_ENTITY = "climate.daikinap61890"
HEATPUMP_HEAT_TEMP = 21
HEATPUMP_COOL_TEMP = 19


def _heatpump_controls() -> html.Div:
    """Tre knappar till vänster om temperaturrutorna för att styra värmepumpen."""
    return html.Div(
        className="heatpump-controls",
        children=[
            html.Button(
                [html.Div("🔥", className="hp-icon"),
                 html.Div("Värme", className="hp-label"),
                 html.Div(f"{HEATPUMP_HEAT_TEMP}°", className="hp-sub")],
                id="heatpump-heat", n_clicks=0, className="heatpump-btn heat",
            ),
            html.Button(
                [html.Div("❄️", className="hp-icon"),
                 html.Div("Kyla", className="hp-label"),
                 html.Div(f"{HEATPUMP_COOL_TEMP}°", className="hp-sub")],
                id="heatpump-cool", n_clicks=0, className="heatpump-btn cool",
            ),
            html.Button(
                [html.Div("⏻", className="hp-icon"),
                 html.Div("Av", className="hp-label")],
                id="heatpump-off", n_clicks=0, className="heatpump-btn off",
            ),
            html.Div(id="heatpump-status-msg", className="heatpump-status-msg"),
        ],
    )


def create_modal_layout() -> html.Div:
    """
    Create the static modal layout structure.

    This should be called once during app initialization to create
    the modal container. The content is updated via callbacks.

    Returns:
        html.Div: Complete modal structure
    """
    return html.Div(
        id="temp-modal",
        className="modal",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-content temp-modal-content",
                children=[
                    html.Div(
                        className="modal-header",
                        children=[
                            html.Button("×", id="close-temp-modal", className="modal-close-button"),
                        ],
                    ),
                    html.Div(
                        className="temp-modal-body",
                        children=[
                            _heatpump_controls(),
                            html.Div(id="temp-tiles-container", className="temp-tiles-container"),
                        ],
                    ),
                ],
            ),
        ],
    )


def render_temperature_tiles(snapshot: dict | None, local_tz=None) -> list[html.Div]:
    """
    Render all temperature tiles from snapshot data.

    Args:
        snapshot: MQTT snapshot containing room sensor data
        local_tz: Timezone for formatting the per-tile timestamp

    Returns:
        list[html.Div]: List of temperature tile components
    """
    tiles = []

    for room in ROOMS:
        room_data = (snapshot or {}).get(room["key"], {})
        temperature = room_data.get("t")
        humidity = room_data.get("rh")

        tile = create_temperature_tile(
            room_name=room["name"],
            icon=room["icon"],
            temperature=temperature,
            humidity=humidity,
            ts=room_data.get("ts"),
            local_tz=local_tz,
        )
        tiles.append(tile)

    return tiles
