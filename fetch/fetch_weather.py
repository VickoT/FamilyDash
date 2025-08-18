#!/usr/bin/env python3
import json, os, requests
from datetime import datetime, date
from zoneinfo import ZoneInfo

# Koordinater (Bunkeflostrand ungefär). Sätt via env om du vill.
LAT = float(os.getenv("WX_LAT", "55.55"))
LON = float(os.getenv("WX_LON", "12.92"))
TZ  = os.getenv("WX_TZ", "Europe/Stockholm")

BASE = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": LAT,
    "longitude": LON,
    "timezone": TZ,
    "current": "temperature_2m,weather_code",
    "daily": ",".join([
        "weather_code",
        "temperature_2m_max",
        "uv_index_max",
        "precipitation_sum",
        "precipitation_probability_max"
    ])
}

def wmo_icon(code: int) -> str:
    # Superenkel mapping (räcker för dashboarden)
    if code in (0,): return "☀️"
    if code in (1,2): return "🌤️"
    if code in (3,): return "☁️"
    if code in (45,48): return "🌫️"
    if code in (51,53,55,56,57): return "🌦️"     # dugg
    if code in (61,63,65,80,81,82): return "🌧️"   # regn
    if code in (66,67): return "🌨️"               # iskorn/underkylt
    if code in (71,73,75,77,85,86): return "❄️"   # snö
    if code in (95,96,99): return "⛈️"            # åska
    return "🌡️"

def simplify(payload: dict) -> dict:
    tz = ZoneInfo(TZ)
    today_idx = 0  # API: day 0 = idag
    d = payload["daily"]
    return {
        "generated_at": datetime.now(tz).isoformat(timespec="seconds"),
        "current": {
            "temperature": payload["current"]["temperature_2m"],
            "weather_code": payload["current"]["weather_code"],
            "icon": wmo_icon(payload["current"]["weather_code"]),
        },
        "today": {
            "date": d["time"][today_idx],
            "weather_code": d["weather_code"][today_idx],
            "icon": wmo_icon(d["weather_code"][today_idx]),
            "t_max": d["temperature_2m_max"][today_idx],
            "uv_max": d.get("uv_index_max", [None])[today_idx],
            "precip_sum_mm": d.get("precipitation_sum", [0])[today_idx],
            "precip_prob_max": d.get("precipitation_probability_max", [None])[today_idx],
        }
    }

def main():
    r = requests.get(BASE, params=params, timeout=15)
    r.raise_for_status()
    data = simplify(r.json())
    os.makedirs("data", exist_ok=True)
    with open("data/weather.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
