from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from components.tibber_plot import make_tibber_figure
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
#        html.H1("The Anne Family Planner", className="title"),
        html.Div(
            className="tibber",
            children=dcc.Graph(
                id="tibber-graph",
                figure=make_tibber_figure(),
                className="tibber-graph",
                config={"displayModeBar": False},
            ),
        ),
        dcc.Interval(id="interval-component", interval=2*60*1000, n_intervals=0),
    ]
)

@app.callback(
    Output("tibber-graph", "figure"),
    Output("calendar", "children"),
    Input("interval-component", "n_intervals"),
)
def update_everything(_):
    return make_tibber_figure(), calendar_boxes()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
