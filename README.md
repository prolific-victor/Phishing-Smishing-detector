# CyberGuard AI — Phishing and Smishing Assistant

CyberGuard AI is a learning and demonstration project for checking suspicious URLs and text messages. It combines a browser-based scanner, a FastAPI backend, machine-learning classifiers, and a local scan-history dashboard. Optional integrations include Google Safe Browsing, a Chrome extension, and a Telegram bot.

Automated results can be wrong. A **Safe** result does not prove that a URL or message is safe. Do not use this project as the only security control, and do not submit confidential messages unless you are comfortable storing them locally.

## Contents

- [Features](#features)
- [How a scan works](#how-a-scan-works)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Clone and run locally](#clone-and-run-locally)
- [Use the app](#use-the-app)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Optional integrations](#optional-integrations)
- [Model training and datasets](#model-training-and-datasets)
- [Database and privacy](#database-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Project status and license](#project-status-and-license)

## Features

- **URL analysis:** extracts simple URL characteristics and uses a saved Random Forest classifier to estimate phishing risk. A rule-based fallback is used if the model cannot be loaded.
- **Message analysis:** uses a saved TF-IDF vectorizer and Logistic Regression classifier to estimate smishing risk. A rule-based fallback is used if the model artifacts cannot be loaded.
- **Explanations:** returns a risk level, score, indicators, and a recommendation.
- **Web scanner:** a chat-style interface for submitting URLs and messages.
- **Admin dashboard:** shows scan counts and the latest ten saved scans; saved reports can be viewed or deleted.
- **Optional reputation check:** when configured, URL submissions are also checked against Google Safe Browsing.
- **Optional integrations:** a Chrome extension and a Telegram bot can send scans to the local API.

## How a scan works

The frontend in `frontend/` sends JSON requests to the FastAPI service in `backend/main.py`. The URL analyzer extracts eight features, including URL length, domain structure, suspicious characters or words, IP-address hostnames, and whether HTTPS is used. The message analyzer uses the saved text model and adds readable indicators for urgency, financial bait, and links.

The API responds with a risk score from 0 to 100, a `Safe`, `Suspicious`, or `Phishing` label, indicators, and a recommendation. URL responses also include the live reputation-check status. A URL not listed by Safe Browsing is not thereby proven safe.

Each scan is saved to a local SQLite database when the database write succeeds. The dashboard displays counts and the ten most recent records. It can show the full saved result for new scans and delete one record or all records. These deletion actions permanently remove the selected history.

The saved model files are included in the repository, so you do not need to train models to run the app. Node.js and npm are not required for the local web app.

## Repository structure

```text
.
├── api/                         # Serverless-style API entry points
│   ├── admin/                   # Dashboard statistics and history handlers
│   ├── scan/                    # URL and message scan handlers
│   ├── health.py                # Health handler
│   └── index.py                 # Main API handler
├── backend/
│   ├── data/                    # Sample and prepared datasets, attribution notes
│   ├── ml/                      # Feature extraction, training scripts, model artifacts
│   ├── database.py              # SQLAlchemy models and SQLite initialization
│   ├── main.py                  # FastAPI routes and frontend serving
│   ├── models.py                # Request and response schemas
│   └── reputation.py            # Optional Google Safe Browsing lookup
├── bot/                         # Optional Telegram bot
├── extension/                   # Optional Chrome extension source
├── frontend/                    # Local web scanner and dashboard
├── public/                      # Static deployment copies
├── requirements.txt             # Python dependencies for the web app/API
└── vercel.json                  # Deployment rewrite configuration
```

## Requirements

- Git
- Python 3.10 or newer
- Internet access to clone the repository and install Python packages
- A modern browser to use the web interface

Python 3.11 or 3.12 is recommended. On Debian or Kali, if creating a virtual environment fails because `venv` is missing, install the OS package that provides it (often `python3-venv`) and retry.

## Clone and run locally

### 1. Clone the GitHub repository

```bash
git clone https://github.com/prolific-victor/Phishing-Smishing-detector.git
cd Phishing-Smishing-detector
```

If you already cloned it, change to the directory containing this README instead. All commands below should be run from the repository root.

### 2. Create a Python virtual environment

#### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, either allow activation for the current user according to your organization's policy, or skip activation and use `.venv\Scripts\python.exe` for the commands below.

### 3. Start the app

With the virtual environment active, run:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal open while using the app. On Linux or macOS, you can start it without activating the environment by running `./.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`. On Windows, use `.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`.

### 4. Open the app and confirm the API is running

Open these addresses in your browser:

- Scanner: <http://127.0.0.1:8000/>
- Dashboard: <http://127.0.0.1:8000/admin.html>
- Health check: <http://127.0.0.1:8000/api/health>
- Interactive API documentation: <http://127.0.0.1:8000/docs>

The health check should return JSON indicating that the API is running. Use the dashboard after submitting scans to see saved results. Stop the server with **Ctrl+C** in its terminal.

The HTML pages should be opened through the local server, not directly as `file://` URLs. If port 8000 is already in use, change `--port 8000` to another port, such as `--port 8001`, and open the matching address in the browser.

## Use the app

1. Open the scanner page.
2. Enter a URL or a message in the scanner and submit it.
3. Review the risk level, score, indicators, recommendation, and (for URLs) reputation status.
4. Open the dashboard to review recent scans and totals.
5. Select a scan or its **View result** control to inspect the saved report. Use the delete controls to remove a scan or clear history.

Example API requests are shown in the [API reference](#api-reference). The browser interface uses the same local API.

## API reference

The local API is served from `http://127.0.0.1:8000`. Scan request bodies have a single string field named `content`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check service status |
| `POST` | `/api/scan/url` | Analyze a URL |
| `POST` | `/api/scan/message` | Analyze a message |
| `GET` | `/api/admin/stats` | Get scan counts and the latest ten saved scans |
| `DELETE` | `/api/admin/history?scan_id=123` | Delete one scan by ID |
| `DELETE` | `/api/admin/history` | Delete all scan history |

Example URL scan:

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

Scan responses include `risk_score`, `risk_level`, `indicators`, and `recommendation`. URL responses also include `live_reputation`, whose status can be `not_configured`, `unavailable`, `threat_found`, or `no_threat_found`. Full schemas and interactive request controls are available at <http://127.0.0.1:8000/docs> while the server is running.

## Configuration

### Google Safe Browsing (optional)

Without a key, URL classification still works and `live_reputation.status` is `not_configured`. To enable live lookups, obtain a Google Safe Browsing API key for your intended use and set it in the environment of the process that starts the backend. Never put the key in frontend code or commit it to the repository.

Linux/macOS shell:

```bash
read -rsp 'Google Safe Browsing API key: ' GOOGLE_SAFE_BROWSING_API_KEY; echo
export GOOGLE_SAFE_BROWSING_API_KEY
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
$secureKey = Read-Host -AsSecureString "Google Safe Browsing API key"
$env:GOOGLE_SAFE_BROWSING_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The submitted URL is sent to Google when a lookup is made. Results are briefly cached by the backend. Review Google's current terms and privacy information before enabling this integration. A `no_threat_found` response is not a safety guarantee. To disable the check, stop the server and unset `GOOGLE_SAFE_BROWSING_API_KEY` in the terminal before restarting (`unset GOOGLE_SAFE_BROWSING_API_KEY` on Linux/macOS; `Remove-Item Env:GOOGLE_SAFE_BROWSING_API_KEY` in PowerShell).

### Database location

By default, the local app creates `cyber_assistant.db` in the project directory. The database is ignored by Git and is not included when you clone the repository. In common serverless environments the code uses `/tmp/cyber_assistant.db`, which is temporary and not durable storage. The included local setup uses SQLite; production deployments need a durable storage design.

## Optional integrations

### Chrome extension

The extension source is in `extension/` and is configured to send URLs to `http://127.0.0.1:8000/api/scan/url`. Start the backend first, then in Chrome:

1. Open `chrome://extensions/`.
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select this repository's `extension/` folder.
4. Right-click a link and choose **Scan link for phishing** while the local backend is running.

This integration is intended for local development. The extension's API address is fixed to localhost; it will not reach a backend running on a different machine without changing the extension source. The popup's paste-and-scan controls are currently presentation-only, and the background script's notification display may require adding the browser's notifications permission to the extension manifest. Review the permissions and browser behavior before using or distributing it.

### Telegram bot

The bot is optional and its dependencies are not in `requirements.txt`. Install them in the activated virtual environment:

```bash
python -m pip install python-telegram-bot requests
```

Create a bot with Telegram's BotFather and configure its token for `bot/telegram_bot.py`. The current source uses a placeholder token and expects you to replace it in that file. **Do not commit a real token**: keep any personal token change local or move token handling to an environment variable before committing. Start the API in one terminal, then run the bot from the repository root in another:

```bash
python bot/telegram_bot.py
```

The bot expects the API at `http://127.0.0.1:8000/api`, so the bot process must be able to reach the backend at that address. Press **Ctrl+C** to stop it.

## Model training and datasets

Training is optional; the committed model artifacts are used by default. The training scripts are in `backend/ml/`:

- `url_analyzer.py` extracts URL features and loads `url_model.pkl`.
- `message_analyzer.py` loads `message_model.pkl`, `vectorizer.pkl`, and `message_threshold.json`.
- `train_models.py` trains a Random Forest URL classifier and a TF-IDF plus Logistic Regression message classifier. It prints validation metrics and replaces the saved artifacts.
- `fetch_real_datasets.py` downloads and normalizes the public training datasets.

To fetch the public datasets and train both classifiers, first activate the virtual environment and run these commands from the repository root:

```bash
python backend/ml/fetch_real_datasets.py
python backend/ml/train_models.py
```

Dataset fetching requires internet access and disk space. The preparation script reads the dataset files but does not visit URLs contained in the URL corpus. The trainer uses `real_url_dataset.csv` and `real_message_dataset.csv` if present; otherwise it uses the small sample CSVs. It writes the resulting model artifacts under `backend/ml/`. Dataset sources, label mappings, licenses, and preparation notes are documented in [backend/data/README.md](backend/data/README.md).

Validation results describe performance on the available datasets and do not predict accuracy on new or current attacks. Training datasets may be imbalanced or outdated.

## Database and privacy

The backend stores submitted content, classification, risk score, timestamp, and available result details in SQLite so the dashboard can show history. The default database file is `cyber_assistant.db` in the project root and is excluded from Git. If you need to retain scan history, back up this file while the application is stopped. Do not share the database without considering the submitted message contents it contains.

By default the development server binds to `127.0.0.1`, so it is accessible only from the same machine. The API currently has no user authentication, and its history deletion endpoints can delete records. Do not expose it to the public internet as-is. If Safe Browsing is enabled, URLs submitted for reputation checks are also sent to Google.

## Troubleshooting

- **`python` or `python3` is not found:** install Python 3.10 or newer and ensure it is on your PATH. On Windows, use `py -3` to create the environment.
- **Virtual environment creation fails:** install the OS package for Python `venv` (often `python3-venv` on Debian/Kali), then recreate `.venv`.
- **`ModuleNotFoundError` or missing dependency:** activate `.venv` and run `python -m pip install -r requirements.txt` again. Start Uvicorn with the same environment's Python.
- **PowerShell will not activate `.venv`:** use `.venv\Scripts\python.exe -m pip ...` and `.venv\Scripts\python.exe -m uvicorn ...` directly.
- **`Address already in use`:** stop the other server or choose another port, for example `--port 8001`, then use the matching browser URL.
- **The browser page does not connect to the API:** confirm the Uvicorn terminal still says the server is running and open the page from `http://127.0.0.1:<port>/`, not from a local file.
- **A scan uses fallback behavior or model loading warns:** confirm the model files exist in `backend/ml/`. Reinstall compatible requirements; if needed, run the training steps above.
- **Safe Browsing status is `not_configured`:** set `GOOGLE_SAFE_BROWSING_API_KEY` in the same terminal before starting the backend.
- **Safe Browsing status is `unavailable`:** check the key, network connection, and provider configuration. The local URL model still provides its result.
- **Old history lacks indicators or recommendation:** older records may not have stored full result details. New scans save the complete response.
- **A browser icon request returns 404 or the server logs `304 Not Modified`:** these are usually browser cache or conventional favicon requests and do not prevent scanning. Try a hard reload if the page looks stale.

## Project status and license

This repository contains local development code plus deployment-oriented `api/`, `public/`, and `vercel.json` files. The documented and supported path for running the complete web app is the local FastAPI/Uvicorn procedure above. The deployment files are not a substitute for configuring and securing a production service, including durable storage and access control.

There is currently no standalone `LICENSE` file in the repository, so do not assume the application code is MIT-licensed. Dataset attribution and source licenses are documented in [backend/data/README.md](backend/data/README.md).
