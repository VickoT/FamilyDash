import pickle
from datetime import datetime, timedelta, UTC
import os
from dotenv import load_dotenv


from googleapiclient.discovery import build


load_dotenv()
token_path = os.getenv("GOOGLE_TOKEN_PATH", ".config/token.pickle")


def main():
    # Ladda autentiserings-token
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)

    # Ange kalender-ID här (t.ex. "Familie")
    calendar_id = 'family12428309117852465721@group.calendar.google.com'


    # Hämta events från nu och en vecka framåt – tidszonsmedvetet i UTC
    now_dt = datetime.now(UTC)
    one_week_dt = now_dt + timedelta(days=7)

    # Google Calendar vill ha RFC3339. Använd 'Z' för UTC.
    time_min = now_dt.isoformat().replace("+00:00", "Z")       # ← ÄNDRAT
    time_max = one_week_dt.isoformat().replace("+00:00", "Z")  # ← ÄNDRAT

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        print('Inga kommande händelser hittades.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start}: {event.get('summary', '(Ingen titel)')}")

if __name__ == '__main__':
    main()
