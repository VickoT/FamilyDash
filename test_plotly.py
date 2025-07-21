import requests
import pandas as pd
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import matplotlib.pyplot as mpl
import matplotlib.colors as mcolors

# === Config ===
load_dotenv()
TIBBER_TOKEN = os.getenv("TIBBER_TOKEN")
DATAFILE = "tibber_prices.csv"

# === Tibber GraphQL query ===
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

headers = {"Authorization": f"Bearer {TIBBER_TOKEN}"}
response = requests.post("https://api.tibber.com/v1-beta/gql", json={"query": query}, headers=headers)
response.raise_for_status()
data = response.json()

homes = data["data"]["viewer"]["homes"]
if not homes:
    print("No homes found in Tibber account.")
    exit(1)

price_info = homes[0]["currentSubscription"]["priceInfo"]
price_current = price_info.get("current")
prices_today = price_info.get("today", [])
prices_tomorrow = price_info.get("tomorrow", [])

# === Convert Tibber response to DataFrame ===
def to_dataframe(prices, label):
    df = pd.DataFrame(prices)
    df["startsAt"] = pd.to_datetime(df["startsAt"])
    df["energy_öre"] = df["energy"] * 100  # Convert to öre
    df["day"] = label
    return df

if prices_tomorrow:
    # Use fresh data and save it
    dfs = [
        to_dataframe(prices_today, "Today"),
        to_dataframe(prices_tomorrow, "Tomorrow")
    ]
    df_all = pd.concat(dfs).sort_values("startsAt")
    df_all.to_csv(DATAFILE, index=False)
    print("Fetched and saved new data.")
else:
    # Fallback to saved data if available
    if os.path.exists(DATAFILE):
        df_all = pd.read_csv(DATAFILE, parse_dates=["startsAt"])
        print("Tomorrow's data not available. Using previously saved data.")
    else:
        print("No data available. Exiting.")
        exit(1)

# === Generate gradient colors based on price ===
def get_gradient_color(value, vmin=0, vmax=150, cmap="turbo"):
    norm = mpl.Normalize(vmin=vmin, vmax=vmax)
    rgba = mpl.cm.get_cmap(cmap)(norm(value))
    return mcolors.to_hex(rgba)

df_all["color"] = df_all["energy_öre"].apply(lambda x: get_gradient_color(x))

# === Plotly Figure ===
fig = go.Figure()

# (1) Filled area below the line
fig.add_trace(go.Scatter(
    x=df_all["startsAt"],
    y=df_all["energy_öre"],
    mode="lines",
    line=dict(width=0, color="rgba(1, 209, 178, 0.2)"),
    fill="tozeroy",
    name="Area"
))

# (2) Line with gradient-colored markers
fig.add_trace(go.Scatter(
    x=df_all["startsAt"],
    y=df_all["energy_öre"],
    mode="lines+markers",
    line=dict(width=2, color="rgba(255,255,255,0.3)"),
    marker=dict(color=df_all["color"], size=8),
    hovertemplate="%{x|%H:%M}, %{y:.0f} öre<extra></extra>",
    name="Price Gradient"
))

# (3) Red vertical line for current hour
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

# === Layout ===
fig.update_layout(
    template="plotly_dark",
    title="Electricity Price (öre/kWh) – Gradient Style",
    xaxis_title=None,
    yaxis_title="öre/kWh",
    showlegend=False,
    height=500,
    margin=dict(t=60, b=40, l=60, r=40)
)
fig.update_xaxes(tickformat="%H:%M", showgrid=False)
fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

fig.show()
