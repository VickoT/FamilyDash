import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API token from .env file
load_dotenv()
TIBBER_TOKEN = os.getenv("TIBBER_TOKEN")

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
response = requests.post("https://api.tibber.com/v1-beta/gql",
                         json={"query": query},
                         headers=headers)
response.raise_for_status()
data = response.json()

homes = data["data"]["viewer"]["homes"]
price_info = homes[0]["currentSubscription"]["priceInfo"]
#price_current = price_info.get("current")
prices_day1 = price_info.get("today", [])
prices_day2 = price_info.get("tomorrow", [])

def to_dataframe(prices, label):
    df = pd.DataFrame(prices)
    df["startsAt"] = pd.to_datetime(df["startsAt"])
    df["energy_öre"] = df["energy"] * 100
    df["day"] = label
    return df

if prices_day2:
    dfs = [to_dataframe(prices_day1, "today"), to_dataframe(prices_day2,
                                                            "tomorrow")]
    df_all = pd.concat(dfs).sort_values("startsAt")
    df_all.to_csv("data/tibber_prices.csv", index=False)
    print(df_all)

else:
    raise SystemExit("No 'Day2' data available")
