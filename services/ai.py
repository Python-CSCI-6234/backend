from typing import List, Dict
import json
from config import settings
from openai import OpenAI
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        self.model = "deepseek/deepseek-chat-v3-0324:free"
        self.max_tokens = 1000
        self.temperature = 0.7

    def _prepare_email_batch(self, emails: List[Dict]) -> str:
        """Prepare a batch of emails for AI processing"""
        batch_text = ""
        for email in emails:
            batch_text += f"""
            Subject: {email.get('subject', 'No Subject')}
            From: {email.get('from', 'Unknown')}
            Date: {email.get('date', 'Unknown')}
            Body: {email.get('body', '')[:500]}...  # Truncate long bodies
            ---
            """
        return batch_text

    def _call_openrouter(self, prompt: str) -> str:
        """Make API call to OpenRouter"""
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": settings.SITE_URL,
                    "X-Title": settings.SITE_NAME,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that helps categorize and summarize emails. Always respond with valid JSON when asked for structured data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30  # 30 second timeout
            )
            if not completion or not completion.choices:
                raise Exception("No response from OpenRouter API")
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {str(e)}")
            # Return a fallback response instead of raising an exception
            return f"Error processing request: {str(e)}. Using fallback categorization."

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON response with multiple attempts and error handling"""
        try:
            # First attempt: direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # Second attempt: try to extract JSON from the response
                # Look for content between curly braces
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                logger.warning("Failed to parse JSON response, using fallback")
                return {"emails": []}  # Return empty structure for fallback
        return {"emails": []}  # Default fallback

    def summarize_emails(self, emails: List[Dict]) -> Dict:
        """
        Summarize a batch of emails and categorize them using OpenRouter
        """
        try:
            if not emails:
                return {"error": "No emails provided"}

            # Process emails in batches to avoid token limits
            batch_size = 5  # Adjust based on email size and token limits
            all_categories = {
                "work": [],
                "personal": [],
                "newsletters": [],
                "other": [],
                "important": []
            }
            all_summaries = []

            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                batch_text = self._prepare_email_batch(batch)

                prompt = f"""
                Analyze the following emails and provide a JSON response with this exact structure:
                {{
                    "emails": [
                        {{
                            "id": "email_id",
                            "category": "category_name",
                            "summary": "brief_summary",
                            "importance": "why_important_if_applicable"
                        }}
                    ]
                }}

                Categorize each email into one of these categories: work, personal, newsletters, important, or other.
                Provide a brief summary of each email.
                For important emails, explain why they are important.

                Emails to analyze:
                {batch_text}

                Respond ONLY with the JSON structure, no additional text.
                """

                response = self._call_openrouter(prompt)
                result = self._parse_json_response(response)
                
                for email_result in result.get("emails", []):
                    category = email_result.get("category", "other").lower()
                    if category in all_categories:
                        # Find the original email and add the AI analysis
                        original_email = next((e for e in batch if e.get('id') == email_result.get('id')), None)
                        if original_email:
                            original_email.update({
                                "ai_summary": email_result.get("summary", ""),
                                "importance": email_result.get("importance", "")
                            })
                            all_categories[category].append(original_email)
                            all_summaries.append(email_result.get("summary", ""))

            # Generate overall summary
            summary_prompt = f"""
            Based on these email summaries:
            {chr(10).join(all_summaries)}

            Provide a concise overall summary of the email batch, highlighting:
            1. Main topics discussed
            2. Any urgent or important matters
            3. Key action items if any

            Keep the summary under 200 words.
            """

            overall_summary = self._call_openrouter(summary_prompt)

            return {
                "total_emails": len(emails),
                "categories": all_categories,
                "important_emails": all_categories["important"],
                "summary_text": overall_summary,
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in summarize_emails: {str(e)}")
            raise Exception(f"Failed to summarize emails: {str(e)}")

    def generate_notification_summary(self, emails: List[Dict]) -> str:
        """
        Generate a concise summary for notifications using OpenRouter
        """
        try:
            if not emails:
                return "No new emails to summarize."

            try:
                summary = self.summarize_emails(emails)
                
                prompt = f"""
                Based on this email analysis: {summary.get('summary_text', '')}
                Create a friendly email summary in the following JSON structure. Return ONLY the JSON, no other text:

                {{
                    "email_summary": {{
                        "greeting": "A casual, friendly greeting",
                        "overview": "A brief, conversational overview of the emails",
                        "attention_needed": ["List of items needing immediate attention"],
                        "action_items": ["List of things to do"],
                        "email_list": ["List of email subjects with their importance"],
                        "closing": "A friendly closing note offering help if needed"
                    }}
                }}

                Make it feel personal and helpful, like a personal assistant talking to their boss.
                Keep the tone friendly but professional.
                Include ALL email subjects in the email_list.
                Highlight urgent or important matters in attention_needed.
                List specific actions needed in action_items.
                
                IMPORTANT: Return ONLY the JSON object, no additional text, no code blocks, no explanations.
                """

                response = self._call_openrouter(prompt)
                if "Error processing request" in response:
                    raise Exception(response)
                    
                # Try to parse the response to ensure it's valid JSON
                try:
                    json.loads(response)
                    return response
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract JSON from the response
                    import re
                    json_match = re.search(r'({[\s\S]*})', response)
                    if json_match:
                        return json_match.group(1)
                    raise ValueError("Response is not valid JSON")
                
            except Exception as e:
                logger.error(f"Error generating AI summary: {str(e)}")
                # Create a basic JSON structure as fallback
                email_list = [f"{email.get('subject', 'No Subject')} (From: {email.get('from', 'Unknown Sender')})" 
                            for email in emails]
                
                basic_summary = {
                    "email_summary": {
                        "greeting": "Hey there!",
                        "overview": "Here's a quick summary of your emails:",
                        "attention_needed": [],
                        "action_items": [],
                        "email_list": email_list,
                        "closing": "Let me know if you need anything else!"
                    }
                }
                return json.dumps(basic_summary)
                
        except Exception as e:
            logger.error(f"Error in generate_notification_summary: {str(e)}")
            return json.dumps({
                "email_summary": {
                    "greeting": "Hey there!",
                    "overview": "Sorry, I encountered an error while processing your emails.",
                    "attention_needed": [],
                    "action_items": [],
                    "email_list": [],
                    "closing": "Please try again later."
                }
            })

    def generate_daily_digest(self, emails: List[Dict]) -> str:
        """
        Generate a detailed daily digest using OpenRouter
        """
        try:
            summary = self.summarize_emails(emails)
            
            prompt = f"""
            Create a comprehensive daily digest based on this email analysis:
            {summary['summary_text']}

            Include:
            1. Overview of the day's emails
            2. Important updates and announcements
            3. Action items and follow-ups
            4. Key discussions and decisions

            Format it as a well-structured daily report.
            """

            digest_text = self._call_openrouter(prompt)
            return digest_text
        except Exception as e:
            logger.error(f"Error generating daily digest: {str(e)}")
            raise Exception(f"Failed to generate daily digest: {str(e)}")

ai_service = AIService() 