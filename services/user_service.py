from models.user import UserCredentials
from config import settings
from datetime import datetime, timedelta
import jwt
from typing import Optional
import json
import os
from pathlib import Path

class UserService:
    def __init__(self):
        self.credentials_dir = Path("credentials")
        self.credentials_dir.mkdir(exist_ok=True)

    async def store_user_credentials(self, user_credentials: UserCredentials) -> None:
        """Store user credentials securely"""
        # Convert the model to a dict with datetime as ISO format string
        cred_dict = user_credentials.dict()
        cred_dict['token_expiry'] = user_credentials.token_expiry.isoformat() if user_credentials.token_expiry else None
        
        # Encrypt sensitive data before storing
        encrypted_data = jwt.encode(
            cred_dict,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        file_path = self.credentials_dir / f"{user_credentials.user_id}.enc"
        with open(file_path, "w") as f:
            f.write(encrypted_data)

    async def get_user_credentials(self, user_id: str) -> Optional[UserCredentials]:
        """Retrieve user credentials"""
        file_path = self.credentials_dir / f"{user_id}.enc"
        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            encrypted_data = f.read()

        try:
            data = jwt.decode(
                encrypted_data,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            # Convert ISO format string back to datetime
            if data.get('token_expiry'):
                data['token_expiry'] = datetime.fromisoformat(data['token_expiry'])
            return UserCredentials(**data)
        except:
            return None

    async def get_all_users_for_digest(self) -> list[UserCredentials]:
        """Get all users who have enabled daily digest"""
        users = []
        for file_path in self.credentials_dir.glob("*.enc"):
            user = await self.get_user_credentials(file_path.stem)
            if user and user.preferences.get("digest_enabled", True):
                users.append(user)
        return users

user_service = UserService() 