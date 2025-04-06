from resend import Resend
from config import settings
from typing import Dict, List
import json

class NotificationService:
    def __init__(self):
        self.resend = Resend(api_key=settings.RESEND_API_KEY)

    async def send_email_notification(self, to: str, subject: str, content: str):
        """
        Send an email notification using Resend
        """
        try:
            response = self.resend.emails.send({
                "from": "Email Organizer <notifications@emailorganizer.com>",
                "to": to,
                "subject": subject,
                "html": content
            })
            return response
        except Exception as e:
            raise Exception(f"Error sending email notification: {str(e)}")

    async def send_daily_digest(self, to: str, digest_content: str):
        """
        Send the daily email digest
        """
        try:
            response = await self.send_email_notification(
                to=to,
                subject="📊 Your Daily Email Digest",
                content=f"""
                <html>
                    <body>
                        <h1>📊 Daily Email Digest</h1>
                        <div style="white-space: pre-line;">
                            {digest_content}
                        </div>
                        <p>Powered by Email Organizer</p>
                    </body>
                </html>
                """
            )
            return response
        except Exception as e:
            raise Exception(f"Error sending daily digest: {str(e)}")

    async def send_important_notification(self, to: str, important_emails: List[Dict]):
        """
        Send notification about important emails
        """
        try:
            email_list = "\n".join([f"• {email['subject']}" for email in important_emails])
            response = await self.send_email_notification(
                to=to,
                subject="⚠️ Important Emails Require Attention",
                content=f"""
                <html>
                    <body>
                        <h2>⚠️ Important Emails</h2>
                        <p>The following emails require your attention:</p>
                        <div style="white-space: pre-line;">
                            {email_list}
                        </div>
                    </body>
                </html>
                """
            )
            return response
        except Exception as e:
            raise Exception(f"Error sending important notification: {str(e)}")

notification_service = NotificationService() 