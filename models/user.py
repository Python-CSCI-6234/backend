from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCredentials(BaseModel):
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    token_expiry: datetime
    preferences: dict = {
        "digest_time": "00:00",  # Default digest time
        "timezone": "UTC",
        "digest_enabled": True
    } 