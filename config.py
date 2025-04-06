import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Settings:
    # Google OAuth settings
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    
    # Resend settings
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    
    # Email processing settings
    BATCH_SIZE = 50  # Number of emails to process in one batch
    MAX_EMAILS_PER_SUMMARY = 10  # Maximum number of emails to include in notifications
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # API settings
    API_V1_STR = "/api/v1"
    PROJECT_NAME = "Email Organizer API"

    def __init__(self):
        # Log the loaded settings (without sensitive data)
        logger.debug(f"GOOGLE_REDIRECT_URI: {self.GOOGLE_REDIRECT_URI}")
        logger.debug(f"BATCH_SIZE: {self.BATCH_SIZE}")
        logger.debug(f"MAX_EMAILS_PER_SUMMARY: {self.MAX_EMAILS_PER_SUMMARY}")
        logger.debug(f"API_V1_STR: {self.API_V1_STR}")
        logger.debug(f"PROJECT_NAME: {self.PROJECT_NAME}")

settings = Settings() 