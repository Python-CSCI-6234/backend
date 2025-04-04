from fastapi import APIRouter, HTTPException, Request
from app.services.gmail_auth import get_user_email, fetch_and_save_emails, clear_existing_tokens

router = APIRouter()

@router.get("/clear-session")
def clear_session(request: Request):
    """Clear the current session and force new authentication"""
    try:
        clear_existing_tokens(request)
        return {
            "status": "success",
            "message": "Session cleared successfully. Next authentication will require new login."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "error": "Failed to clear session"
            }
        )

@router.get("/get-user-email")
def fetch_user_email(request: Request):
    try:
        email = get_user_email(request)
        return {
            "status": "success",
            "message": "Successfully authenticated with Gmail",
            "email": email
        }
    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "message": str(e),
                "error": "Project validation failed"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "error": "Authentication failed"
            }
        )
    
@router.get("/fetch-emails")
def get_emails(request: Request):
    try:
        # First get the user email to ensure authentication
        email = get_user_email(request)
        # Then fetch the emails
        emails = fetch_and_save_emails(request)
        return {
            "status": "success",
            "message": f"Emails fetched and saved successfully for {email}",
            "emails": emails
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "error": "Failed to fetch emails"
            }
        )
