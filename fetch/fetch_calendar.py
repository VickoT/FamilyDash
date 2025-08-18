import os
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime

load_dotenv()
token_path = os.getenv("GOOGLE_TOKEN_PATH", ".config/token.pickle")

# Dansk veckodag/månad
DK_WD = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]
DK_MON = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

def dk_label(dt):
    return f"{DK_WD[dt.weekday()]} {dt.day:02d}/{DK_MON[dt.month-1]}"

def main():
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)

    calendar_id = 'family12428309117852465721@group.calendar.google.com'

    now_dt = datetime.now(UTC)
    one_week_dt = now_dt + timedelta(days=7)

    time_min = now_dt.isoformat().replace("+00:00", "Z")
    time_max = one_week_dt.isoformat().replace("+00:00", "Z")

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
            dt = datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
            date_key = dt.date()
            time_str = dt.strftime("%H:%M")
        else:
            dt = datetime.fromisoformat(start_date)
            date_key = dt.date()
            time_str = None

        if date_key not in days_map:
            days_map[date_key] = []

        days_map[date_key].append({
            "time": time_str,
            "title": event.get('summary', '(Ingen titel)')
        })

    # Bygg JSON-struktur
    json_data = {
        "generated_at": datetime.now(timezone(timedelta(hours=2))).isoformat(timespec="minutes"),
        "days": []
    }

    today = datetime.now().date()
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

    ts = datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] ✅ Wrote to data/calendar.json")

if __name__ == '__main__':
    main()
