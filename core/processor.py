import json
import time

from postgres.vectordb_manager import save_preferences, find_relevant_preference
from integrations.gmail_manager import get_gmail_service, fetch_emails
from llm.llm_engine import get_llm_decision
from core.action_router import route_action


# ----------------------------
# Vector DB Setup
# ----------------------------
with open("user_preferences.json", "r") as f:
    user_prefs = json.load(f).get('preferences')

user_pref_ids = [f"rule_{i}" for i in range(len(user_prefs))]
save_preferences(user_prefs, user_pref_ids)


def process_emails(n=10):
    """
    Main function to process emails in the background.
    1. Fetches unprocessed emails using Gmail API.
    2. For each email, query the RAG database to find the MOST (only 1) relevant user preference.
    3. Gets LLM categorization and decision based on email and user preference.
    4. Routes the action via action_router.
    """
    service = get_gmail_service()
    emails = fetch_emails(service=service, total_emails=n)

    if not emails:
        return None

    for email in emails:
        email_id = email.get('id')
        sender = email.get('sender')
        subject = email.get('subject')
        body_snippet = email.get('body_snippet')
        unsubscribe_url = email.get('unsubscribe_url')
        
        # RAG QUERY (TO FIND THE MOST RELEVANT USER PREFERENCE)
        query_text = f"Email from {sender} with subject: {subject}"
        user_pref = find_relevant_preference(query_text=query_text, n_results=1)

        # LLM CALL
        email_data = {'sender': sender, 'subject': subject, 'body_snippet': body_snippet}
        result = get_llm_decision(email_data, user_pref)
        time.sleep(1)
            
        action = {
            "id": email_id,
            "action_id": email_id,
            "sender": sender,
            "subject": subject[:20],
            "decision": result.get('decision').lower(),
            "category": result.get('category'),
            "reason": result.get('reason'),
            "confidence_score": result.get('confidence_score'),
            "unsubscribe_url": unsubscribe_url,
            "result_data": result
        }

        # ROUTE ONLY (NO EXECUTION HERE)
        route_action(action)
