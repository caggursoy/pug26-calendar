# PuG2026 Calendar
A small Python utility that scrapes the PUG 2026 conference agenda and writes the sessions into Google Calendar.

It follows each session link, pulls the detailed session information, and creates calendar events you can subscribe to from your usual calendar apps.

## Table Of Contents

- [Subscribing to the Calendar](#subscribing-to-the-calendar)
- [About The Project](#about-the-project)
- [Built With](#built-with)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Google Calendar Notes](#google-calendar-notes)

## Subscribing to the Calendar

Click the following Google Calendar link to add your instance

### If you want to use the calendar without personalising (removing the parallel sessions that you might not attend) just use the link below

- Just click this link and it should be automatically added to your Google Calendar
  - [Link](https://calendar.google.com/calendar/u/0?cid=ZTNiODRiZTlmMzlhMmYzODc1NjRlNGQxYTRjM2JjMTAzYTA2ZDhlMTQ1N2U0ZDdmZWVmMzUyMzIwYjAzMjUzNEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t)

### Duplicating and creating your own calendar

If you want to personalise your own calendar by removing some of the sessions from the whole calendar, you can follow the steps below to duplicate the calendar and create your own

#### Step 1: Export the Calendar

1. **Download the `.ics` file**

   - Go to [this link](https://drive.google.com/file/d/1nKYj1t0bnFOkBodkQ4t3s9GmghEe80U-/view?usp=sharing) and download the `.ics` calendar file

#### Step 2: Create a New Calendar

1. **Go to Google Calendar**:

   - If you're not already there, go back to [Google Calendar](https://calendar.google.com).

2. **Create a New Calendar**:
   - Click on the `+` icon next to `Other calendars` on the left sidebar.
   - Select `Create new calendar`.
   - Fill in the details for your new calendar and click `Create calendar`.

#### Step 3: Import the Calendar

1. **Go to Settings**:

   - Click on the gear icon in the top-right corner and select `Settings` if you're not already in `Settings`.

2. **Select Import & Export**:

   - In the left sidebar, click on `Import & export`.

3. **Import the .ics File**:
   - In the `Import` section, click on `Select file from your computer`.
   - Choose the `.ics` file you downloaded earlier.
   - In the `Add to calendar` drop-down menu, select the new calendar you created in the previous step.
   - Click `Import`.

Your new calendar should now contain all the events from the original calendar.
Now you can uncheck the original `PuG24-Calendar` from the `My calendars` panel and start editing your own instance.


## About The Project

`pug26-calendar` reads the public PUG 2026 agenda from ConfTool, extracts the session schedule, opens each session page to gather the detailed description and abstract, and writes the result to a Google Calendar.

This is useful if you want to:

- browse the conference program from your calendar app
- subscribe to a dedicated conference calendar on phone or desktop
- keep the conference schedule separate from your personal calendar

The script currently:

- parses the list view of the PUG 2026 agenda
- follows each session link to fetch detailed session information
- creates Google Calendar events with title, time, location, and description
- supports writing either to your primary calendar or to a specific target calendar

## Built With

This project uses:

- Python 3.11+
- `uv` for environment and dependency management
- `requests` for fetching agenda pages
- `beautifulsoup4` for HTML parsing
- `gcsa` for Google Calendar integration

## Getting Started

### Prerequisites

- Python 3.11 or newer
- `uv` installed locally
- a Google Cloud OAuth client configured as a `Desktop app`

### Installation

1. Install dependencies:

	 ```bash
	 uv sync
	 ```

2. In Google Cloud Console, create an OAuth client ID with application type `Desktop app`.

3. Download the OAuth client JSON and save it in the project root as `credentials.json`.

	 Important:
	 The script expects a Desktop app OAuth client. A Web client will fail with `redirect_uri_mismatch`.

## Usage

Run the script with:

```bash
uv run python main.py
```

The first successful run will open the Google OAuth flow in your browser and store the local auth token for later runs.

To write events to a specific calendar for a single run:

```bash
uv run python main.py --calendar-id your_calendar_id@group.calendar.google.com
```

## Google Calendar Notes

If you do not pass `--calendar-id`, the script resolves the destination calendar in this order:

1. `--calendar-id`
2. top-level `calendar_id` in `credentials.json`
3. `GOOGLE_CALENDAR_ID`
4. `PUG26_CALENDAR_ID`
5. `primary`

To use an environment variable instead of a command-line flag:

```bash
export GOOGLE_CALENDAR_ID="your_calendar_id@group.calendar.google.com"
uv run python main.py
```

You can find a calendar ID in Google Calendar under:

`Settings and sharing` -> `Integrate calendar` -> `Calendar ID`