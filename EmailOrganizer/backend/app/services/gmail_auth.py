import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.core.config import settings
from fastapi import Request as FastAPIRequest

# Global variable to store the authenticated service and credentials
_authenticated_service = None
_credentials = None

def clear_existing_tokens(request: FastAPIRequest):
    """Delete existing token file and clear session"""
    if os.path.exists(settings.TOKEN_FILE):
        os.remove(settings.TOKEN_FILE)
    request.session.clear()

def validate_project(creds):
    """Validate if the project has the correct name and permissions"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        # Get project information
        project_info = service.users().getProfile(userId='me').execute()
        # Get the email address
        email = project_info.get('emailAddress', '')
        # Check if the email is valid (not empty)
        if not email:
            raise ValueError("Could not retrieve email address")
        return True
    except Exception as e:
        raise ValueError(f"Project validation failed: {str(e)}")

def get_authenticated_service(request: FastAPIRequest, force_new_auth=False):
    """Get authenticated service using session storage"""
    try:
        # If forcing new auth, clear session
        if force_new_auth:
            clear_existing_tokens(request)
            
        # Check if we have credentials in the session
        if not force_new_auth and "credentials" in request.session:
            creds_dict = json.loads(request.session["credentials"])
            creds = Credentials.from_authorized_user_info(creds_dict, settings.SCOPES)
            validate_project(creds)
            return build('gmail', 'v1', credentials=creds)
            
        # Check if we have valid tokens and not forcing new auth
        if os.path.exists(settings.TOKEN_FILE) and not force_new_auth:
            creds = Credentials.from_authorized_user_file(settings.TOKEN_FILE, settings.SCOPES)
            validate_project(creds)
            # Store credentials in session
            request.session["credentials"] = creds.to_json()
            return build('gmail', 'v1', credentials=creds)
            
        # Start new authentication flow
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.CLIENT_SECRET_FILE, settings.SCOPES
        )
        creds = flow.run_local_server(port=0)
        
        # Validate project
        validate_project(creds)
        
        # Save new token
        with open(settings.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
        # Store credentials in session
        request.session["credentials"] = creds.to_json()
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")

def get_user_email(request: FastAPIRequest):
    """Get the authenticated user's email"""
    # Only force new auth if we don't have credentials in session
    force_new_auth = "credentials" not in request.session
    service = get_authenticated_service(request, force_new_auth=force_new_auth)
    profile = service.users().getProfile(userId='me').execute()
    return profile.get('emailAddress')

def get_email_body(payload):
    parts = payload.get("parts")
    if parts:
        for part in parts:
            mime_type = part.get("mimeType")
            body = part.get("body", {}).get("data")
            if body:
                decoded_body = base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")
                if mime_type == "text/plain":
                    return decoded_body.strip()
                elif mime_type == "text/html":
                    return decoded_body.strip()
    else:
        body = payload.get("body", {}).get("data")
        if body:
            return base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")
    return None

def fetch_attachment(service, msg_id, attachment_id):
    attachment = service.users().messages().attachments().get(
        userId="me", messageId=msg_id, id=attachment_id
    ).execute()
    data = attachment.get("data")
    return base64.urlsafe_b64decode(data.encode("UTF-8")) if data else None

def extract_attachments(service, msg_id, payload):
    attachments = []
    parts = payload.get("parts", [])
    for part in parts:
        filename = part.get("filename")
        mime_type = part.get("mimeType")
        attachment_id = part.get("body", {}).get("attachmentId")

        if filename and attachment_id:
            attachments.append({
                "filename": filename,
                "mimeType": mime_type
            })
    return attachments

def fetch_and_save_emails(request: FastAPIRequest, limit=50, output_file="emails.json"):
    """Fetch and save emails using the session-based authenticated service"""
    # Only force new auth if we don't have credentials in session
    force_new_auth = "credentials" not in request.session
    service = get_authenticated_service(request, force_new_auth=force_new_auth)

    results = service.users().messages().list(userId='me', maxResults=limit).execute()
    messages = results.get('messages', [])

    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), None)
        sender = next((h['value'] for h in headers if h['name'] == 'From'), None)
        date = next((h['value'] for h in headers if h['name'] == 'Date'), None)

        body = get_email_body(payload)
        attachments = extract_attachments(service, msg['id'], payload)

        email_json = {
            "id": msg['id'],
            "subject": subject,
            "from": sender,
            "date": date,
            "body": body,
            "attachments": attachments
        }

        emails.append(email_json)

    with open(output_file, "w") as f:
        json.dump(emails, f, indent=4)

    return emails