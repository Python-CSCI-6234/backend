from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import List, Dict
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from auth.google_auth import google_auth
from services.email import EmailService
from services.ai import ai_service
from services.notification import notification_service
from config import settings

# Load environment variables
load_dotenv()

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

@app.get("/auth/google")
async def google_auth_url():
    """Get Google OAuth URL"""
    return {"url": google_auth.get_auth_url()}

@app.get("/auth/google/callback")
async def google_auth_callback(code: str):
    """Handle Google OAuth callback"""
    try:
        credentials = await google_auth.get_credentials(code)
        user_info = google_auth.get_user_info(credentials)
        return {"user_info": user_info, "credentials": credentials.to_json()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/emails/fetch")
async def fetch_emails(credentials: str = Depends(oauth2_scheme)):
    """Fetch emails from Gmail"""
    try:
        creds = google_auth.get_credentials(credentials)
        email_service = EmailService(creds)
        emails = email_service.fetch_emails(max_results=settings.BATCH_SIZE)
        return {"emails": emails}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/emails/summarize")
async def summarize_emails(emails: List[Dict]):
    """Summarize a batch of emails"""
    try:
        summary = ai_service.summarize_emails(emails)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/notifications")
async def send_notification(request: Request):
    """Send notification about new emails"""
    try:
        data = await request.json()
        phone_number = data.get("phone_number")
        emails = data.get("emails", [])
        
        if not phone_number or not emails:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        summary = ai_service.generate_notification_summary(emails)
        await notification_service.send_email_notification(
            to=phone_number,
            subject="📧 New Email Summary",
            content=summary
        )
        return {"message": "Notification sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/digest")
async def generate_daily_digest(credentials: str = Depends(oauth2_scheme)):
    """Generate and send daily digest"""
    try:
        creds = google_auth.get_credentials(credentials)
        email_service = EmailService(creds)
        user_info = google_auth.get_user_info(creds)
        
        emails = email_service.fetch_daily_emails()
        digest_content = ai_service.generate_daily_digest(emails)
        
        await notification_service.send_daily_digest(
            to=user_info["email"],
            digest_content=digest_content
        )
        return {"message": "Daily digest sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Schedule daily digest
@scheduler.scheduled_job('cron', hour=0, minute=0)
async def scheduled_daily_digest():
    """Scheduled task to generate and send daily digest"""
    # TODO: Implement scheduled daily digest logic
    # This would require storing user credentials securely
    pass

# Start scheduler when application starts
@app.on_event("startup")
async def startup_event():
    scheduler.start()

# Stop scheduler when application shuts down
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown() 