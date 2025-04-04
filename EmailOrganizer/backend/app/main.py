from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api import auth
from app.core.config import settings
import secrets

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generate a secure secret key
secret_key = secrets.token_urlsafe(32)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="session",
    max_age=1800,  # 30 minutes
    same_site="lax",
    https_only=False  # Set to True in production
)

app.include_router(auth.router)
