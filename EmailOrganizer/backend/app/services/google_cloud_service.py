from google.cloud import resourcemanager
from google.cloud import service_usage_v1
from google.cloud.service_usage_v1.types import EnableServiceRequest
from google.api_core import exceptions
from google.cloud import api_keys_v2
from fastapi import HTTPException
import json
import os

class GoogleCloudService:
    def __init__(self):
        self.project_search_term = "emailorganizer"
        
    def list_user_projects(self):
        """List all projects accessible by the user"""
        try:
            client = resourcemanager.Client()
            return list(client.list_projects())
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list projects: {str(e)}"
            )

    def find_emailorganizer_project(self):
        """Find project containing 'emailorganizer' in name"""
        projects = self.list_user_projects()
        for project in projects:
            if self.project_search_term in project.project_id.lower():
                return project
        return None

    def check_gmail_api_enabled(self, project_id):
        """Check if Gmail API is enabled for the project"""
        try:
            client = service_usage_v1.ServiceUsageClient()
            name = f"projects/{project_id}/services/gmail.googleapis.com"
            service = client.get_service(name=name)
            return service.state == service_usage_v1.State.ENABLED
        except exceptions.NotFound:
            return False
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check Gmail API status: {str(e)}"
            )

    def enable_gmail_api(self, project_id):
        """Enable Gmail API for the project"""
        try:
            client = service_usage_v1.ServiceUsageClient()
            name = f"projects/{project_id}/services/gmail.googleapis.com"
            request = EnableServiceRequest(name=name)
            operation = client.enable_service(request=request)
            operation.result()  # Wait for operation to complete
            return True
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to enable Gmail API: {str(e)}"
            )

    def create_oauth_credentials(self, project_id):
        """Create OAuth credentials for the project"""
        try:
            # Create OAuth client ID
            credentials_data = {
                "installed": {
                    "client_id": "YOUR_CLIENT_ID",  # This will be replaced with actual client ID
                    "project_id": project_id,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": "YOUR_CLIENT_SECRET",  # This will be replaced with actual secret
                    "redirect_uris": ["http://localhost"]
                }
            }

            # Check if we have environment variables for client ID and secret
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

            if client_id and client_secret:
                credentials_data["installed"]["client_id"] = client_id
                credentials_data["installed"]["client_secret"] = client_secret
                print("Using credentials from environment variables")
            else:
                print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables")
                print("Or create OAuth 2.0 credentials in Google Cloud Console and download them")
                print("Then replace the client_id and client_secret in credentials.json")
            
            return credentials_data
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create OAuth credentials: {str(e)}"
            )

    def create_new_project(self):
        """Create a new project with emailorganizer name"""
        try:
            client = resourcemanager.Client()
            project = resourcemanager.Project()
            project.project_id = f"{self.project_search_term}-{os.urandom(4).hex()}"
            project.display_name = "Email Organizer"
            
            operation = client.create_project(
                request={"project": project}
            )
            new_project = operation.result()
            return new_project
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create new project: {str(e)}"
            )

    def setup_project_credentials(self):
        """Setup project and return credentials data"""
        try:
            # Try to find existing project
            project = self.find_emailorganizer_project()
            
            if project:
                project_id = project.project_id
                # Check if Gmail API is enabled
                if not self.check_gmail_api_enabled(project_id):
                    self.enable_gmail_api(project_id)
            else:
                # Create new project
                project = self.create_new_project()
                project_id = project.project_id
                # Enable Gmail API
                self.enable_gmail_api(project_id)

            # Create or get OAuth credentials
            credentials_data = self.create_oauth_credentials(project_id)
            
            # Save credentials to file
            credentials_file = os.path.join(os.getcwd(), "credentials.json")
            with open(credentials_file, 'w') as f:
                json.dump(credentials_data, f)
            print(f"Saved credentials to {credentials_file}")
            
            return credentials_data
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to setup project credentials: {str(e)}"
            ) 