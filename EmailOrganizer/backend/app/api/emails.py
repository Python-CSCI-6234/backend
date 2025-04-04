from fastapi import APIRouter, HTTPException
from app.services.gmail_service import GmailService
from typing import Dict, Union

router = APIRouter()
gmail_service = GmailService()

@router.get("/emails")
async def get_emails():
    try:
        emails = gmail_service.fetch_emails()
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-user-email", response_model=Dict[str, str])
async def get_user_email():
    """
    Authenticate user and get their email.
    This endpoint:
    1. Cleans up existing session files
    2. Checks for existing project or creates new one
    3. Sets up necessary permissions
    4. Gets user consent
    5. Returns user's email
    """
    try:
        email = await gmail_service.authenticate()
        return {"email": email}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/fetch-emails")
async def fetch_emails() -> Dict[str, list]:
    """
    Endpoint to fetch latest 50 emails.
    Uses existing authentication from get-user-email.
    """
    try:
        return gmail_service.fetch_emails(limit=50)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 