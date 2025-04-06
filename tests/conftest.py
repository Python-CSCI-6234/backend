import pytest
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables"""
    os.environ["TESTING"] = "True"
    os.environ["GOOGLE_CLIENT_ID"] = os.getenv("TEST_GOOGLE_CLIENT_ID", "test_client_id")
    os.environ["GOOGLE_CLIENT_SECRET"] = os.getenv("TEST_GOOGLE_CLIENT_SECRET", "test_client_secret")
    os.environ["RESEND_API_KEY"] = os.getenv("TEST_RESEND_API_KEY", "test_resend_key")
    os.environ["SECRET_KEY"] = os.getenv("TEST_SECRET_KEY", "test_secret_key")
    return os.environ 