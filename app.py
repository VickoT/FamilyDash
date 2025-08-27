from dash import Dash, html, dcc
from dash.dependencies import Input, Output

from components.calendar_box import calendar_box
from components.tibber_plot import make_tibber_figure
from components.weather_box import weather_box
from components.washer_box import washer_box, washer_render

from fetch import fetch_tibber, fetch_calendar, fetch_weather, fetch_washer

# ---- NEW: importera MQTT helper ----
from mqtt_subscriber import start as mqtt_start, get_latest
from datetime import datetime

try:
    fetch_tibber.main(); fetch_calendar.main(); fetch_weather.main(); fetch_washer.main()
except Exception as e:
    print(f"Initial fetch failed: {e}")

app = Dash(__name__)
mqtt_start()   # <-- starta subscribern i bakgrunden

app.layout = html.Div(
    className="app-wrapper",
    children=[
        # Kalender
        html.Div(id="calendar-box", className="calendar box", children=calendar_box()),

        # Väder
        html.Div(id="weather-box", className="weather box", children="Weather placeholder"),

        # Widgets
        html.Div(
            id="widgets-box",
            className="widgets box",
            children=[
                washer_box(),
                html.Div(id="shelly-box", className="tile"),  # <-- NY TILE
                html.Div(id="aqi-box", className="tile"),
                html.Div(id="sonos-box", className="tile"),
                html.Div(id="sensor3-box", className="tile"),
                html.Div(id="sensor4-box", className="tile"),
                html.Div(id="sensor5-box", className="tile"),
                html.Div(id="sensor6-box", className="tile"),
                html.Div(id="sensor7-box", className="tile"),
            ],
        ),

        # Tibber
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

        dcc.Interval(id="interval-component", interval=2*60*1000, n_intervals=0),
        dcc.Interval(id="shelly-interval", interval=2000, n_intervals=0),  # <-- pollar cache
    ],
)

# ---------- Callbacks ----------
@app.callback(Output("calendar-box", "children"), Input("interval-component", "n_intervals"))
def cb_calendar(_): return calendar_box()

@app.callback(Output("weather-box", "children"), Input("interval-component", "n_intervals"))
def cb_weather(_): return weather_box()

@app.callback([Output("washer-box", "children"), Output("washer-box", "className")],
              Input("interval-component", "n_intervals"))
def cb_washer(_): return washer_render()

@app.callback(Output("tibber-graph", "figure"), Input("interval-component", "n_intervals"))
def cb_tibber(_): return make_tibber_figure()

# ---- NEW: Shelly callback ----
@app.callback(Output("shelly-box", "children"), Input("shelly-interval", "n_intervals"))
def cb_shelly(_):
    data = get_latest()
    if not data or not data.get("ts"):
        return "Shelly H&T: väntar på data…"
    t = data.get("tC"); h = data.get("rh"); ts = data.get("ts")
    ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    return html.Div([
        html.Div(f"Temp: {t:.1f} °C" if isinstance(t,(int,float)) else "Temp: –"),
        html.Div(f"Fukt: {h:.1f} %" if isinstance(h,(int,float)) else "Fukt: –"),
        html.Div(f"Tid: {ts_str}"),
    ])

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
