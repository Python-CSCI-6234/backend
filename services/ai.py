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
            Based on this email analysis: {summary['summary_text']}
            Create a comprehensive daily digest in the following JSON structure. Return ONLY the JSON, no markdown or code blocks:

            {{
                "daily_digest": {{
                    "overview": {{
                        "description": "A friendly summary of today's emails",
                        "total_emails_processed": "Number of emails processed",
                        "main_topics": ["List of main topics discussed"]
                    }},
                    "important_updates_and_announcements": {{
                        "updates": ["List of important updates"],
                        "announcements": ["List of announcements"],
                        "notes": "Any additional notes about updates"
                    }},
                    "action_items_and_follow_ups": {{
                        "key_action_items": ["List of things that need to be done"],
                        "follow_ups": ["List of items needing follow-up"],
                        "deadlines": "Any important deadlines"
                    }},
                    "key_discussions_and_decisions": {{
                        "discussions": ["List of important discussions"],
                        "decisions": ["List of decisions made"],
                        "notes": "Additional context about discussions"
                    }},
                    "additional_notes": "Any other important information"
                }}
            }}

            IMPORTANT: Return ONLY the JSON object, no markdown, no code blocks, no additional text.
            Make it friendly and conversational while maintaining professionalism.
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
            logger.error(f"Error generating daily digest: {str(e)}")
            # Return a basic digest structure as fallback
            return json.dumps({
                "daily_digest": {
                    "overview": {
                        "description": "Sorry, I encountered an error while generating your daily digest.",
                        "total_emails_processed": "0",
                        "main_topics": []
                    },
                    "important_updates_and_announcements": {
                        "updates": [],
                        "announcements": [],
                        "notes": "Unable to process updates at this time."
                    },
                    "action_items_and_follow_ups": {
                        "key_action_items": [],
                        "follow_ups": [],
                        "deadlines": "None"
                    },
                    "key_discussions_and_decisions": {
                        "discussions": [],
                        "decisions": [],
                        "notes": "Unable to process discussions at this time."
                    },
                    "additional_notes": "Please try again later."
                }
            })

ai_service = AIService() 