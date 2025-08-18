#!/usr/bin/env python3
import os, requests
from dotenv import load_dotenv
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


load_dotenv()

SHELLY_IP = os.getenv("SHELLY_IP", "192.168.50.54")
SWITCH_ID = os.getenv("SHELLY_SWITCH_ID", "0")
TIMEOUT_S = float(os.getenv("SHELLY_TIMEOUT_S", "2.5"))
OUTFILE = os.getenv("WASHER_FILE", "data/washer_w.csv")

def fetch_power():
    url = f"http://{SHELLY_IP}/rpc/Switch.GetStatus?id={SWITCH_ID}"
    r = requests.get(url, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()["apower"]

def main():
    w = fetch_power()
    TZ = ZoneInfo(os.getenv("TZ", "Europe/Stockholm"))
    ts = datetime.now(TZ).isoformat(timespec="seconds")
    line = f"{ts},{w}\n"
    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
    with open(OUTFILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())

if __name__ == "__main__":
    main()

