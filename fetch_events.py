import pickle
import datetime
from googleapiclient.discovery import build

def main():
    # Ladda autentiserings-token
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)

    # Ange kalender-ID här (t.ex. "Familie")
    calendar_id = 'family12428309117852465721@group.calendar.google.com'

    # Hämta events från nu och en vecka framåt
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    one_week = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=one_week,
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
