# AI Cybersecurity Assistant (Phishing Detection)

An intelligent cybersecurity assistant designed to detect phishing links and suspicious messages in real-time. This project features a FastAPI backend, machine learning models for URL and NLP message analysis, a web-based Chatbot interface, an Admin Dashboard, a Chrome Browser Extension, and a Telegram Bot integration.

## Project Structure
```text
cyber_security_project/
├── backend/
│   ├── ml/
│   │   ├── dataset_generator.py # Generates fake datasets for training
│   │   ├── train_models.py      # Trains ML models and outputs .pkl files
│   │   ├── url_analyzer.py      # Predicts URL risks using Random Forest
│   │   └── message_analyzer.py  # Predicts NLP risks using Logistic Regression
│   ├── database.py              # SQLite Database setup
│   ├── main.py                  # Core FastAPI application
│   └── models.py                # Request/Response schemas
├── frontend/
│   ├── index.html               # Chatbot UI
│   ├── admin.html               # Admin Dashboard UI
│   ├── script.js                # Frontend logic calling the API
│   └── style.css                # Styles
├── extension/
│   ├── manifest.json            # Chrome Manifest V3
│   ├── popup.html               # Extension UI
│   ├── popup.js                 # Extension frontend logic
│   ├── background.js            # Background worker for Right-Click context menus
│   └── icon.png                 # Extension Icon
├── bot/
│   └── telegram_bot.py          # Telegram bot script
├── data/                        # Datasets (created during execution)
└── requirements.txt             # Python dependencies
```

## Setup Instructions

### 1. Python Environment Setup
Install dependencies in a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Train the Machine Learning Models
Before running the backend, you must train the models based on the mock datasets:
```bash
cd backend/ml
python train_models.py
cd ../..
```

### 3. Run the Backend Server
Start the FastAPI server:
```bash
uvicorn backend.main:app --reload
```
The API running at `http://127.0.0.1:8000`

### 4. Open the Web Applications
Simply open `frontend/index.html` or `frontend/admin.html` in your web browser. It talks directly to the backend API.

### 5. Install the Chrome Extension
1. Open Google Chrome.
2. Go to `chrome://extensions/`
3. Enable "Developer mode" in the top right.
4. Click "Load unpacked" and select the `extension` folder in this project.
5. You can now use the extension popup or right-click any link on a webpage to "Scan link for phishing".

### 6. Run the Telegram Bot (Optional)
If you want to use the Telegram bot:
1. Message `@BotFather` on Telegram and create a new bot to get a Token.
2. Open `bot/telegram_bot.py` and replace `YOUR_TELEGRAM_BOT_TOKEN_HERE` with your token.
3. Run the bot:
```bash
python bot/telegram_bot.py
```

## Features
- **URL Phishing Detection**: Analyzes length, dots, unusual characters (`@`, `-`), IP masking, HTTPS usage, and suspicious keywords.
- **Message Phishing Detection**: Uses `spaCy` and TF-IDF to detect urgency cues and financial baits in texts.
- **Admin Dashboard**: Live metrics on the success rate of the detection models and historical scan data.
- **Cross-Platform**: Integrates perfectly via REST API to the Web App, Browser Extension, and Chatbot.

## License
MIT License
