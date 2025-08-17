from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from components.tibber_plot import make_tibber_figure
from components.washer_box import washer_box

import json, os

CAL_PATH = "data/calendar.json"

def load_calendar(path=CAL_PATH):
    if not os.path.exists(path):
        return {"generated_at": None, "days": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def calendar_boxes():
    data = load_calendar()
    days = data.get("days", [])[:7]
    boxes = []

    for i, day in enumerate(days):
        label = day.get("label", "")
        events = day.get("events", [])

        items = []
        if events:
            events = sorted(events, key=lambda e: (e.get("time") is not None, e.get("time") or ""))
            for e in events:
                t = e.get("time")
                title = e.get("title", "")
                items.append(html.Li(f"{t} - {title}" if t else title))

        boxes.append(
            html.Div(
                className=f"day{' today' if i == 0 else ''}",
                children=[
                    html.Div(label, className="day-title"),
                    html.Ul(items, className="day-content"),
                ],
            )
        )
    return boxes

app = Dash(__name__)

app.layout = html.Div(
    className="app-wrapper",
    children=[
        html.Div(id="calendar", className="calendar", children=calendar_boxes()),

        # wrapper för högerkolumnen
        html.Div(
            className="tibber",
            children=[
                html.Div(id="washer-box", className="box"),  # boxen ovanför
                dcc.Graph(
                    id="tibber-graph",
                    figure=make_tibber_figure(),
                    className="tibber-graph",
                    config={"displayModeBar": False},
                ),
            ],
        ),

        dcc.Interval(id="interval-component", interval=2*60*1000, n_intervals=0),
    ]
)


# Uppdatera washer-box varje gång intervallet tickar
@app.callback(
    Output("washer-box", "children"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False,
)
def _update_washer(_n):
    # returnerar html-innehållet (titel + värde) från CSV:n
    return washer_box()

@app.callback(
    Output("tibber-graph", "figure"),
    Output("calendar", "children"),
    Input("interval-component", "n_intervals"),
)
def update_everything(_):
    return make_tibber_figure(), calendar_boxes()

if __name__ == "__main__":
    try:
        from fetch import fetch_calendar, fetch_tibber
        fetch_calendar.main()
        fetch_tibber.main()
    except Exception as e:
        print(f"Initial fetch failed: {e} (starting server anyway)")
    app.run(debug=False, host="0.0.0.0", port=8050)
