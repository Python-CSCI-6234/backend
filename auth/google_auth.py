from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import settings
from fastapi import HTTPException
import json
import logging

logger = logging.getLogger(__name__)

class GoogleAuth:
    def __init__(self):
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        
        # Validate required environment variables
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID is not set")
        if not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_SECRET is not set")
        if not settings.GOOGLE_REDIRECT_URI:
            raise ValueError("GOOGLE_REDIRECT_URI is not set")
            
        logger.debug(f"Initializing GoogleAuth with client_id: {settings.GOOGLE_CLIENT_ID}")
        logger.debug(f"Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
        
        try:
            # Create OAuth2 client configuration
            self.client_config = {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            }
            
            logger.debug(f"Client config: {json.dumps(self.client_config, indent=2)}")
            
            # Initialize the flow
            self.flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            logger.debug("Flow initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Flow: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize OAuth flow: {str(e)}"
            )

    def get_auth_url(self):
        """Generate the authorization URL for Google OAuth"""
        try:
            auth_url, _ = self.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            logger.debug(f"Generated auth URL: {auth_url}")
            return auth_url
        except Exception as e:
            logger.error(f"Error generating auth URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate auth URL: {str(e)}"
            )

    async def get_credentials(self, code: str):
        """Exchange authorization code for credentials"""
        try:
            logger.debug("Starting token exchange process")
            if not code:
                raise ValueError("Authorization code is required")
                
            logger.debug(f"Attempting to fetch token with code: {code}")
            
            # Create a new flow instance for each token exchange
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            # Exchange the code for a token
            flow.fetch_token(code=code)
            
            if not flow.credentials:
                logger.error("No credentials returned after token exchange")
                raise ValueError("Failed to get credentials from token exchange")
                
            credentials = flow.credentials
            logger.debug("Successfully obtained credentials")
            return credentials
            
        except Exception as e:
            logger.error(f"Error in get_credentials: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get credentials: {str(e)}"
            )

    def get_gmail_service(self, credentials: Credentials):
        """Get Gmail service instance"""
        return build('gmail', 'v1', credentials=credentials)

    def get_user_info(self, credentials: Credentials):
        """Get user information from Google"""
        try:
            logger.debug("Attempting to get user info")
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            logger.debug(f"Successfully retrieved user info: {user_info}")
            return user_info
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get user info: {str(e)}"
            )

google_auth = GoogleAuth() 