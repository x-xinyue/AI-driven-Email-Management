import time
from typing import Optional
import os
from enum import Enum
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 1. Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env!")

client = genai.Client(api_key=API_KEY)

class CategoryEnum(str, Enum):
    job_hunt = "job_hunt"
    career = "career"
    transactional = "transactional"
    promotional = "promotional"
    review = "review"


class EmailDecision(BaseModel):
    category: CategoryEnum = Field(description="The category of the email")
    decision: str = Field(description="Must be: keep, delete, or unsubscribe")
    reason: str = Field(description="A short explanation for the user")
    confidence_score: float = Field(description="0.0 to 1.0 accuracy estimate")

    company_name: Optional[str] = Field(None, description="The name of the company (e.g., Axrail, Maxis, Shopee)")
    job_role: Optional[str] = Field(None, description="The specific job title mentioned (e.g., Data Analyst, Graduate Trainee)")
    status_update: Optional[str] = Field(None, description="The stage of the application: Applied, Assessment, Interviewing, Rejected, or Offer")


def get_llm_decision(email_data, user_pref):
    """
    Categorizes emails using the latest google-genai SDK.
    """
    system_instruction = """
    ROLE: You are Astra, a logical Email Management Assistant.

    TASK: Categorize the incoming email into one of the following categories.

    CONTEXT & DEFINITIONS:
    - job_hunt: Emails regarding any job application UPDATES, job offers, interview invites, or rejections. NOTE: This is specifically for active job seeking.
    - career: LinkedIn alerts, job alerts (automated), and tech newsletters. NOTE: Not to be confused with 'job_hunt' which is for personal application updates.
    - transactional: Receipts, bills, bank statements, and ticket confirmations.
    - promotional: Marketing, sales, and brand newsletters.
    - review: Anything that doesn't fit the above.

    EXTRACTION RULES (Only for 'job_hunt'):
    1. COMPANY_NAME: Identify the employer.
    2. JOB_ROLE: Identify the position name.
    3. STATUS_UPDATE: Determine the current state:
       - 'Applied': Confirmation of receipt.
       - 'Assessment': Link to a technical test or HackerRank.
       - 'Interviewing': Invite for a screen or technical round.
       - 'Rejected': Application unsuccessful.
       - 'Offer': Employment offer received.

    CONSTRAINTS:
    - Prioritize 'job_hunt' if the email is a direct response to the user.
    - Use the user's preference for promotional items: {user_pref}
    - Respond ONLY in valid JSON.
    """

    prompt = f"""
    Sender: {email_data['sender']}
    Subject: {email_data['subject']}
    Body Snippet: {email_data['body_snippet']}
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_json_schema=EmailDecision.model_json_schema(),
                ),
            )
            return response.parsed
        
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            
            else:
                print(f"Error with Gemini API: {e}")
                return EmailDecision(
                    category=CategoryEnum.review,
                    decision="keep",
                    reason=f"System Error: {str(e)}",
                    confidence_score=0.0
                )
    

