from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import List, Dict
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from auth.google_auth import google_auth
from services.email import EmailService
from services.ai import AIService, ai_service
from services.notification import NotificationService, notification_service
from config import settings
import logging
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from fastapi import HTTPException
from services.email_service import EmailService
from services.user_service import user_service
from datetime import datetime, timezone
import pytz
from models.user import UserCredentials

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Debug environment variables
logger.debug(f"GOOGLE_CLIENT_ID: {os.getenv('GOOGLE_CLIENT_ID')}")
logger.debug(f"GOOGLE_CLIENT_SECRET: {os.getenv('GOOGLE_CLIENT_SECRET')}")
logger.debug(f"GOOGLE_REDIRECT_URI: {os.getenv('GOOGLE_REDIRECT_URI')}")

app = FastAPI(title="Email Organizer API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

# Initialize scheduler
scheduler = BackgroundScheduler()

async def get_current_user(credentials: str = Depends(oauth2_scheme)):
    """Get current user from credentials"""
    return credentials 

@app.get("/auth/google")
async def google_auth_url():
    """Get Google OAuth URL and redirect to it"""
    try:
        auth_url = google_auth.get_auth_url()
        logger.debug(f"Generated auth URL: {auth_url}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/google/callback")
async def google_auth_callback(code: str):
    """Handle Google OAuth callback"""
    try:
        logger.debug(f"Received auth code: {code}")
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code is required")
            
        # Exchange code for credentials
        try:
            credentials = await google_auth.get_credentials(code)
            logger.debug("Successfully obtained credentials")
        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to get credentials: {str(e)}")
            
        # Get user info
        try:
            user_info = google_auth.get_user_info(credentials)
            logger.debug(f"Successfully obtained user info: {user_info}")
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to get user info: {str(e)}")
            
        if not user_info:
            raise HTTPException(status_code=400, detail="No user info returned")
            
        logger.debug(f"Successfully authenticated user: {user_info.get('email')}")
        
        # Store user credentials
        user_creds = UserCredentials(
            user_id=user_info["sub"],
            email=user_info["email"],
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=credentials.expiry,
        )
        await user_service.store_user_credentials(user_creds)
        
        return {
            "user_info": user_info,
            "credentials": credentials.to_json()
        }
    except HTTPException as he:
        logger.error(f"HTTP Exception in auth callback: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in auth callback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during authentication: {str(e)}"
        )

@app.get("/api/emails/fetch")
async def fetch_emails(token: str):
    """Fetch emails from Gmail"""
    try:
        logger.debug("Starting fetch_emails endpoint")
        
        # Create credentials with required fields
        creds = Credentials(
            token=token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        logger.debug("Successfully created credentials")
        
        # Create email service instance
        email_service = EmailService()
        emails = await email_service.fetch_emails(creds)
        logger.debug(f"Successfully fetched {len(emails)} emails")
        return {"emails": emails}
    except Exception as e:
        logger.error(f"Error in fetch_emails endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch emails: {str(e)}"
        )

@app.post("/api/emails/summarize")
async def summarize_emails(emails: List[Dict]):
    """Summarize a batch of emails"""
    try:
        summary = ai_service.summarize_emails(emails)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/notifications")
async def send_notification(token: str, email_address: str, email_data: Dict):
    """Send notification about new emails"""
    try:
        # Extract the emails list from email_data
        emails = email_data.get("emails", [])
        if not isinstance(emails, list):
            raise HTTPException(status_code=400, detail="emails must be a list")
            
        summary = ai_service.generate_notification_summary(emails)
        
        # Send notification using Resend
        response = await notification_service.send_email_notification(
            to=email_address,
            subject="📧 New Email Summary",
            content=f"""
            <html>
                <body>
                    <h2>📧 New Email Summary</h2>
                    <div style="white-space: pre-line;">
                        {summary}
                    </div>
                    <p>Powered by Email Organizer</p>
                </body>
            </html>
            """
        )
        
        return {"message": "Notification sent successfully", "resend_response": response}
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/digest")
async def generate_daily_digest(token: str):
    """Generate and send daily digest"""
    try:
        # Create credentials with required fields
        creds = Credentials(
            token=token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        email_service = EmailService()
        emails = await email_service.fetch_emails(creds)
        digest_content = ai_service.generate_daily_digest(emails)
        return {"digest": digest_content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Schedule daily digest
@scheduler.scheduled_job('cron', hour=0, minute=0)
async def scheduled_daily_digest():
    """Scheduled task to generate and send daily digest"""
    try:
        # Get all users who have enabled daily digest
        users = await user_service.get_all_users_for_digest()
        
        for user in users:
            # Check if it's the right time for this user's timezone
            user_tz = pytz.timezone(user.preferences.get("timezone", "UTC"))
            user_time = datetime.now(user_tz)
            digest_time = datetime.strptime(
                user.preferences.get("digest_time", "00:00"),
                "%H:%M"
            ).time()
            
            if user_time.time().hour == digest_time.hour and \
               user_time.time().minute == digest_time.minute:
                try:
                    # Create services
                    email_service = EmailService()
                    ai_service = AIService()
                    notification_service = NotificationService()
                    
                    # Fetch emails from the last 24 hours
                    emails = await email_service.fetch_emails(
                        user.access_token,
                        time_range="1d"
                    )
                    
                    # Generate digest
                    digest_content = ai_service.generate_daily_digest(emails)
                    
                    # Send notification
                    await notification_service.send_daily_digest(
                        to=user.email,
                        digest_content=digest_content
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing digest for user {user.email}: {str(e)}")
                    continue
    
    except Exception as e:
        logger.error(f"Error in scheduled daily digest: {str(e)}")

# Add new endpoint to update user preferences
@app.post("/api/preferences")
async def update_preferences(
    preferences: dict,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_creds = await user_service.get_user_credentials(current_user["sub"])
        if not user_creds:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_creds.preferences.update(preferences)
        await user_service.store_user_credentials(user_creds)
        return {"status": "success", "preferences": user_creds.preferences}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Start scheduler when application starts
@app.on_event("startup")
async def startup_event():
    scheduler.start()

# Stop scheduler when application shuts down
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()