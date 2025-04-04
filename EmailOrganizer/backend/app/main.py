from fastapi import FastAPI
from app.api import auth, emails

app = FastAPI()
app.include_router(auth.router)
app.include_router(emails.router, prefix="/api")
