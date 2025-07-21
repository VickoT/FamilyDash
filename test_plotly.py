import requests
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

# Load .env file to get Tibber token
load_dotenv()
TIBBER_TOKEN = os.getenv("TIBBER_TOKEN")

# GraphQL query for Tibber prices
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

# Get price data
homes = data["data"]["viewer"]["homes"]
if not homes:
    print("No homes linked to your Tibber account.")
    exit(1)

price_info = homes[0]["currentSubscription"]["priceInfo"]
price_current = price_info.get("current")
prices_today = price_info.get("today", [])
prices_tomorrow = price_info.get("tomorrow", [])

def to_dataframe(prices, label):
    df = pd.DataFrame(prices)
    df["startsAt"] = pd.to_datetime(df["startsAt"])
    df["day"] = label
    df["color"] = df["energy"].apply(lambda x: "gold" if x > 0.5 else "#3d9be9")
    return df

# Combine data
dfs = []
if prices_today:
    dfs.append(to_dataframe(prices_today, "Today"))
if prices_tomorrow:
    dfs.append(to_dataframe(prices_tomorrow, "Tomorrow"))
if not dfs:
    print("No price data available.")
    exit(1)
df_all = pd.concat(dfs).sort_values("startsAt")

# Create figure
fig = go.Figure()

for day in df_all["day"].unique():
    df_day = df_all[df_all["day"] == day]
    fig.add_trace(go.Bar(
        x=df_day["startsAt"],
        y=df_day["energy"],
        name=day,
        marker_color=df_day["color"],
        hovertemplate="Time: %{x|%H:%M}<br>Price: %{y:.4f} kr/kWh<extra></extra>"
    ))

# Add vertical line using add_shape (instead of add_vline)
if price_current and price_current.get("energy") is not None:
    current_time = pd.to_datetime(price_current["startsAt"])
    fig.add_shape(
        type="line",
        x0=current_time, x1=current_time,
        y0=0, y1=1,
        xref='x',
        yref='paper',
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

# Layout settings
fig.update_layout(
    title="Electricity Price Forecast (Tibber Style)",
    xaxis_title="Time",
    yaxis_title="Price (kr/kWh)",
    barmode="group",
    template="plotly_white",
    legend_title=None,
    bargap=0.15,
    height=500
)
fig.update_xaxes(tickformat="%H:%M")

# Show the plot
fig.show()
