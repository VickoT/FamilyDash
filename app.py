from dash import Dash, html, dcc
from components.tibber_plot import make_tibber_figure

fig = make_tibber_figure()

# === Dash layout ===
app = Dash(__name__)
app.layout = html.Div(
    style={
        "backgroundColor": "#000000",
        "height": "720px",
        "width": "1280px",
        "padding": "10px"
    },
    children=[
        html.H1("The Anne Family Planner", style={"textAlign": "center",
                                               "color": "white"}),

        html.Div([
            dcc.Graph(
                figure=fig,
                style={"height": "360px", "width": "100%"},
                config={"displayModeBar": False}
            )
        ])
    ]
)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
