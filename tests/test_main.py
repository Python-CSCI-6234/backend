import pytest
from fastapi.testclient import TestClient
from main import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Email Organizer API"}

def test_google_auth_url():
    response = client.get("/auth/google")
    assert response.status_code == 200
    assert "url" in response.json()

@pytest.mark.asyncio
async def test_fetch_emails():
    # This test requires a valid Google OAuth token
    # You'll need to replace this with a valid token
    test_token = "your_test_token"
    response = client.get(
        "/api/emails/fetch",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code in [200, 401]  # 401 if token is invalid

def test_summarize_emails():
    test_emails = [
        {
            "id": "1",
            "from": "test@example.com",
            "subject": "Test Work Email",
            "date": "2024-01-01",
            "snippet": "This is a test work email"
        },
        {
            "id": "2",
            "from": "newsletter@example.com",
            "subject": "Weekly Newsletter",
            "date": "2024-01-01",
            "snippet": "This is a test newsletter"
        }
    ]
    response = client.post("/api/emails/summarize", json=test_emails)
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "summary_text" in data

def test_send_notification():
    test_data = {
        "phone_number": "test@example.com",
        "emails": [
            {
                "id": "1",
                "from": "test@example.com",
                "subject": "Test Email",
                "date": "2024-01-01",
                "snippet": "This is a test email"
            }
        ]
    }
    response = client.post("/api/notifications", json=test_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Notification sent successfully"

@pytest.mark.asyncio
async def test_daily_digest():
    # This test requires a valid Google OAuth token
    test_token = "your_test_token"
    response = client.get(
        "/api/digest",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code in [200, 401]  # 401 if token is invalid 