from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from components.tibber_plot import make_tibber_figure
import pandas as pd
from datetime import datetime, timedelta
import math

app = Dash(__name__)

app.layout = html.Div(
    className="app-wrapper",
    children=[
        html.H1("The Anne Family Planner", className="title"),

        dcc.Graph(
            id="tibber-graph",
            figure=make_tibber_figure(),
            style={"height": "360px", "width": "100%"},
            config={"displayModeBar": False}
        ),

        dcc.Interval(
            id="interval-component",
            interval=2 * 60 * 1000,  # update every hour
            n_intervals=0,
            max_intervals=-1,
            disabled=False,
        )
    ]
)


@app.callback(
    Output("tibber-graph", "figure"),
    Input("interval-component", "n_intervals")
)
def update_graph(n):
    return make_tibber_figure()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
