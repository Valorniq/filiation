<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/85889949-8052-4fb9-b823-096ee0dace8e

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Python API-backed app

This repository also includes a standard-library Python app in [app.py](app.py). It keeps the dashboard, auth shell, profile editing, sync status, and notification prompts, but it no longer ships with fake dashboard records. App pages read from configured APIs and show connection states until credentials or endpoint URLs are provided.

Run it with:

`python3 app.py`

Then open:

`http://127.0.0.1:3000`

Optional environment variables:

- `PORT`: change the local port, for example `PORT=3001 python3 app.py`
- `HOST`: change the bind host
- `FILIATION_SECRET`: set a stronger local session-signing secret
- `FILIATION_DATA_DIR`: change where local profile data is stored
- `FILIATION_API_TIMEOUT`: request timeout for provider calls, default `8`

### AI assistant

The Assistant page can answer questions across connected finance, calendar, school, health, logistics, P2P, weather, and family data. Without an AI key it falls back to a local readiness summary.

- `GEMINI_API_KEY`: enables generated assistant answers
- `GEMINI_MODEL`: optional, default `gemini-1.5-flash`

### API integrations

Finance uses Plaid:

- `PLAID_ENV`: `sandbox`, `development`, or `production`
- `PLAID_CLIENT_ID`
- `PLAID_SECRET`
- `PLAID_ACCESS_TOKEN`
- `PLAID_TRANSACTION_COUNT`: optional, default `50`

Calendar uses Google Calendar:

- `GOOGLE_CLIENT_ID`: OAuth client ID for the built-in Connect Google flow
- `GOOGLE_CLIENT_SECRET`: OAuth client secret for the built-in Connect Google flow
- `GOOGLE_REDIRECT_URI`: optional callback URL, default `http://127.0.0.1:3000/integrations/google/callback`
- `GOOGLE_CALENDAR_ID`: default `primary`
- `GOOGLE_CALENDAR_ACCESS_TOKEN`: optional direct token for private calendars
- `GOOGLE_CALENDAR_API_KEY`: for public calendars

For local OAuth, add the redirect URI above to your Google Cloud OAuth client, start the app, sign in locally, then use `Connect Google` from Calendar or Sync. Refresh tokens are stored in `FILIATION_DATA_DIR/google_tokens.json`, which is ignored by git.

Weather uses the National Weather Service:

- `FILIATION_LAT`
- `FILIATION_LON`

School, health, logistics, P2P requests, and family members use generic JSON endpoints. Each endpoint can return either a list or an object with `items`, `data`, or `results`.

- `SCHOOL_EVENTS_URL` and optional `SCHOOL_API_TOKEN`
- `HEALTH_EVENTS_URL` and optional `HEALTH_API_TOKEN`
- `LOGISTICS_EVENTS_URL` and optional `LOGISTICS_API_TOKEN`
- `P2P_REQUESTS_URL` and optional `P2P_API_TOKEN`
- `FAMILY_MEMBERS_URL` and optional `FAMILY_API_TOKEN`
