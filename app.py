from dash import Dash, html, dcc, no_update
from dash.dependencies import Input, Output, State

from components.calendar_box import calendar_box
from components.tibber_plot import make_tibber_figure
from components.weather_box import weather_box
from components.washer_box import  washer_compute
from components.dryer_box import dryer_compute
from components.kia_box import kia_compute
from components.power_box import power_compute
from components.climate_quality_box import climate_quality_compute
from components.temperature_modal import create_modal_layout, render_temperature_tiles
from components.anne_button import anne_button_render

from ha_client import call_service

# --- MQTT helper ---
from mqtt_subscriber import start as mqtt_start, get_snapshot
from datetime import datetime, timezone
from typing import Any, cast
from zoneinfo import ZoneInfo
import os, time

LOCAL_TZ = ZoneInfo(os.getenv("LOCAL_TZ", "Europe/Stockholm"))
ANNE_SCRIPT_ENTITY = os.getenv("HA_SCRIPT_ANNE")
STATUS_TTL_SECONDS = 5

app = Dash(__name__)

# Starta MQTT-subscribe i bakgrunden (threads), och skapar snapshots med
# senaste värdena från MQTT, en fryst bild av senaste mqtt-läget.
mqtt_start()

app.layout = html.Div(
    className="app-wrapper",
    children=[
        html.Div(id="calendar-box", className="calendar box", children=calendar_box()),

        html.Div(
            id="widgets-box",
            className="widgets box",
            children=[
                html.Div(id="weather-box", className="tile span-2r"),
                html.Div(id="washer-box",   className="box washer-card"),
                # Climate widget with modal button
                html.Div(
                    className="climate-wrapper tile span-2r",
                    children=[
                        html.Div(id="climate-quality-box", className="climate-content"),
                        html.Button("+", id="open-temp-modal", className="modal-trigger-btn", n_clicks=0),
                    ]
                ),
                html.Div(id="anne-button-box", className="anne-button-tile", children=anne_button_render(False)),
                html.Div(id="kia-box",      className="box kia-card"),
                html.Div(id="dryer-box",    className="dryer-card"),
                html.Div(id="power-box",    className="box power-card"),
                html.Div(id="heartbeat-box", className="tile"),
            ],
        ),

        html.Div(
            id="tibber-box",
            className="tibber box",
            children=dcc.Graph(
                id="tibber-graph",
                figure=make_tibber_figure(),
                className="tibber-graph",
                style={"height": "100%"},
                config={"displayModeBar": False},
            ),
        ),

        # Temperature modal
        create_modal_layout(),

        # Två olika intervaller för callback-anrop:
        # 2 minuter för fetch av tibber, kalender, väder
        # 5 sekunder för uppdatering av widgets
        dcc.Interval(id="interval-component", interval=2*60*1000, n_intervals=0),
        dcc.Interval(id="tick", interval=5000, n_intervals=0),
        # Store för att hålla reda på senaste timestamps för olika widgets,
        dcc.Store(id="last-ts-weather", data={}),
        dcc.Store(id="anne-button-pressed-at", data=None),
        dcc.Store(id="anne-button-status", data=None),
        dcc.Store(id="last-ts-washer", data={}),
        dcc.Store(id="last-ts-dryer",  data={}),
        dcc.Store(id="last-ts-kia", data={}),
        dcc.Store(id="last-ts-climate-quality", data={}),
        dcc.Store(id="last-ts-power", data={}),
        dcc.Store(id="modal-open", data=False),
    ],
)

# ---- CALLBACKS ----------------------------------------------------------

#Callback syntax:
#    Output - vad som uppdateras. Kan vara flera outputs i en lista.
#    Input  - vad som triggar uppdateringen. Kan vara flera inputs i en lista.
#    State - vad som är "read-only" data som skickas in i callbacken.

# ---- Calendar -----------------------------------------------------------
@app.callback(
        [Output("calendar-box", "children")],
        Input("interval-component", "n_intervals"))
def cb_calendar(_):
    return (calendar_box(),)

# ---- Weather --------------------------------------------------------------
@app.callback(
        [Output("weather-box", "children")],
        Input("interval-component", "n_intervals"))
def cb_weather(_):
    return (weather_box(),)

# ---- Washer --------------------------------------------------------------
@app.callback(
    [Output("washer-box", "children"),
     Output("washer-box", "className"),
     Output("last-ts-washer", "data")],
    Input("tick", "n_intervals"),
    State("last-ts-washer", "data"),
)
def cb_washer(_n, last_ts):
    return washer_compute(get_snapshot(), LOCAL_TZ, last_ts)

# ---- Tibber graph --------------------------------------------------------
@app.callback(Output("tibber-graph", "figure"), Input("interval-component", "n_intervals"))
def cb_tibber(_):
    return make_tibber_figure()

