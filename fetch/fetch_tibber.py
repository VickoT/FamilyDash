import os
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

# === Setup paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PRICES_FILE = DATA_DIR / "tibber_prices.csv"
LOG_FILE = DATA_DIR / "fetch_tibber.log"

# === Load Tibber token ===
load_dotenv()
TIBBER_TOKEN = os.getenv("TIBBER_TOKEN")

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

# === Extract and format data ===
homes = data["data"]["viewer"]["homes"]
price_info = homes[0]["currentSubscription"]["priceInfo"]

def to_dataframe(prices, label):
    df = pd.DataFrame(prices)
    df["startsAt"] = pd.to_datetime(df["startsAt"])
    df["energy_øre"] = df["energy"] * 100
    df["day"] = label
    return df[["startsAt", "energy_øre", "day"]]

prices_today = price_info.get("today", [])
prices_tomorrow = price_info.get("tomorrow", [])

df_all = pd.concat([
    to_dataframe(prices_today, "today"),
    to_dataframe(prices_tomorrow, "tomorrow")
], ignore_index=True)


print(df_all)
# === Save to file ===
df_all.to_csv(PRICES_FILE, index=False)
