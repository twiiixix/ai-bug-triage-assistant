# AI Bug Triage Assistant

A Flask application with account registration and login, user-specific bug reports, AI-assisted triage, analytics, search, filtering, status updates, editing, and deleting.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open `(https://ai-bug-triage-assistant-7348.onrender.com/login)`, create an account, and sign in.

The app uses rule-based fallback analysis when an OpenAI API key is unavailable.
