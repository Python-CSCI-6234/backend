from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
from config import settings
from fastapi import HTTPException
import json

class GoogleAuth:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        self.flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=self.scopes
        )

    def get_auth_url(self):
        """Generate the authorization URL for Google OAuth"""
        auth_url, _ = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return auth_url

    async def get_credentials(self, code: str):
        """Exchange authorization code for credentials"""
        try:
            self.flow.fetch_token(code=code)
            credentials = self.flow.credentials
            return credentials
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_gmail_service(self, credentials: Credentials):
        """Get Gmail service instance"""
        return build('gmail', 'v1', credentials=credentials)

    def get_user_info(self, credentials: Credentials):
        """Get user information from Google"""
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info

google_auth = GoogleAuth() 