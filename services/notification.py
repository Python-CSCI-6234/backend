import resend
from config import settings
from typing import Dict, List

class NotificationService:
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    async def send_email_notification(self, to: str, subject: str, content: str) -> Dict:
        """
        Send an email notification using Resend
        """
        try:
            params = {
                "from": "mailbot <notifications@aialexa.org>",
                "to": [to],  # Resend expects a list of recipients
                "subject": subject,
                "html": content
            }
            email = resend.Emails.send(params)
            return email
        except Exception as e:
            raise Exception(f"Error sending email notification: {str(e)}") from e

    async def send_daily_digest(self, to: str, digest_content: str) -> dict:
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
                    <p>Powered by mailbot</p>
                </body>
                </html>
                """
            )
            return response
        except Exception as e:
            raise Exception(f"Error sending daily digest: {str(e)}") from e

    async def send_important_notification(self, to: str, important_emails: List[Dict]) -> dict:
        """
        Send notification about important emails
        """
        try:
            email_list = "\n".join([f"• {email.get('subject', 'No Subject')}" for email in important_emails])
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
            raise Exception(f"Error sending important notification: {str(e)}") from e

notification_service = NotificationService() 