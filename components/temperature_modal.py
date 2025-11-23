# components/temperature_modal.py
"""
Temperature Modal Component

Displays a modal with temperature and humidity tiles for all rooms.
Uses MQTT snapshot data to show real-time sensor readings.
"""

from dash import html


# Room configuration
ROOMS = [
    {"key": "shelly_bht", "name": "Stue", "icon": "🛋️"},
    {"key": "env_office", "name": "Kontor", "icon": "💼"},
    {"key": "env_laundry", "name": "Vaskerum", "icon": "🧺"},
    {"key": "env_bedroom", "name": "Soveværelse", "icon": "🛏️"},
]


def create_temperature_tile(room_name: str, icon: str, temperature: float | None, humidity: float | None) -> html.Div:
    """
    Create a single temperature tile.

    Args:
        room_name: Display name of the room
        icon: Emoji icon for the room
        temperature: Temperature in Celsius (None if no data)
        humidity: Relative humidity percentage (None if no data)

    Returns:
        html.Div: Temperature tile component
    """
    # Format display values
    temp_txt = f"{temperature:.1f}°C" if isinstance(temperature, (int, float)) else "–°C"
    humidity_txt = f"{humidity:.0f}%" if isinstance(humidity, (int, float)) else "–%"

    # Determine tile class based on data availability
    has_data = isinstance(temperature, (int, float))
    tile_class = "temp-tile" if has_data else "temp-tile no-data"

    return html.Div(
        className=tile_class,
        children=[
            html.Div(icon, className="room-icon"),
            html.Div(room_name, className="room-name"),
            html.Div(temp_txt, className="room-temp"),
            html.Div(humidity_txt, className="room-humidity"),
        ]
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
                className="modal-content",
                children=[
                    html.Div(
                        className="modal-header",
                        children=[
                            html.Button("×", id="close-temp-modal", className="modal-close-button"),
                        ],
                    ),
                    html.Div(id="temp-tiles-container", className="temp-tiles-container"),
                ],
            ),
        ],
    )


def render_temperature_tiles(snapshot: dict | None) -> list[html.Div]:
    """
    Render all temperature tiles from snapshot data.

    Args:
        snapshot: MQTT snapshot containing room sensor data

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
            humidity=humidity
        )
        tiles.append(tile)

    return tiles
