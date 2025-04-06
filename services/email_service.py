import base64
from googleapiclient.discovery import build
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
import logging
from config import settings
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        pass

    async def fetch_emails(self, credentials: Credentials):
        """Fetch emails from Gmail"""
        try:
            logger.debug("Starting to fetch emails")
            logger.debug("Using credentials for Gmail API access")
            
            # Build the Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            logger.debug("Successfully built Gmail service")
            
            # Get the list of messages
            results = service.users().messages().list(userId='me').execute()
            messages = results.get('messages', [])
            logger.debug(f"Found {len(messages)} messages")
            
            if not messages:
                return []
                
            # Fetch full message details
            emails = []
            for message in messages[:settings.MAX_EMAILS]:  # Limit to 10 emails for testing
                try:
                    msg = service.users().messages().get(userId='me', id=message['id']).execute()
                    
                    # Extract email data
                    headers = msg['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    # Get message body
                    body = ''
                    if 'parts' in msg['payload']:
                        for part in msg['payload']['parts']:
                            if part['mimeType'] == 'text/plain':
                                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                                break
                    elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                        body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
                    
                    emails.append({
                        'id': message['id'],
                        'subject': subject,
                        'from': from_email,
                        'date': date,
                        'body': body
                    })
                except Exception as e:
                    logger.error(f"Error processing message {message['id']}: {str(e)}")
                    continue
                    
            logger.debug(f"Successfully processed {len(emails)} emails")
            return emails
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch emails: {str(e)}"
            ) from e