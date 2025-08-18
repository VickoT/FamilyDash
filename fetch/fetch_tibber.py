#!/usr/bin/env python3
import os, sys, requests, pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PRICES_FILE = DATA_DIR / "tibber_prices.csv"
LOG_FILE = DATA_DIR / "fetch_tibber.log"

load_dotenv()
TIBBER_TOKEN = os.getenv("TIBBER_TOKEN")

QUERY = """
{
  viewer {
    homes {
      currentSubscription {
        priceInfo {
          current { startsAt energy }
          today   { startsAt energy }
          tomorrow{ startsAt energy }
        }
      }
    }
  }
}
"""

def _to_df(prices, label):
    if not prices:
        return pd.DataFrame(columns=["startsAt", "energy_ore", "day"])
    df = pd.DataFrame(prices)
    df["startsAt"] = pd.to_datetime(df["startsAt"])
    df["energy_ore"] = df["energy"] * 100
    df["day"] = label
    return df[["startsAt", "energy_ore", "day"]]

def fetch_prices():
    if not TIBBER_TOKEN:
        raise RuntimeError("TIBBER_TOKEN saknas i miljön (.env).")
    headers = {"Authorization": f"Bearer {TIBBER_TOKEN}"}
    r = requests.post(
        "https://api.tibber.com/v1-beta/gql",
        json={"query": QUERY},
        headers=headers,
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    homes = data["data"]["viewer"]["homes"]
    price_info = homes[0]["currentSubscription"]["priceInfo"]
    today = price_info.get("today", [])
    tomorrow = price_info.get("tomorrow", [])
    return (
        pd.concat([_to_df(today, "today"), _to_df(tomorrow, "tomorrow")], ignore_index=True)
        if tomorrow else
        _to_df(today, "today")
    )

def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df_all = fetch_prices()
        df_all.to_csv(PRICES_FILE, index=False)
        ts = datetime.now().isoformat(timespec="seconds")
        msg = f"[{ts}] Saved {len(df_all)} rows to {PRICES_FILE}"
        print(msg)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(msg + "\n")
        except Exception:
            pass
        return 0
    except Exception as e:
        ts = datetime.now().isoformat(timespec="seconds")
        err = f"[{ts}] Tibber fetch FAILED: {e}"
        print(err)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(err + "\n")
        except Exception:
            pass
        return 1

if __name__ == "__main__":
    sys.exit(main())
