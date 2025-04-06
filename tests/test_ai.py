from services.ai import ai_service
import json
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sample test emails
test_emails = [
    {
        "id": "1",
        "subject": "Important: Project Deadline Extension",
        "from": "manager@company.com",
        "date": (datetime.now() - timedelta(hours=2)).isoformat(),
        "body": "Hello team, I wanted to inform you that the project deadline has been extended by one week. Please adjust your schedules accordingly. The new deadline is next Friday. Let me know if you have any questions."
    },
    {
        "id": "2",
        "subject": "Weekly Newsletter: Tech Updates",
        "from": "newsletter@tech.com",
        "date": (datetime.now() - timedelta(hours=5)).isoformat(),
        "body": "Here are this week's top tech stories: 1. New AI developments 2. Latest software releases 3. Industry trends. Click here to read more!"
    },
    {
        "id": "3",
        "subject": "Dinner plans with family",
        "from": "mom@family.com",
        "date": (datetime.now() - timedelta(hours=8)).isoformat(),
        "body": "Hi dear, just checking if you're free for dinner this weekend. Grandma is coming to town and would love to see you. Let me know your availability."
    }
]

def test_summarize_emails():
    print("\n=== Testing Email Summarization ===")
    try:
        # Test direct service call
        result = ai_service.summarize_emails(test_emails)
        print("\nDirect Service Result:")
        print(json.dumps(result, indent=2))

        # Test API endpoint
        response = requests.post(
            "http://localhost:8000/api/emails/summarize",
            json=test_emails
        )
        print("\nAPI Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def test_notification_summary():
    print("\n=== Testing Notification Summary ===")
    try:
        # Test direct service call
        summary = ai_service.generate_notification_summary(test_emails)
        print("\nDirect Service Notification Summary:")
        print(summary)

        # Test API endpoint
        response = requests.post(
            "http://localhost:8000/api/notifications",
            params={
                "token": "test_token",
                "email_address": "test@example.com"
            },
            json={"emails": test_emails}
        )
        print("\nAPI Notification Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def test_daily_digest():
    print("\n=== Testing Daily Digest ===")
    try:
        # Test direct service call
        digest = ai_service.generate_daily_digest(test_emails)
        print("\nDirect Service Daily Digest:")
        print(digest)

        # Test API endpoint
        response = requests.get(
            "http://localhost:8000/api/digest",
            params={"token": "test_token"}
        )
        print("\nAPI Digest Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def test_email_fetch():
    print("\n=== Testing Email Fetch ===")
    try:
        # Test API endpoint
        response = requests.get(
            "http://localhost:8000/api/emails/fetch",
            params={"token": "test_token"}
        )
        print("\nAPI Fetch Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def test_auth_flow():
    print("\n=== Testing Auth Flow ===")
    try:
        # Test Google auth URL
        response = requests.get("http://localhost:8000/auth/google")
        print("\nAuth URL Response:")
        print(response.url)

        # Test auth callback (this will fail without a real code)
        response = requests.get(
            "http://localhost:8000/auth/google/callback",
            params={"code": "test_code"}
        )
        print("\nAuth Callback Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def run_all_tests():
    print("Starting AI Service Tests...")
    
    # Test direct service calls
    test_summarize_emails()
    test_notification_summary()
    test_daily_digest()
    
    # Test API endpoints
    test_email_fetch()
    test_auth_flow()
    
    print("\nTests completed!")

if __name__ == "__main__":
    run_all_tests() 