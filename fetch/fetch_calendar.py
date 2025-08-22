#!/usr/bin/env python3
import os
import pickle
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

# Ladda miljövariabler
load_dotenv()
token_path = os.getenv("GOOGLE_TOKEN_PATH", ".config/token.pickle")

# Svensk tidszon
SWEDEN_TZ = ZoneInfo("Europe/Stockholm")

# Dansk veckodag/månad
DK_WD = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]
DK_MON = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

def dk_label(d):
    """Format: 'Man 22/Aug' (d kan vara date eller datetime)."""
    if isinstance(d, datetime):
        d = d.date()
    return f"{DK_WD[d.weekday()]} {d.day:02d}/{DK_MON[d.month-1]}"

def is_all_day(ev: dict) -> bool:
    return "date" in ev.get("start", {}) and "date" in ev.get("end", {})

def iter_all_day_dates(ev: dict):
    """Yield alla datum som ett heldagsevent täcker (end.date är exklusiv)."""
    s = date.fromisoformat(ev["start"]["date"])
    e = date.fromisoformat(ev["end"]["date"])  # exklusiv
    d = s
    while d < e:
        yield d
        d += timedelta(days=1)

def parse_dt_iso_zaware(s: str) -> datetime:
    """Tål 'Z' (UTC) och offset, returnerar svensk tid."""
    # google kan ge '...Z' eller med offset. Gör tz-aware och konvertera.
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(SWEDEN_TZ)

def main():
    # Läs Google Calendar credentials
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)
    calendar_id = 'family12428309117852465721@group.calendar.google.com'

    # Tidsfönster: 14 dagar bakåt, 7 dagar framåt — hela dygn
    now_dt = datetime.now(SWEDEN_TZ)
    today_start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    time_min = (today_start - timedelta(days=14)).isoformat()
    time_max = (today_start + timedelta(days=7)).isoformat()

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,            # instanser av återkommande
        orderBy='startTime',
        timeZone="Europe/Stockholm",
        maxResults=2500
    ).execute()

    events = events_result.get('items', [])

    # Samla events per datum
    days_map: dict[date, list] = {}

    for event in events:
        if is_all_day(event):
            # Heldags- (även fler-dagars) → lägg till på varje dag
            for d in iter_all_day_dates(event):
                days_map.setdefault(d, []).append({
                    "time": None,
                    "title": event.get("summary", "(Ingen titel)")
                })
        else:
            # Tidsatta event → lägg på startdagen
            start_dt = event['start'].get('dateTime')
            if not start_dt:
                continue
            dt = parse_dt_iso_zaware(start_dt)
            date_key = dt.date()
            time_str = dt.strftime("%H:%M")
            days_map.setdefault(date_key, []).append({
                "time": time_str,
                "title": event.get('summary', '(Ingen titel)')
            })

    # Bygg JSON-struktur (alltid 7 dagar framåt från idag)
    json_data = {
        "generated_at": now_dt.isoformat(timespec="minutes"),
        "days": []
    }

    for i in range(7):
        d = today_start.date() + timedelta(days=i)
        events_list = days_map.get(d, [])
        # Sortera: heldag (None) först, sedan stigande klockslag
        events_list.sort(key=lambda e: (e["time"] is not None, e["time"] or ""))
        json_data["days"].append({
            "label": dk_label(d),
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
