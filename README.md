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

## Python translation

This repository also includes a standard-library Python translation in [app.py](app.py). It preserves the same protected app sections, local profile editing, dashboard data, sync action, and notification prompts without requiring Node.js or Firebase credentials.

Run it with:

`python3 app.py`

Then open:

`http://127.0.0.1:3000`

Optional environment variables:

- `PORT`: change the local port, for example `PORT=3001 python3 app.py`
- `HOST`: change the bind host
- `FILIATION_SECRET`: set a stronger local session-signing secret
- `FILIATION_DATA_DIR`: change where local profile data is stored
