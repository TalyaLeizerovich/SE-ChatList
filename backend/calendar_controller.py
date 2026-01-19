import os
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ============================
# CONFIG
# ============================
SCOPES = ['https://www.googleapis.com/auth/calendar']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(BASE_DIR, "calendar_profile")

TOKEN_PATH = os.path.join(PROFILE_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(PROFILE_DIR, "credentials.json")


# ============================
# CONNECT / AUTH
# ============================
def connect_calendar():
    """
    Connect to Google Calendar API using OAuth2.
    
    On first run, will open browser for authentication.
    Subsequent runs will use saved token.
    
    Returns:
        Google Calendar API service object
    """
    creds = None

    # Try to load existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            creds.refresh(Request())
        else:
            # First time authentication
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Missing credentials.json file at: {CREDENTIALS_PATH}\n"
                    "Please download it from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Enable Google Calendar API\n"
                    "3. Create OAuth 2.0 credentials (Desktop app)\n"
                    "4. Download and save as credentials.json"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future use
        os.makedirs(PROFILE_DIR, exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


# ============================
# ADD EVENT
# ============================
def add_task_to_calendar(task_text: str, event_date: datetime):
    """
    Add a task to Google Calendar as an all-day event.
    
    Args:
        task_text: Task description (will be event summary)
        event_date: datetime object for the event date
    
    Raises:
        HttpError: If API call fails
    """
    try:
        service = connect_calendar()

        # Create all-day event
        event = {
            'summary': task_text,
            'start': {'date': event_date.date().isoformat()},
            'end': {'date': event_date.date().isoformat()},
            'description': f'נוצר מ-ChatList ב-{datetime.now().strftime("%d/%m/%Y %H:%M")}'
        }

        # Insert event to primary calendar
        result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        print(f"Event created: {result.get('htmlLink')}")
        return result
        
    except HttpError as error:
        print(f"Google Calendar API error: {error}")
        raise
    except Exception as error:
        print(f"Unexpected error: {error}")
        raise