from dash import Dash, html, dcc, no_update
from dash.dependencies import Input, Output, State

from components.calendar_box import calendar_box
from components.tibber_plot import make_tibber_figure
from components.weather_box import weather_box
from components.washer_box import box as washer_box, compute as washer_compute
from components.dryer_box import compute as dryer_compute
from components.kia_box import kia_compute


from fetch import fetch_tibber, fetch_calendar, fetch_weather, fetch_washer

# --- MQTT helper ---
from mqtt_subscriber import start as mqtt_start, get_snapshot
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os, time

LOCAL_TZ = ZoneInfo(os.getenv("LOCAL_TZ", "Europe/Stockholm"))

# Initiala fetch (best effort)
try:
    fetch_tibber.main(); fetch_calendar.main(); fetch_weather.main(); fetch_washer.main()
except Exception as e:
    print(f"Initial fetch failed: {e}")

app = Dash(__name__)
mqtt_start()   # starta MQTT-subscribe i bakgrunden

app.layout = html.Div(
    className="app-wrapper",
    children=[
        html.Div(id="calendar-box", className="calendar box", children=calendar_box()),
        html.Div(id="weather-box",  className="weather box",  children="Weather placeholder"),

        html.Div(
            id="widgets-box",
            className="widgets box",
            children=[
                washer_box(),                         # befintlig tvättmaskinskomponent
                html.Div(id="dryer-box", className="box dryer-card"),
                html.Div(id="shelly-box",    className="tile"),
                html.Div(id="heartbeat-box", className="tile"),
                html.Div(id="sensor3-box",   className="tile"),
                html.Div(id="washertime-box",className="tile"),
                html.Div(id="sensor5-box",   className="tile"),
                html.Div(id="kia-box", className="box kia-card"),
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

        # Intervaller & state
        dcc.Interval(id="interval-component", interval=2*60*1000, n_intervals=0),
        dcc.Interval(id="tick", interval=5000, n_intervals=0),
        dcc.Store(id="last-ts-shelly", data={}),
        dcc.Store(id="last-ts-washer", data={}),
        dcc.Store(id="last-ts-dryer",  data={}),   # <-- NY
        dcc.Store(id="last-ts-kia", data={}),
    ],
)

# ---------- Callbacks ----------
@app.callback(Output("calendar-box", "children"), Input("interval-component", "n_intervals"))
def cb_calendar(_):
    return calendar_box()

@app.callback(Output("weather-box", "children"), Input("interval-component", "n_intervals"))
def cb_weather(_):
    return weather_box()

@app.callback(
    [Output("washer-box", "children"),
     Output("washer-box", "className"),
     Output("last-ts-washer", "data")],
    Input("tick", "n_intervals"),
    State("last-ts-washer", "data"),
)
def cb_washer(_n, last_ts):
    return washer_compute(get_snapshot(), LOCAL_TZ, last_ts)

@app.callback(Output("tibber-graph", "figure"), Input("interval-component", "n_intervals"))
def cb_tibber(_):
    return make_tibber_figure()

# ---- Shelly (Sovrum) ----------------------------------------------------
@app.callback(
    [Output("shelly-box", "children"),
     Output("last-ts-shelly", "data")],
    Input("tick", "n_intervals"),
    State("last-ts-shelly", "data"),
)
def refresh_shelly(_n, last_ts):
    snap = get_snapshot()
    last_ts = last_ts or {}
    s = snap.get("shelly") or {}
    ts = s.get("ts")

    if not ts:
        return html.Div([html.Div("Shelly temp."), html.Div("Väntar på sensor …")]), last_ts

    if last_ts.get("shelly") == ts:
        return no_update, last_ts

    t = s.get("tC"); h = s.get("rh")
    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(LOCAL_TZ).strftime("%H:%M:%S")
    view = html.Div([
        html.Div("Shelly temp."),
        html.Div(f"Temp: {t:.1f} °C" if isinstance(t, (int, float)) else "Temp: –"),
        html.Div(f"Fukt: {h:.1f} %" if isinstance(h, (int, float)) else "Fukt: –"),
        html.Div(f"Tid: {ts_str}"),
    ])
    last_ts["shelly"] = ts
    return view, last_ts

# ---- Torktumlare: ny tile -----------------------------------------------
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

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
