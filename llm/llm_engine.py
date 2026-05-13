import os

from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


load_dotenv()


class CategoryEnum(str, Enum):
    career = "career"
    job_hunt = "job_hunt"
    promotional = "promotional"
    review = "review"
    transactional = "transactional"


class StatusEnum(str, Enum):
    applied = "applied"
    assessment = "assessment"
    interview = "interview"
    rejection = "rejection"
    offer = "offer"
    


class EmailDecision(BaseModel):
    email_id: str = Field(description="The unique ID of the email from the input list")  # for processor.py to map results back to original emails
    category: CategoryEnum = Field(description="The category of the email")
    decision: str = Field(description="Must be: keep, delete, or unsubscribe")
    reason: str = Field(description="A short explanation for the user")
    confidence_score: float = Field(description="0.0 to 1.0 accuracy estimate")

    # Career extraction fields
    position: Optional[str] = Field(None, description="The specific job title mentioned (e.g., Data Analyst, Graduate Trainee)")
    company: Optional[str] = Field(None, description="The name of the company (e.g., Axrail, Maxis, Shopee)")
    industry: Optional[str] = Field(None, description="The industry of the company (e.g., Tech, Consulting, Finance)")
    location: Optional[str] = Field(None, description="The job location (e.g., KL, Subang Jaya, Remote)")
    date_applied: Optional[str] = Field(None, description="The date of the email")
    status_update: Optional[StatusEnum] = Field(None, description="The current application stage")


class BatchEmailDecision(BaseModel):
    """
    Container for multiple email decisions to ensure a single batch JSON response.
    """
    decisions: List[EmailDecision]


def get_llm_decision(email_data, user_pref):
    """
    Categorizes emails using LangChain and Google Gemini.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

    structured_llm = llm.with_structured_output(BatchEmailDecision)

    system_instruction = f"""
    ROLE: You are a logical Email Management Assistant.

    TASK: Categorize the batch of emails into the defined categories.

    CONTEXT & DEFINITIONS:
    - job_hunt: Emails regarding any job application UPDATES, job offers, interview invites, or rejections. (NOTE: This is specifically for active job seeking)
    - career: Automated job alerts, newsletters, or generic job postings. (NOTE: Not to be confused with 'job_hunt' which is for personal job application updates)
    - transactional: Receipts, bills, bank statements, and confirmations.
    - promotional: Marketing, sales, and brand newsletters.
    - review: Anything that doesn't fit the above.

    EXTRACTION RULES (only for 'job_hunt'):
    1. POSITION: Identify the job role name.
    2. COMPANY: Identify the company's name.
    3. INDUSTRY: Use your internal knowledge to identify the company's sector e.g., 'Consulting'.
    4. LOCATION: Extract the city or 'Remote' from the text. If unknown, use your internal knowledge to identify the company's office location e.g., KL, PJ.
    3. DATE_APPLIED RULES:
        - Look for a specific date mentioned in the Snippet e.g., 'I applied on April 5th'.
        - If no specific date is mentioned in the text, use the 'Timestamp' provided for that email.
        - ALWAYS return the date in the format: MMM-DD-YYYY e.g., 'May-11-2026'.
    4. Set STATUS_UPDATE ONLY to one of these exact values to match my spreadsheet dropdown:
       - 'applied': Confirmation of receipt.
       - 'assessment': Link to a technical test e.g., HackerRank.
       - 'interview': Invite for a screen or technical round.
       - 'rejection': Application unsuccessful.
       - 'offer': Employment offer received.

    CONSTRAINTS:
    - Every email ID provided MUST have a corresponding decision in the list.
    - Prioritize 'job_hunt' if the email is a direct response to the user.
    - Use the user's preference for promotional items: {user_pref} (FOLLOW EXACTLY, if unsure just choose to delete.)
    """

    batch_text = "Emails to analyze:\n\n"
    for email in email_data:
        batch_text += (
            f"Email_ID: {email['id']}\n"
            f"Timestamp: {email.get('date_received')}\n"
            f"Sender: {email['sender']}\n"
            f"Subject: {email['subject']}\n"
            f"Snippet: {email['body_snippet']}\n"
            "---\n"
        )

    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=batch_text)
    ]

    try:
        response = structured_llm.invoke(messages)
        return response.decisions
    except Exception as e:
        print(f"Error with LLM: {e}")
        return []
