#!/usr/bin/env python3
import os
import pickle
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Ladda miljövariabler
load_dotenv()
token_path = os.getenv("GOOGLE_TOKEN_PATH", ".config/token.pickle")

# Svensk tidszon
SWEDEN_TZ = ZoneInfo("Europe/Stockholm")

# Dansk veckodag/månad
DK_WD = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]
DK_MON = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

def dk_label(dt):
    return f"{DK_WD[dt.weekday()]} {dt.day:02d}/{DK_MON[dt.month-1]}"

def main():
    # Läs Google Calendar credentials
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)
    calendar_id = 'family12428309117852465721@group.calendar.google.com'

    # Hämta events för kommande vecka (svensk tid)
    now_dt = datetime.now(SWEDEN_TZ)
    one_week_dt = now_dt + timedelta(days=7)

    time_min = now_dt.isoformat()
    time_max = one_week_dt.isoformat()

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Samla events per datum
    days_map = {}
    for event in events:
        start_dt = event['start'].get('dateTime')
        start_date = event['start'].get('date')

        if start_dt:
            # Timed event
            dt = datetime.fromisoformat(start_dt.replace("Z", "+00:00")).astimezone(SWEDEN_TZ)
            date_key = dt.date()
            time_str = dt.strftime("%H:%M")
        elif start_date:
            # All-day event
            date_key = datetime.fromisoformat(start_date).date()
            time_str = None
        else:
            continue  # hoppa över om start saknas helt

        days_map.setdefault(date_key, []).append({
            "time": time_str,
            "title": event.get('summary', '(Ingen titel)')
        })

    # Bygg JSON-struktur
    json_data = {
        "generated_at": now_dt.isoformat(timespec="minutes"),
        "days": []
    }

    today = now_dt.date()
    for i in range(7):
        date_key = today + timedelta(days=i)
        events_list = days_map.get(date_key, [])

        # Sortera: utan tid först
        events_list.sort(key=lambda e: (e["time"] is not None, e["time"] or ""))

        json_data["days"].append({
            "label": dk_label(date_key),
            "events": events_list
        })

    # Spara JSON
    os.makedirs("data", exist_ok=True)
    with open("data/calendar.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    ts = datetime.now(SWEDEN_TZ).isoformat(timespec="seconds")
    print(f"[{ts}] ✅ Wrote to data/calendar.json")

if __name__ == '__main__':
    main()
