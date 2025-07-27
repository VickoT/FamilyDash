from dash import Dash, html, dcc
import pandas as pd
import os
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

DATAFILE = "data/tibber_prices.csv"
df_all = pd.read_csv(DATAFILE)

# === Gradient coloring ===
def get_gradient_color(value, vmin=0, vmax=150, cmap="turbo"):
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    colormap = cm.get_cmap(cmap)  # or: matplotlib.colormaps[cmap]
    rgba = colormap(norm(value))
    return mcolors.to_hex(rgba)

df_all["color"] = df_all["energy_öre"].apply(lambda x: get_gradient_color(x))

# === Plotly figure ===
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_all["startsAt"],
    y=df_all["energy_öre"],
    mode="lines",
    line=dict(width=0, color="rgba(1, 209, 178, 0.2)"),
    fill="tozeroy"
))
fig.add_trace(go.Scatter(
    x=df_all["startsAt"],
    y=df_all["energy_öre"],
    mode="lines+markers",
    line=dict(width=2, color="rgba(255,255,255,0.3)"),
    marker=dict(color=df_all["color"], size=8),
    hovertemplate="%{x|%H:%M}, %{y:.0f} öre<extra></extra>"
))

#current_time = pd.to_datetime(price_current["startsAt"])
current_time = pd.Timestamp.now(tz="Europe/Stockholm").floor("h")
fig.add_shape(
    type="line",
    x0=current_time,
    x1=current_time,
    y0=0,
    y1=1,
    xref="x",
    yref="paper",
    line=dict(color="red", width=2, dash="dot")
)
fig.add_annotation(
    x=current_time,
    y=1.05,
    xref='x',
    yref='paper',
    text="Nu",
    showarrow=False,
    font=dict(color="red", size=12)
)

fig.update_layout(
    template="plotly_dark",
    title="Elpris (øre/kWh)",
    height=500,
    width=1280,
    margin=dict(t=60, b=40, l=60, r=40),
    showlegend=False
)
fig.update_xaxes(tickformat="%H", showgrid=False)
fig.update_yaxes(title="øre/kWh", gridcolor="rgba(255,255,255,0.05)")

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
