from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    CLIENT_SECRET_FILE = "credentials.json"
    SCOPES = [os.getenv("GOOGLE_SCOPES", "https://www.googleapis.com/auth/gmail.readonly")]
    TOKEN_FILE = "token.json"

settings = Settings()
