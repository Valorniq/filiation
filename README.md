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

After signing in, open `Setup` in the left navigation or visit:

`http://127.0.0.1:3000/connections`

That page lets you paste testing keys in plain language, saves them to `.env.local`, masks secrets when the page reloads, and updates the running app without making you restart for most local testing.

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

For testing, create a Gemini key from Google AI Studio, paste it into `Setup > Assistant Brain`, and save.

### API integrations

Finance defaults to Direct so you can test with local bank export files or your own endpoint without Plaid or another data broker:

- `FINANCE_PROVIDER`: `direct`, `json`, or `plaid`, default `direct`
- `BANK_ACCOUNTS_FILE`: optional CSV or JSON file with account rows
- `BANK_TRANSACTIONS_FILE`: optional CSV or JSON file with transaction rows
- `FINANCE_DATA_URL`: optional direct/custom endpoint returning `{ "accounts": [], "transactions": [] }`
- `FINANCE_API_TOKEN`: optional bearer token for `FINANCE_DATA_URL`

Local CSV files can use common column names such as `name`, `account`, `bank`, `balance`, `mask`, `date`, `description`, `merchant`, `amount`, and `category`.

Plaid remains optional:

- `PLAID_ENV`: `sandbox`, `development`, or `production`
- `PLAID_CLIENT_ID`
- `PLAID_SECRET`
- `PLAID_ACCESS_TOKEN`
- `PLAID_TRANSACTION_COUNT`: optional, default `50`

In `Setup > Finance`, users can choose `Direct`, `Plaid`, or `Custom API`. For testing Plaid specifically, set `FINANCE_PROVIDER=plaid`, paste your Plaid sandbox client ID and sandbox secret, then click `Create optional Plaid sandbox connection`.

When `FINANCE_PROVIDER=direct`, the app reads local bank files first unless `FINANCE_DATA_URL` is set, in which case it reads that direct endpoint.

Calendar can use iCalendar first, then fall back to Google Calendar when configured:

- `CALENDAR_PROVIDER`: `auto`, `icalendar`, or `google`, default `auto`
- `ICALENDAR_URL`: public/private `.ics` subscription URL from Apple Calendar, Outlook, school calendars, etc.
- `ICALENDAR_FILE`: local `.ics` export file path
- `ICALENDAR_API_TOKEN`: optional bearer token for protected `.ics` feeds

Google Calendar remains optional:

- `GOOGLE_CLIENT_ID`: OAuth client ID for the built-in Connect Google flow
- `GOOGLE_CLIENT_SECRET`: OAuth client secret for the built-in Connect Google flow
- `GOOGLE_REDIRECT_URI`: optional callback URL, default `http://127.0.0.1:3000/integrations/google/callback`
- `GOOGLE_CALENDAR_ID`: default `primary`
- `GOOGLE_CALENDAR_ACCESS_TOKEN`: optional direct token for private calendars
- `GOOGLE_CALENDAR_API_KEY`: for public calendars

For iCalendar, paste the `.ics` URL or file path into `Setup > Family Calendar`. For Google OAuth, add the redirect URI above to your Google Cloud OAuth client, start the app, sign in locally, then use `Connect Google` from Calendar or Sync. Refresh tokens are stored in `FILIATION_DATA_DIR/google_tokens.json`, which is ignored by git.

The `Setup > Family Calendar` card shows the exact redirect URI your current server expects.

Weather uses the National Weather Service:

- `FILIATION_LAT`
- `FILIATION_LON`

Weather does not require an API key.

School lets users choose the front-end system label while keeping the backend URL flexible:

- `SCHOOL_PROVIDER`: `infinite_campus`, `schoology`, `canvas`, or `custom_json`
- `SCHOOL_EVENTS_URL` and optional `SCHOOL_API_TOKEN`

Health, logistics, P2P requests, and family members use generic JSON endpoints. Each endpoint can return either a list or an object with `items`, `data`, or `results`.

- `HEALTH_EVENTS_URL` and optional `HEALTH_API_TOKEN`
- `LOGISTICS_EVENTS_URL` and optional `LOGISTICS_API_TOKEN`
- `P2P_REQUESTS_URL` and optional `P2P_API_TOKEN`
- `FAMILY_MEMBERS_URL` and optional `FAMILY_API_TOKEN`