# ---- Anne Button ---------------------------------------------------------
@app.callback(
    [Output("anne-button-box", "children"),
     Output("anne-button-pressed-at", "data"),
     Output("anne-button-status", "data")],
    [Input("anne-button", "n_clicks"),
     Input("tick", "n_intervals")],
    [State("anne-button-pressed-at", "data"),
     State("anne-button-status", "data")],
    prevent_initial_call=False,
)
def refresh_anne_button(n_clicks, _tick, pressed_at, status_state):
    from dash import ctx

    now = time.time()
    status = status_state if isinstance(status_state, dict) else None

    if status and now - float(status.get("ts", 0)) > STATUS_TTL_SECONDS:
        status = None

    if ctx.triggered_id == "anne-button" and n_clicks:
        if not ANNE_SCRIPT_ENTITY:
            message = "HA_SCRIPT_ANNE saknas"
            status = {"text": message, "ts": now}
            app.logger.warning("Anne-knappen saknar konfiguration: %s", message)
            return anne_button_render(is_active=False, status_text=message), None, status

        success, error_text = call_service("script", "turn_on", {"entity_id": ANNE_SCRIPT_ENTITY})
        if success:
            return anne_button_render(is_active=True), now, None

        message = error_text or "Fel vid anrop"
        app.logger.warning("Anne-knappen misslyckades: %s", message)
        status = {"text": message, "ts": now}
        return anne_button_render(is_active=False, status_text=message), None, status

    if pressed_at and (now - float(pressed_at)) < 3:
        return anne_button_render(is_active=True), pressed_at, status

    if status and status.get("text"):
        return anne_button_render(is_active=False, status_text=status["text"]), None, status

    return anne_button_render(is_active=False), None, None

# ---- Dryer ---------------------------------------------------------------
@app.callback(
    [Output("dryer-box", "children"),
     Output("dryer-box", "className"),
     Output("last-ts-dryer", "data")],
    Input("tick", "n_intervals"),
    State("last-ts-dryer", "data"),
)
def cb_dryer(_n, last_ts):
    return dryer_compute(get_snapshot(), LOCAL_TZ, last_ts)

# ---- Heartbeat ----------------------------------------------------------
@app.callback(
    Output("heartbeat-box", "children"),
    Input("tick", "n_intervals"),
)
def refresh_heartbeat(_n):
    snap = get_snapshot()
    hb = snap.get("heartbeat", {})
    ts = hb.get("ts")

    if not ts:
        return html.Div([html.Div("Heartbeat"), html.Div("Väntar …")])

    age = time.time() - ts
    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(LOCAL_TZ).strftime("%H:%M:%S")
    status = "OK" if age <= 30 else f"Ingen puls på {int(age)}s"

    return html.Div([
        html.Div("Heartbeat"),
        html.Div(f"Senast: {ts_str}"),
        html.Div(f"Status: {status}"),
    ])

# ---- KIA ---------------------------------------------------------------
@app.callback(
    [Output("kia-box", "children"),
     Output("kia-box", "className"),
     Output("last-ts-kia", "data")],
    Input("tick", "n_intervals"),
    State("last-ts-kia", "data"),
)
def cb_kia(_n, last_ts):
    return kia_compute(get_snapshot(), LOCAL_TZ, last_ts)

# ---- Climate + Air Quality (combined) -------------------------------------
@app.callback(
    [Output("climate-quality-box", "children"),
     Output("last-ts-climate-quality", "data")],
    Input("tick", "n_intervals"),
    State("last-ts-climate-quality", "data"),
)
def cb_climate_quality(_n, last_ts):
    children, className, updated_ts = climate_quality_compute(get_snapshot(), LOCAL_TZ, last_ts)
    # Wrap children i en div när nytt innehåll kommer
    if children == no_update or className == no_update:
        return children, updated_ts
    wrapped = html.Div(cast(Any, children), className=cast(str, className))
    return wrapped, updated_ts

# ---- Tibber Power -------------------------------------------------------
@app.callback(
    [Output("power-box", "children"),
     Output("power-box", "className"),
     Output("last-ts-power", "data")],
    Input("tick", "n_intervals"),
    State("last-ts-power", "data"),
)
def cb_power(_n, last_ts):
    return power_compute(get_snapshot(), LOCAL_TZ, last_ts)

# ---- Temperature Modal --------------------------------------------------
@app.callback(
    [Output("modal-open", "data"),
     Output("temp-modal", "style")],
    [Input("open-temp-modal", "n_clicks"),
     Input("close-temp-modal", "n_clicks")],
    State("modal-open", "data"),
)
def toggle_temperature_modal(open_clicks, close_clicks, is_open):
    """Toggle temperature modal visibility"""
    from dash import callback_context

    if not callback_context.triggered:
        return is_open, {"display": "flex" if is_open else "none"}

    button_id = callback_context.triggered[0]["prop_id"].split(".")[0]

    if button_id == "open-temp-modal":
        return True, {"display": "flex"}
    elif button_id == "close-temp-modal":
        return False, {"display": "none"}

    return is_open, {"display": "flex" if is_open else "none"}

@app.callback(
    Output("temp-tiles-container", "children"),
    Input("tick", "n_intervals"),
)
def update_temperature_tiles(_n):
    """Update temperature tiles with latest sensor data"""
    return render_temperature_tiles(get_snapshot())

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
