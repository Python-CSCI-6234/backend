# backend
Udit Chowdary 
# 📬 Email Automation Backend (Gist, Notifications, Daily Digest)

This FastAPI-based backend powers email summarization, notifications, and daily digest functionality as part of the AI-powered Email Automation system. It is responsible for:

- 🔹 Summarizing the first 50 emails on user login (`/gist`)
- 🔹 Sending real-time notifications for the latest 10 emails (`/send_notifications`)
- 🔹 Sending a daily summary digest of all emails via SMS (`/daily_digest`)
- 🔹 Running scheduled jobs using cron-like behavior

---

## 🧩 Prerequisites

- Python 3.8+
- A Resend account (for SMS/email notifications)
- Gmail API access (via FetchEmails)
- AI Summarization API (for SummarizeEmails)
- `.env` file with required environment variables

---

## 📦 Installation

```bash
# Clone and enter the repo
git clone <your-repo-url>
cd email_automation

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt

⚙️ Environment Setup
Create a .env file in the root directory:
FETCH_EMAILS_API=https://yourdomain.com/api/fetch_emails
SUMMARIZE_EMAILS_API=https://yourdomain.com/api/summarize_emails
RESEND_API_KEY=your_resend_api_key
USER_PHONE=+1234567890

🚀 Run the Server
Start the FastAPI backend server:
uvicorn main:app --reload

📡 API Endpoints
1. /gist
Fetches and summarizes the first 50 emails when the user logs in.
GET http://localhost:8000/gist

2. /send_notifications
Fetches the latest 10 emails, summarizes them, and sends an SMS notification using Resend.
GET http://localhost:8000/send_notifications

3. /daily_digest
Summarizes all emails received today and sends an SMS summary to the user.
GET http://localhost:8000/daily_digest
