from dash import Dash, html, dcc
from dash.dependencies import Input, Output
# Import the app components
from components.tibber_plot import make_tibber_figure
from components.washer_box import washer_box
from components.calendar_box import calendar_box
from components.weather_box import weather_box

# Initialize the Dash app
app = Dash(__name__)

app.layout = html.Div(
    className="app-wrapper",
    children=[
        calendar_box(),  # ska ge <div id="calendar" class="calendar">...</div>
        html.Div(
            className="right-panel",
            children=[
                html.Div("Weather placeholder", id="weather-box", className="box"),
                html.Div("Washer placeholder", id="washer-box", className="box"),
                dcc.Graph(
                    id="tibber-graph",
                    figure=make_tibber_figure(),
                    className="tibber-graph",
                    style={"height": "100%"},
                    config={"displayModeBar": False},
                ),
            ],
        ),
        dcc.Interval(id="interval-component", interval=2*60*1000, n_intervals=0),
    ]
)


@app.callback(
    Output("washer-box", "children"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False,
)
def _update_washer(_n):
    return washer_box()

@app.callback(
    Output("tibber-graph", "figure"),
    Output("calendar", "children"),
    Input("interval-component", "n_intervals"),
)
def update_everything(_):
    # kalendern returnerar en wrapper <div id="calendar"> med children=boxes
    from components.calendar_box import _load_calendar  # lokal import för att läsa om filen
    data = _load_calendar()
    days = data.get("days", [])[:7]

    # bygg bara children (boxes) igen:
    from components.calendar_box import calendar_box as _calendar_box
    fresh = _calendar_box()  # ny wrapper
    return make_tibber_figure(), fresh.children


@app.callback(
    Output("weather-box", "children"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False,
)
def _update_weather(_n):
    return weather_box()

if __name__ == "__main__":
    try:
        from fetch import fetch_calendar, fetch_tibber, fetch_washer, fetch_weather
        fetch_calendar.main()
        fetch_tibber.main()
        fetch_washer.main()
        fetch_weather.main()
    except Exception as e:
        print(f"Initial fetch failed: {e} (starting server anyway)")
    app.run(debug=False, host="0.0.0.0", port=8050)
