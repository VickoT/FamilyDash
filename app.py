from dash import Dash, html, dcc
from dash.dependencies import Input, Output

from components.calendar_box import calendar_box
from components.tibber_plot import make_tibber_figure
from components.weather_box import weather_box
from components.washer_box import washer_box  # behövs i callback

from fetch import fetch_tibber, fetch_calendar, fetch_weather, fetch_washer
try:
    fetch_tibber.main(); fetch_calendar.main(); fetch_weather.main(); fetch_washer.main()
except Exception as e:
    print(f"Initial fetch failed: {e}")

app = Dash(__name__)

app.layout = html.Div(
    className="app-wrapper",
    children=[
        # Kalender
        html.Div(
            id="calendar-box",
            className="calendar box",
            children=calendar_box(),  # <- returns a list of day Divs
        ),

        # Väder
        html.Div(
            id="weather-box",
            className="weather box",
            children="Weather placeholder",
        ),

        # Widgets: 8 tiles, inkl. washer-box
        html.Div(
            id="widgets-box",
            className="widgets box",
            children=[
                html.Div("Washer",       id="washer-box", className="tile"),
                html.Div(id="aqi-box",    className="tile"),
                html.Div(id="sonos-box",  className="tile"),
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
    ],
)

# ---------- Callbacks ----------
@app.callback(
    Output("calendar-box", "children"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False,
)
def cb_calendar(_):
    # calendar_box() returns a list -> return it directly
    return calendar_box()

@app.callback(
    Output("weather-box", "children"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False,
)
def cb_weather(_):
    # weather_box() should return either a Div or children list -> return directly
    return weather_box()

@app.callback(
    Output("washer-box", "children"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False,
)
def cb_washer(_):
    # washer_box() should return the inner content for the tile
    return washer_box()

@app.callback(
    Output("tibber-graph", "figure"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False,
)
def cb_tibber(_):
    return make_tibber_figure()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
