import argparse
import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
from datetime import datetime, timedelta

AGENDA_URL = "https://www.conftool.com/pug2026/index.php?page=browseSessions&form_date=all&mode=list&presentations=hide"


def validate_credentials_data(credentials_data):
    if "installed" in credentials_data:
        return

    if "web" in credentials_data:
        raise RuntimeError(
            "credentials.json contains a Google OAuth Web client. "
            "This local script needs a Desktop app OAuth client, otherwise Google returns redirect_uri_mismatch. "
            "Create a new OAuth client in Google Cloud Console with application type 'Desktop app', "
            "download its JSON, and replace credentials.json."
        )

    raise RuntimeError(
        "credentials.json is missing a supported Google OAuth client block. "
        "Expected an 'installed' client from a Desktop app OAuth credential."
    )


def resolve_calendar_id(credentials_data):
    if "calendar_id" in credentials_data:
        return credentials_data["calendar_id"]

    for client_type in ("installed", "web"):
        client_config = credentials_data.get(client_type, {})
        if "calendar_id" in client_config:
            return client_config["calendar_id"]

    return os.environ.get("GOOGLE_CALENDAR_ID") or os.environ.get("PUG26_CALENDAR_ID") or "primary"


def parse_args():
    parser = argparse.ArgumentParser(description="Create Google Calendar events from the PUG 2026 agenda.")
    parser.add_argument(
        "--calendar-id",
        help="Google Calendar ID to write to. Overrides credentials.json and environment variables.",
    )
    return parser.parse_args()


def parse_date_header(text):
    cleaned = text.replace("Date:", "", 1).strip()
    return datetime.strptime(cleaned, "%A, %d/%B/%Y").date()


def parse_time_range(date_value, time_text):
    start_text, end_text = [part.strip().lower() for part in time_text.split("-", maxsplit=1)]
    start_time = datetime.strptime(start_text, "%I:%M%p").time()
    end_time = datetime.strptime(end_text, "%I:%M%p").time()

    start = datetime.combine(date_value, start_time)
    end = datetime.combine(date_value, end_time)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def build_detail_url(session_url):
    parsed = urlparse(session_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["presentations"] = "show"
    return urlunparse(parsed._replace(query=urlencode(query)))


def fetch_detailed_description(http_session, detail_url):
    response = http_session.get(detail_url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    description_parts = []

    session_info = soup.select_one("div.session_info")
    if session_info is not None:
        session_info_text = session_info.get_text("\n", strip=True)
        if session_info_text:
            description_parts.append(session_info_text)

    abstracts = [
        abstract.get_text(" ", strip=True)
        for abstract in soup.select("p.paper_abstract")
        if abstract.get_text(" ", strip=True)
    ]
    if abstracts:
        description_parts.append("Session Abstract:\n" + "\n\n".join(abstracts))

    return description_parts


def extract_session_details(http_session, details_cell):
    title_link = details_cell.find("a", href=True)
    if title_link is None:
        return None

    title = title_link.get_text(" ", strip=True)
    session_url = urljoin(AGENDA_URL, title_link["href"])
    detail_url = build_detail_url(session_url)
    lines = [line.strip() for line in details_cell.stripped_strings if line.strip()]

    location = ""
    chairs = []
    description_lines = []
    for line in lines[1:]:
        if line.startswith("Location:"):
            location = line.removeprefix("Location:").strip()
        elif line.startswith("Chair:"):
            chairs.append(line.removeprefix("Chair:").strip())
        elif line.startswith("Chairs:"):
            chairs.append(line.removeprefix("Chairs:").strip())
        else:
            description_lines.append(line)

    description_parts = []
    if chairs:
        description_parts.append("Chair(s): " + "; ".join(chairs))
    description_parts.extend(description_lines)

    try:
        description_parts.extend(fetch_detailed_description(http_session, detail_url))
    except requests.RequestException:
        pass

    description_parts.append(detail_url)

    return {
        "title": title,
        "location": location,
        "description": "\n".join(part for part in description_parts if part),
    }


def download_schedule():
    http_session = requests.Session()
    response = http_session.get(AGENDA_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select('tr')
    sessions = []
    current_date = None

    for row in rows:
        header = row.find('b')
        if header is not None and 'Date:' in header.get_text(' ', strip=True):
            current_date = parse_date_header(header.get_text(' ', strip=True))
            continue

        cells = row.find_all('td', recursive=False)
        if current_date is None or len(cells) < 2:
            continue

        time_text = cells[0].get_text(' ', strip=True)
        if '-' not in time_text:
            continue

        session_details = extract_session_details(http_session, cells[1])
        if session_details is None:
            continue

        start_time, end_time = parse_time_range(current_date, time_text)
        sessions.append(
            {
                'summary': session_details['title'],
                'description': session_details['description'],
                'location': session_details['location'],
                'start': start_time,
                'end': end_time,
            }
        )

    return sessions

def conf_gcal(calendar_id_override=None):
    with open('./credentials.json', 'r', encoding='utf-8') as f:
        credentials_data = json.load(f)
    validate_credentials_data(credentials_data)
    calendar_id = calendar_id_override or resolve_calendar_id(credentials_data)
    print(f"Using calendar: {calendar_id}")
    try:
        gcal = GoogleCalendar(calendar_id, credentials_path='./credentials.json')  # Set the Google Calendar
    except Exception as e:
        if os.path.isfile('token.pickle'):
            os.remove('token.pickle')  # Remove the pickle file
            gcal = GoogleCalendar(calendar_id, credentials_path='./credentials.json')  # Retry
        else:
            print(e)
            sys.exit()
    return gcal

def flush_cal(gcal):
    for g_ev in gcal:  # Delete every event in the calendar
        gcal.delete_event(g_ev)

def read_and_create(calendar, sessions):
    for session in sessions:
        event = Event(
            summary=session['summary'],
            description=session['description'],
            start=session['start'],
            end=session['end'],
            location=session['location'],
            minutes_before_popup_reminder=10,
        )
        calendar.add_event(event)

def main():
    args = parse_args()

    # Download the schedule
    sessions = download_schedule()

    # Connect to Google Calendar
    gcal = conf_gcal(args.calendar_id)

    # Flush the calendar
    flush_cal(gcal)

    # Create events in the calendar
    read_and_create(gcal, sessions)

if __name__ == '__main__':
    main()