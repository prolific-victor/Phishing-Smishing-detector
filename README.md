# CyberGuard AI — Cybersecurity Assistant

CyberGuard AI is a phishing detection demo with a browser based scanner, a FastAPI backend, URL and message classifiers, and an admin dashboard. It can optionally check scanned URLs against Google Safe Browsing. A Chrome extension and Telegram bot are also included as optional integrations.

The project is intended for learning and demonstration. Its model output is an indicator, not a guarantee that a URL or message is safe. Do not use it as the only security control.

## Contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Project layout](#project-layout)
- [Requirements](#requirements)
- [Run locally from a fresh clone](#run-locally-from-a-fresh-clone)
- [Train or refresh the models (optional)](#train-or-refresh-the-models-optional)
- [Configure Google Safe Browsing (optional)](#configure-google-safe-browsing-optional)
- [API reference](#api-reference)
- [Optional integrations](#optional-integrations)
- [Troubleshooting](#troubleshooting)
- [Data, privacy, and limitations](#data-privacy-and-limitations)
- [License](#license)

## What it does

- **URL scanning:** extracts URL characteristics and classifies phishing risk with a Random Forest model. If configured, it also queries Google Safe Browsing for known threats.
- **Message scanning:** classifies text for phishing and smishing patterns with a TF-IDF and Logistic Regression model.
- **Web interface:** provides a chat style scanner and an admin dashboard with scan history and counts.
- **Chrome extension:** provides a popup and a right click action to submit links to the local API.
- **Telegram bot:** optionally forwards URLs and messages to the API.

## How it works

The browser interface is static HTML, CSS, and JavaScript in `frontend/`. FastAPI serves that interface and the JSON API from the same local server. The backend loads the trained model files from `backend/ml/`, checks URLs with the URL model and messages with the text model, and stores scan results in a local SQLite database (`cyber_assistant.db`).

For a scan, the page sends the content to the matching API endpoint. The backend returns a risk score, risk label, indicators, and advice; URL responses also include a reputation status. The scan and its complete result are stored in SQLite. The dashboard shows the most recent ten saved scans; select a row or use its **View result** button to open the saved report. The API adds the `result_details` field to an existing local database automatically when the server starts. History created before full result storage was introduced only has its original content, label, and score.

The model artifact files are included in the repository, so you can start the app without downloading datasets or retraining. The first run creates the SQLite database and its tables. You do not need Node.js or npm for the web app.

## Project layout

```text
.
├── api/                     # Serverless API entry points
├── backend/
│   ├── data/                 # Dataset preparation notes and CSV datasets
│   ├── ml/                   # Feature extraction, training, and saved models
│   ├── database.py           # SQLite engine and scan history
│   ├── main.py               # FastAPI app, web routes, and scan endpoints
│   ├── models.py             # API request/response schemas
│   └── reputation.py         # Optional Google Safe Browsing lookup
├── bot/                      # Optional Telegram bot
├── extension/                # Optional Chrome extension
├── frontend/                 # Scanner, dashboard, styles, and browser code
├── public/                   # Deployment copies of static frontend files
├── requirements.txt          # Python backend dependencies
└── vercel.json               # Vercel routing configuration
```

## Requirements

- Git
- Python 3.10 or newer (Python 3.11 or 3.12 are good choices)
- Internet access only when installing packages, downloading optional training datasets, or using Safe Browsing

Use a virtual environment so the project dependencies do not affect your system Python. On Debian/Kali, if `venv` creation fails, install the OS package that provides Python venv (commonly `python3-venv`) and try again.

## Run locally from a fresh clone

### 1. Clone the repository

```bash
git clone https://github.com/cliffkeys/cyber-security-assistant.git
cd cyber-security-assistant
```

If you already have a clone, go to its directory instead:

```bash
cd ~/Downloads/cyber-security-assistant
```

### 2. Create and activate a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Start the web app and API

From the repository root, with the virtual environment activated:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Or, without activating the environment on Linux/macOS:

```bash
./.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal open while using the app. Open these addresses in your browser:

- Scanner: <http://127.0.0.1:8000/>
- Dashboard: <http://127.0.0.1:8000/admin.html>
- API health: <http://127.0.0.1:8000/api/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>

Stop the server with **Ctrl+C** in its terminal. To use another port, replace `8000` in the command and open the matching local address. The web page must be served by FastAPI; opening `frontend/index.html` directly as a `file://` page will not connect to the API.

## Train or refresh the models (optional)

This step is not required for a fresh run because saved model artifacts are supplied. Run it if you want to recreate or update them. Training with the real public datasets first requires internet access and can take time and disk space.

With the virtual environment active, from the repository root:

```bash
python backend/ml/fetch_real_datasets.py
python backend/ml/train_models.py
```

Dataset preparation writes normalized files to `backend/data/real_url_dataset.csv` and `backend/data/real_message_dataset.csv`. The trainer uses those files when present and otherwise falls back to the small synthetic CSVs. It saves updated artifacts in `backend/ml/`. Dataset sources, labels, and licenses are listed in [backend/data/README.md](backend/data/README.md). The URL data is processed as text; the downloader does not visit the URLs in the corpus.

## Configure Google Safe Browsing (optional)

Without a key, URL model analysis still works; the live reputation result reports that it is not configured. To enable the live lookup, obtain a Google Safe Browsing API key for your intended use and set it only in the backend process environment. Do not put it in frontend JavaScript, source control, screenshots, or public issue reports.

Linux/macOS shell example (prompts without echoing the key):

```bash
read -rsp 'Google Safe Browsing API key: ' GOOGLE_SAFE_BROWSING_API_KEY; echo
export GOOGLE_SAFE_BROWSING_API_KEY
./.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The key is sent to Google with each uncached URL lookup, and the submitted URL is also sent to Google. Review Google's current terms and privacy information before enabling it. A URL that is not listed by Safe Browsing is not thereby proven safe. To disable the check, stop the server, unset the variable (`unset GOOGLE_SAFE_BROWSING_API_KEY`), and start it again.

The shell example above is for Linux/macOS. On Windows PowerShell, set the variable for the current terminal before starting Uvicorn:

```powershell
$secureKey = Read-Host -AsSecureString "Google Safe Browsing API key"
$env:GOOGLE_SAFE_BROWSING_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## API reference

The local API is served on the same host and port as the web app. Scan requests use JSON with a `content` string.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check that the service is running |
| `POST` | `/api/scan/url` | Analyze a URL |
| `POST` | `/api/scan/message` | Analyze a message |
| `GET` | `/api/admin/stats` | Get dashboard counts and recent scans |
| `DELETE` | `/api/admin/history` | Delete all saved scans |
| `DELETE` | `/api/admin/history?scan_id=123` | Delete one saved scan by ID |

The dashboard keeps a local scan history in `cyber_assistant.db`, created in the repository directory when the app starts. The newest ten records are returned to the dashboard. Select a row or choose **View result** to review a saved report. Choose **Delete** to remove one scan, or **Clear history** to remove every saved scan; both actions ask for confirmation. Deletion is permanent. On your own machine, back up the database file if you need to keep its history. Do not delete it while the server is running if you want to preserve the data.

Example URL scan from another terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/scan/url \
  -H 'Content-Type: application/json' \
  -d '{"content":"https://example.com"}'
```

Example message scan:

```bash
curl -X POST http://127.0.0.1:8000/api/scan/message \
  -H 'Content-Type: application/json' \
  -d '{"content":"Your account is locked. Verify it now."}'
```

The response includes a risk score, risk level, indicators, and a recommendation. URL responses also include the live reputation status. `/docs` provides interactive OpenAPI documentation.

## Optional integrations

### Chrome extension

1. Start the local FastAPI server.
2. In Chrome, open `chrome://extensions/` and turn on **Developer mode**.
3. Choose **Load unpacked** and select this repository's `extension/` directory.
4. Use the extension popup or right click a link and select **Scan link for phishing**.

The extension is configured to call `http://127.0.0.1:8000`; it needs the backend running on that address. It is intended for local development, not distribution as a production extension.

### Telegram bot

The bot is optional and is not included in `requirements.txt`. Install its extra dependencies in the virtual environment:

```bash
python -m pip install python-telegram-bot requests
```

Set a bot token from Telegram's BotFather as the `TELEGRAM_TOKEN` value in `bot/telegram_bot.py`, then start the backend and, in another terminal with the same environment active, run:

```bash
python bot/telegram_bot.py
```

Keep both processes running. Treat the token as a secret and do not commit a real token. The current bot connects to the API at `http://127.0.0.1:8000/api`.

## Troubleshooting

- **`Address already in use`:** another server is using port 8000. Stop it with Ctrl+C, or start this app with another port, for example `--port 8001`, then open `http://127.0.0.1:8001/`.
- **`ModuleNotFoundError` or missing packages:** activate `.venv` and run `python -m pip install -r requirements.txt` from the project root. Make sure the server is started using that environment's Python.
- **`No such file or directory: .venv/bin/python`:** create the environment using the steps above, or activate it and use `python -m uvicorn ...`.
- **Model file missing or incompatible:** confirm `backend/ml/url_model.pkl`, `message_model.pkl`, and `vectorizer.pkl` exist. Reinstall the requirements in a clean virtual environment; if needed, fetch data and retrain the models.
- **Browser shows an offline result:** the web page includes a lightweight browser-only fallback. Check that the backend terminal still shows Uvicorn running and that the browser is visiting the same host and port.
- **`GET /favicon.ico` returns `404`:** browsers often ask for the conventional icon path automatically. This project provides a linked SVG favicon; if the browser still logs the old request, reload without cache or clear that site's cached page.
- **`304 Not Modified` in server logs:** this is a normal HTTP cache response. The browser already has an unchanged file and reuses its cached copy; it is not an application error. Use a hard reload to request fresh assets while debugging.
- **History entries do not open:** restart Uvicorn after pulling or editing backend changes, open `http://127.0.0.1:8000/admin.html`, and hard reload with Ctrl+Shift+R. Each row is keyboard accessible (Tab to a row, then Enter or Space) and has a **View result** button. The dashboard refreshes history every ten seconds.
- **A past entry has no indicators or recommendation:** versions before full-result history only stored the scan content, classification, and score. Those details cannot be recovered exactly; scans created after this update save the full report.
- **Safe Browsing status is unavailable:** check the key, network access, and API configuration. The URL classifier continues to work without a successful reputation lookup.

## Deployment notes

`api/` contains lightweight serverless handlers and `public/` contains static deployment assets. For local development, follow the Uvicorn instructions above; this does not require a cloud account. The current database setup uses a local SQLite file when writable and `/tmp/cyber_assistant.db` in common serverless environments. `/tmp` storage may be temporary, so it should not be treated as durable shared history for a production deployment. Configure a durable database before deploying for persistent multi-user use.

## Data, privacy, and limitations

Scan requests are processed by the local API. Results are stored in the local SQLite database and the admin dashboard displays scan history. Do not submit private, regulated, or otherwise sensitive messages unless you are comfortable storing them in this database. If Safe Browsing is configured, URL scans are also sent to Google for reputation lookup.

Classifier results can be wrong, and attackers change tactics. The trained models and datasets are benchmarks and may not reflect current threats. A “Safe” classification or no Safe Browsing listing is not a safety guarantee. Verify suspicious communications through a trusted channel and use appropriate security controls.

## License

The earlier project documentation identifies the code as MIT-licensed, but this repository does not currently contain a standalone `LICENSE` file. Dataset licenses and attribution are documented separately in [backend/data/README.md](backend/data/README.md).
