import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.core.config import settings

def get_authenticated_service():
    creds = None

    if os.path.exists(settings.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(settings.TOKEN_FILE, settings.SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.CLIENT_SECRET_FILE, settings.SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open(settings.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service


def get_user_email():
    service = get_authenticated_service()
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
        body = part.get("body", {})
        mime_type = part.get("mimeType")
        attachment_id = body.get("attachmentId")

        if filename and attachment_id:
            content = fetch_attachment(service, msg_id, attachment_id)
            attachments.append({
                "filename": filename,
                "mimeType": mime_type,
                "size": body.get("size"),
                "attachmentId": attachment_id,
                "content": base64.b64encode(content).decode("utf-8") if content else None
            })
    return attachments

def fetch_and_save_emails(limit=5, output_file="emails.json"):
    service = get_authenticated_service()

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