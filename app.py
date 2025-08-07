from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from components.tibber_plot import make_tibber_figure
import pandas as pd

app = Dash(__name__)

app.layout = html.Div(
    style={"backgroundColor": "#000000", "height": "720px", "width": "1280px", "padding": "10px"},
    children=[
        html.H1("The Anne Family Planner", style={"textAlign": "center", "color": "white"}),

        dcc.Graph(
            id="tibber-graph",
            figure=make_tibber_figure(),
            style={"height": "360px", "width": "100%"},
            config={"displayModeBar": False}
        ),

        dcc.Interval(
            id="interval-component",
            interval=60 * 60 * 1000,  # update every hour
            n_intervals=0
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

#from dash import Dash, html, dcc
#from components.tibber_plot import make_tibber_figure
#
#fig = make_tibber_figure()
#
## === Dash layout ===
#app = Dash(__name__)
#app.layout = html.Div(
#    style={
#        "backgroundColor": "#000000",
#        "height": "720px",
#        "width": "1280px",
#        "padding": "10px"
#    },
#    children=[
#        html.H1("The Anne Family Planner", style={"textAlign": "center",
#                                               "color": "white"}),
#
#        html.Div([
#            dcc.Graph(
#                figure=fig,
#                style={"height": "360px", "width": "100%"},
#                config={"displayModeBar": False}
#            )
#        ])
#    ]
#)
#
#if __name__ == "__main__":
#    app.run(debug=False, host="0.0.0.0", port=8050)
