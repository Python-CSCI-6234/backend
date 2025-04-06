import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

def test_google_auth_flow():
    """Test the complete Google OAuth flow"""
    print("\nTesting OAuth flow...")
    
    # Step 1: Get authorization URL
    response = requests.get(f"{BASE_URL}/auth/google", allow_redirects=False)
    assert response.status_code == 307, f"Expected 307, got {response.status_code}"
    
    auth_url = response.headers['location']
    print(f"\nPlease visit this URL to authorize: {auth_url}")
    print("\nAfter authorizing, you will be redirected to a URL.")
    print("Please copy the ENTIRE URL from your browser's address bar and paste it here.")
    print("Make sure to copy the URL immediately after being redirected, as the authorization code expires quickly.")
    
    # Step 2: Get the full redirect URL from user
    redirect_url = input("Enter the complete redirect URL: ").strip()
    if not redirect_url:
        raise ValueError("No redirect URL provided")
        
    # Parse the code from the URL
    parsed_url = urlparse(redirect_url)
    query_params = parse_qs(parsed_url.query)
    
    if 'code' not in query_params:
        print(f"Query parameters found: {query_params}")
        raise ValueError("No authorization code found in redirect URL")
        
    code = query_params['code'][0]
    print(f"\nFound authorization code: {code}")
    print("Exchanging code for token...")
    
    # Step 3: Exchange code for token
    try:
        response = requests.get(
            f"{BASE_URL}/auth/google/callback",
            params={"code": code}
        )
        
        print(f"Callback response status: {response.status_code}")
        print(f"Callback response headers: {response.headers}")
        print(f"Callback response body: {response.text}")
        
        if response.status_code != 200:
            raise ValueError(f"Callback failed with status {response.status_code}: {response.text}")
            
        data = response.json()
        assert "user_info" in data, "Response missing user_info"
        assert "credentials" in data, "Response missing credentials"
        
        print("Successfully authenticated!")
        return data["credentials"]
    except Exception as e:
        print(f"Error during token exchange: {str(e)}")
        raise

def test_fetch_emails(credentials):
    """Test email fetching"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/emails/fetch",
            headers={"Authorization": f"Bearer {credentials}"}
        )
        print(f"Fetch emails response status: {response.status_code}")
        print(f"Fetch emails response: {response.text}")
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch emails: {response.text}")
            
        data = response.json()
        if "emails" not in data:
            raise ValueError("No emails in response")
            
        return data["emails"]
    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        raise

def test_summarize_emails(emails):
    """Test email summarization"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/emails/summarize",
            json=emails[:2]  # Test with first two emails
        )
        print(f"Summarize response status: {response.status_code}")
        print(f"Summarize response: {response.text}")
        
        if response.status_code != 200:
            raise ValueError(f"Failed to summarize emails: {response.text}")
            
        data = response.json()
        if "categories" not in data or "summary_text" not in data:
            raise ValueError("Missing required data in summary response")
            
        return data
    except Exception as e:
        print(f"Error summarizing emails: {str(e)}")
        raise

def test_notifications(summary):
    """Test notification sending"""
    try:
        test_data = {
            "phone_number": os.getenv("TEST_EMAIL", "test@example.com"),
            "emails": summary["categories"]["work"][:1]  # Test with first work email
        }
        response = requests.post(
            f"{BASE_URL}/api/notifications",
            json=test_data
        )
        print(f"Notification response status: {response.status_code}")
        print(f"Notification response: {response.text}")
        
        if response.status_code != 200:
            raise ValueError(f"Failed to send notification: {response.text}")
            
        data = response.json()
        if data.get("message") != "Notification sent successfully":
            raise ValueError("Unexpected notification response")
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        raise

def test_daily_digest(credentials):
    """Test daily digest generation"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/digest",
            headers={"Authorization": f"Bearer {credentials}"}
        )
        print(f"Daily digest response status: {response.status_code}")
        print(f"Daily digest response: {response.text}")
        
        if response.status_code != 200:
            raise ValueError(f"Failed to generate daily digest: {response.text}")
            
        data = response.json()
        if data.get("message") != "Daily digest sent successfully":
            raise ValueError("Unexpected daily digest response")
    except Exception as e:
        print(f"Error generating daily digest: {str(e)}")
        raise

def test_complete_flow():
    """Test the complete flow"""
    try:
        # Get credentials through OAuth
        print("\nTesting OAuth flow...")
        credentials = test_google_auth_flow()
        
        # Fetch emails
        print("\nTesting email fetching...")
        emails = test_fetch_emails(credentials)
        
        # Summarize emails
        print("\nTesting email summarization...")
        summary = test_summarize_emails(emails)
        
        # Send notifications
        print("\nTesting notifications...")
        test_notifications(summary)
        
        # Generate daily digest
        print("\nTesting daily digest...")
        test_daily_digest(credentials)
        
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_complete_flow() 