# Email Organizer Backend

A FastAPI-based backend service for organizing and summarizing emails using Google OAuth and AI processing.

## Features

- Google OAuth integration for email access
- Email fetching and processing
- AI-powered email summarization
- Daily digest notifications via Resend
- Cron job scheduling for automated tasks

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
RESEND_API_KEY=your_resend_api_key
```

4. Run the application:
```bash
uvicorn main:app --reload
```

## API Endpoints

- `/auth/google`: Google OAuth authentication
- `/api/emails/fetch`: Fetch emails from Gmail
- `/api/emails/summarize`: Summarize emails using AI
- `/api/notifications`: Send notifications via Resend
- `/api/digest`: Generate and send daily digest

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── auth/                # Authentication related code
├── services/            # Business logic services
│   ├── email.py        # Email processing service
│   ├── ai.py           # AI summarization service
│   └── notification.py # Notification service
├── models/              # Pydantic models
└── utils/              # Utility functions
```