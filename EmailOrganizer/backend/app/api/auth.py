from fastapi import APIRouter, HTTPException
from app.services.gmail_auth import get_user_email
from app.services.gmail_auth import fetch_and_save_emails

router = APIRouter()

@router.get("/get-user-email")
def fetch_user_email():
    try:
        email = get_user_email()
        return {"email": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/fetch-emails")
def get_emails():
    emails = fetch_and_save_emails()
    return {"message": "Emails fetched and saved to emails.json", "emails": emails}
