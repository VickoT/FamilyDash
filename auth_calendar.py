import os.path
import pickle
import datetime
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 👇 Scopes för att läsa kalenderdata
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

load_dotenv()
credential_file = os.getenv("GOOGLE_CLIENT_SECRET_FILE", ".config/client_secret.json")
token_path = os.getenv("GOOGLE_TOKEN_PATH", ".config/token.pickle")

def main():
    creds = None

    # Spara och återanvänd tokens
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # Logga in om vi inte redan har en giltig token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Spara för framtida användning
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Hämta och lista alla tillgängliga kalendrar
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])

    if not calendars:
        print('No calendars found.')
    for cal in calendars:
        print(f"{cal['summary']} → ID: {cal['id']}")

if __name__ == '__main__':
    main()
