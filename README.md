# mailbot Backend

A FastAPI-based backend service for organizing and summarizing emails using Google OAuth and AI processing.

## Features

- Google OAuth integration for secure email access
- Email fetching and processing from Gmail
- AI-powered email summarization and analysis
- Daily digest notifications via Resend
- User management and authentication
- Automated task scheduling
- Comprehensive test suite

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

5. Run tests:
```bash
./run_tests.sh
```

## API Endpoints

- `/auth/google`: Google OAuth authentication flow
- `/api/emails/fetch`: Fetch and process emails from Gmail
- `/api/emails/summarize`: Generate AI-powered email summaries
- `/api/notifications`: Handle email notifications via Resend
- `/api/digest`: Generate and send personalized daily digests
- `/api/users`: User management endpoints

## Project Structure

```
backend/
├── main.py # FastAPI application entry point
├── config.py # Configuration and environment settings
├── requirements.txt # Python dependencies
├── Procfile # Deployment configuration
├── runtime.txt # Python runtime specification
├── auth/ # Authentication related code
├── services/ # Business logic services
│ ├── ai.py # AI processing and summarization
│ ├── email.py # Core email processing
│ ├── email_service.py # Email service integration
│ ├── notification.py # Notification handling
│ └── user_service.py # User management
├── models/ # Data models
│ └── user.py # User data structures
├── tests/ # Test suite
├── credentials/ # Secure credential storage
└── .env # Environment variables
```

## Development

- The project uses Python 3.x
- FastAPI for the web framework
- Google OAuth2 for authentication
- AI services for email processing
- Resend for email notifications
- Pytest for testing

## Testing

Run the test suite using the provided script:
```bash
./run_tests.sh
```

The test suite includes unit tests and integration tests for all major components.