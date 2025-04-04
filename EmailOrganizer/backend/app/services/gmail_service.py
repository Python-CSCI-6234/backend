import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.cloud import resourcemanager_v3
from google.api_core import exceptions
from google.cloud import service_usage_v1
from google.cloud import api_keys_v2
import base64
from fastapi import HTTPException
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from .google_cloud_service import GoogleCloudService

class GmailService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.project_id = "emailorganizer"
        self.credentials = None
        self.service = None
        # Use paths relative to backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.credentials_file = os.path.join(backend_dir, "credentials.json")
        self.token_file = os.path.join(backend_dir, "token.json")
        self.cloud_service = GoogleCloudService()
        print(f"Initialized GmailService with credentials_file: {self.credentials_file}")
        print(f"Initialized GmailService with token_file: {self.token_file}")

    def _cleanup_session_files(self):
        """Delete contents of credentials and token files at session start"""
        try:
            print(f"Checking if {self.credentials_file} exists")
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                print(f"Removed {self.credentials_file}")
            else:
                print(f"{self.credentials_file} does not exist")
            
            print(f"Checking if {self.token_file} exists")
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                print(f"Removed {self.token_file}")
            else:
                print(f"{self.token_file} does not exist")
                
            print("Session files cleaned up successfully")
        except Exception as e:
            print(f"Error during session cleanup: {str(e)}")

    def _check_gmail_permissions(self, credentials):
        """Check if the selected email has necessary Gmail permissions"""
        try:
            service = build('gmail', 'v1', credentials=credentials)
            # Try to list one email to check permissions
            service.users().messages().list(userId='me', maxResults=1).execute()
            return True
        except Exception:
            return False

    def _setup_project_and_credentials(self):
        """Setup new Google Cloud project and credentials for email without permissions"""
        try:
            # 1. Create new project
            client = resourcemanager_v3.ProjectsClient()
            try:
                project = client.get_project(name=f"projects/{self.project_id}")
            except exceptions.NotFound:
                project = client.create_project(
                    request={
                        "project": {
                            "project_id": self.project_id,
                            "display_name": "Email Organizer"
                        }
                    }
                )

            # 2. Enable Gmail API
            service_client = service_usage_v1.ServiceUsageClient()
            service_name = f"projects/{self.project_id}/services/gmail.googleapis.com"
            
            try:
                request = service_usage_v1.EnableServiceRequest(name=service_name)
                operation = service_client.enable_service(request=request)
                operation.result()
            except Exception as e:
                print(f"Error enabling Gmail API: {str(e)}")

            # 3. Create OAuth credentials
            credentials_client = api_keys_v2.ApiKeysClient()
            
            # Create OAuth client
            parent = f"projects/{self.project_id}"
            key = api_keys_v2.Key()
            key.display_name = "Email Organizer OAuth Client"
            
            create_key_request = api_keys_v2.CreateKeyRequest(
                parent=parent,
                key=key
            )
            
            operation = credentials_client.create_key(request=create_key_request)
            created_key = operation.result()

            # 4. Save credentials to file
            credentials_data = {
                "installed": {
                    "client_id": created_key.key_string,
                    "project_id": self.project_id,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": created_key.secret_key_data.decode() if hasattr(created_key, 'secret_key_data') else "",
                    "redirect_uris": ["http://localhost"]
                }
            }

            with open(self.credentials_file, 'w') as f:
                json.dump(credentials_data, f)

            return True

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to setup project and credentials: {str(e)}"
            )

    def _save_credentials_file(self, credentials_data):
        """Save credentials data to file"""
        try:
            print(f"Attempting to save credentials to {self.credentials_file}")
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials_data, f)
            print(f"Successfully saved credentials to {self.credentials_file}")
        except Exception as e:
            print(f"Error saving credentials: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save credentials: {str(e)}"
            )

    async def authenticate(self):
        """Handle complete authentication flow"""
        try:
            # 1. Clean up session files
            self._cleanup_session_files()
            
            # 2. Check for existing project and permissions
            project = self.cloud_service.find_emailorganizer_project()
            
            if project:
                # Project exists, check permissions
                if self.cloud_service.check_gmail_api_enabled(project.project_id):
                    # Project has permissions, get existing credentials
                    credentials_data = self.cloud_service.create_oauth_credentials(project.project_id)
                else:
                    # Project exists but needs permissions
                    self.cloud_service.enable_gmail_api(project.project_id)
                    credentials_data = self.cloud_service.create_oauth_credentials(project.project_id)
            else:
                # No project exists, create new one
                self._setup_project_and_credentials()
                credentials_data = self.cloud_service.create_oauth_credentials(self.project_id)
            
            # 3. Save credentials and run OAuth flow
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials_data, f)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.SCOPES)
            creds = flow.run_local_server(port=0)
            
            # 4. Save token
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            
            # 5. Build service and get email
            self.service = build('gmail', 'v1', credentials=creds)
            profile = self.service.users().getProfile(userId='me').execute()
            return profile['emailAddress']
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Authentication failed: {str(e)}"
            )

    def get_email_body(self, payload):
        """Extract plain text email body"""
        parts = payload.get("parts", [])
        for part in parts:
            mime_type = part.get("mimeType")
            body = part.get("body", {}).get("data")
            if body and mime_type == "text/plain":
                return base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore").strip()
        
        # If no parts, check main body
        body = payload.get("body", {}).get("data")
        if body:
            return base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore").strip()
        return None

    def get_attachments_info(self, payload):
        """Get attachment names and formats"""
        attachments = []
        parts = payload.get("parts", [])
        for part in parts:
            filename = part.get("filename")
            mime_type = part.get("mimeType")
            if filename and mime_type:
                attachments.append({
                    "name": filename,
                    "format": mime_type
                })
        return attachments

    def fetch_emails(self, limit=50):
        """Fetch latest emails with specified limit"""
        if not self.service:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Please call /get-user-email first."
            )

        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            emails = []

            for msg in messages:
                msg_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                payload = msg_data.get("payload", {})
                headers = payload.get("headers", [])

                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), None)
                sender = next((h['value'] for h in headers if h['name'] == 'From'), None)
                date = next((h['value'] for h in headers if h['name'] == 'Date'), None)

                email_data = {
                    "id": msg['id'],
                    "subject": subject,
                    "from": sender,
                    "date": date,
                    "body": self.get_email_body(payload),
                    "attachments": self.get_attachments_info(payload)
                }
                
                emails.append(email_data)

            return {"emails": emails}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch emails: {str(e)}"
            )

    def get_user_email(self):
        """Get the current user's email address"""
        if not self.service:
            self.authenticate()
            
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get user email: {str(e)}"
            )

    def _create_or_get_project(self):
        """Create or get existing Google Cloud project"""
        client = resourcemanager_v3.ProjectsClient()
        
        try:
            # Try to get existing project
            project = client.get_project(name=f"projects/{self.project_id}")
            return project
        except exceptions.NotFound:
            # Create new project if not found
            project = client.create_project(
                request={
                    "project": {
                        "project_id": self.project_id,
                        "display_name": "Email Organizer"
                    }
                }
            )
            return project 