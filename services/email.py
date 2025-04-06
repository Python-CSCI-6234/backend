from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText
import json
from typing import List, Dict
from config import settings

class EmailService:
    def __init__(self, credentials: Credentials):
        self.service = build('gmail', 'v1', credentials=credentials)

    def fetch_emails(self, max_results: int = 50) -> List[Dict]:
        """
        Fetch emails from Gmail inbox
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg['payload']['headers']
                email_data = {
                    'id': message['id'],
                    'from': next((h['value'] for h in headers if h['name'] == 'From'), ''),
                    'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), ''),
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                    'snippet': msg.get('snippet', '')
                }
                emails.append(email_data)
            
            return emails
        except Exception as e:
            raise Exception(f"Error fetching emails: {str(e)}")

    def get_email_content(self, message_id: str) -> str:
        """
        Get the full content of a specific email
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            if 'payload' in message:
                parts = message['payload'].get('parts', [])
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            return ''
        except Exception as e:
            raise Exception(f"Error getting email content: {str(e)}")

    def fetch_recent_emails(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch recent emails for notifications
        """
        return self.fetch_emails(max_results=max_results)

    def fetch_daily_emails(self) -> List[Dict]:
        """
        Fetch emails from the last 24 hours
        """
        # TODO: Implement date filtering
        return self.fetch_emails(max_results=100) 