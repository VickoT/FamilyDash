from dash import Dash, html, dcc
import pandas as pd
import requests
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

# === Setup ===
load_dotenv()
TIBBER_TOKEN = os.getenv("TIBBER_TOKEN")
DATAFILE = "tibber_prices.csv"

# === Tibber query ===
query = """
{
  viewer {
    homes {
      currentSubscription {
        priceInfo {
          current { startsAt energy }
          today { startsAt energy }
          tomorrow { startsAt energy }
        }
      }
    }
  }
}
"""
headers = {"Authorization": f"Bearer " + TIBBER_TOKEN}
response = requests.post("https://api.tibber.com/v1-beta/gql", json={"query": query}, headers=headers)
response.raise_for_status()
data = response.json()

homes = data["data"]["viewer"]["homes"]
price_info = homes[0]["currentSubscription"]["priceInfo"]
price_current = price_info.get("current")
prices_today = price_info.get("today", [])
prices_tomorrow = price_info.get("tomorrow", [])

def to_dataframe(prices, label):
    df = pd.DataFrame(prices)
    df["startsAt"] = pd.to_datetime(df["startsAt"])
    df["energy_öre"] = df["energy"] * 100
    df["day"] = label
    return df

if prices_tomorrow:
    dfs = [to_dataframe(prices_today, "Today"), to_dataframe(prices_tomorrow, "Tomorrow")]
    df_all = pd.concat(dfs).sort_values("startsAt")
    df_all.to_csv(DATAFILE, index=False)
else:
    if os.path.exists(DATAFILE):
        df_all = pd.read_csv(DATAFILE, parse_dates=["startsAt"])
    else:
        raise SystemExit("No Tibber data available")

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

if price_current and price_current.get("energy") is not None:
    current_time = pd.to_datetime(price_current["startsAt"])
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
        text="Now",
        showarrow=False,
        font=dict(color="red", size=12)
    )

fig.update_layout(
    template="plotly_dark",
    title="Electricity Price (öre/kWh)",
    height=500,
    width=1280,
    margin=dict(t=60, b=40, l=60, r=40),
    showlegend=False
)
fig.update_xaxes(tickformat="%H", showgrid=False)
fig.update_yaxes(title="öre/kWh", gridcolor="rgba(255,255,255,0.05)")

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
        html.H1("Annes Family Planner", style={"textAlign": "center",
                                               "color": "white"}),

        html.Div([
            dcc.Graph(
                figure=fig,
                style={"height": "360px", "width": "100%"},
                config={"displayModeBar": False}
            )
        ],
        style={
            "display": "flex",
            "justifyContent": "flex-end",
            "alignItems": "flex-end",
            "height": "500px",
            "border": "1px dashed gray"
        })
    ]
)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
