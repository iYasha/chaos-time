import argparse
import os.path
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from utils import Time
from utils import set_date_args
from texttable import Texttable


class CalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/contacts.other.readonly']
    CREDENTIALS_PATH = os.path.expanduser('~/google-calendar-token.json')

    def __init__(self):
        if os.getenv('GOOGLE_API_CREDENTIALS') is None:
            raise ValueError('GOOGLE_API_CREDENTIALS environment variable is not set')
        creds = None
        if os.path.exists(self.CREDENTIALS_PATH):
            creds = Credentials.from_authorized_user_file(self.CREDENTIALS_PATH, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('GOOGLE_API_CREDENTIALS'), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(self.CREDENTIALS_PATH, 'w') as token:
                token.write(creds.to_json())
        self.service = build('calendar', 'v3', credentials=creds)

    def get_events(self, date_from: datetime, date_to: datetime) -> list:
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=date_from.isoformat() + 'Z',
            timeMax=date_to.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime',
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return []
        return events

    def get_work_events(self, date_from: datetime) -> tuple[timedelta, list]:
        events = []
        total_time = timedelta()

        date_to = date_from.replace(hour=23, minute=59, second=59)

        for event in self.get_events(date_from, date_to):
            if 'visibility' in event and event['visibility'] == 'private':
                continue
            self_response = next(iter([x['responseStatus'] for x in event['attendees'] if 'self' in x]), None)
            if self_response != 'accepted':
                continue
            events.append(event)
            event['start'] = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
            event['end'] = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
            delta = event['end'] - event['start']
            total_time += delta
        return total_time, events

    @classmethod
    def add_parser(cls, subparser):
        parser = subparser.add_parser('calendar', help='Google Calendar')

        set_date_args(parser)

        parser.add_argument('-l', '--list', help='Show only total time spent', nargs=argparse.REMAINDER)
        parser.set_defaults(func=run)


def run(args):
    service = CalendarService()
    date_from = datetime(year=args.year, month=args.month, day=args.day)
    total_time, events = service.get_work_events(date_from)
    print(f'Communication for {date_from.strftime("%Y-%m-%d")}')
    print(f'Total time spent: {Time(total_time).human_readable}')
    if args.list is not None:
        return

    table_headers = ['Duration', 'Start', 'End', 'Summary']
    table_data = [(Time(x['end'] - x['start']).human_readable ,x["start"].strftime("%H:%M"), x["end"].strftime("%H:%M"), x["summary"]) for x in events]

    print(Texttable().add_rows([table_headers, *table_data]).draw())
