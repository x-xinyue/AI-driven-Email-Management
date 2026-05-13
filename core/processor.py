import json

from postgres.vectordb_manager import save_preferences, find_relevant_preferences
from postgres.db_manager import get_past_delete_count
from integrations.gmail_manager import get_gmail_service, fetch_emails
from llm.llm_engine import get_llm_decision
from core.action_router import route_action


# ----------------------------
# Vector DB Setup
# ----------------------------
# with open("user_preferences.json", "r") as f:
#     user_prefs = json.load(f).get('preferences')

# user_pref_ids = [f"rule_{i}" for i in range(len(user_prefs))]
# save_preferences(user_prefs, user_pref_ids)


def process_emails(n=10):
    """
    Main function to process emails in the background.
    1. Fetches unprocessed emails using Gmail API.
    2. Enrich emails with short-term memory context.
    3. Retrieve relevant long-term user preferences from the vector database (RAG).
    4. Gets LLM categorization and decision based on emails and user preferences.
    5. Force unsubscribe for repeatedly deleted senders.
    6. Routes the action via action_router.
    """
    # 1. Fetch emails
    service = get_gmail_service()
    emails = fetch_emails(service=service, total_emails=n)

    stats = {"processed": len(emails), "instant": 0, "approved": 0}

    if not emails:
        return {"processed": 0, "instant": 0, "approved": 0}

    # 2. Short-term memory
    enriched_emails = []
    for email in emails:
        delete_count = get_past_delete_count(email['sender'])
        # Inject memory context into the body snippet so the LLM sees it
        memory_context = f"[SYSTEM NOTE: User has manually deleted this sender {delete_count} times.] " if delete_count > 0 else ""
        email['body_snippet'] = memory_context + email['body_snippet']
        enriched_emails.append(email)

    # 3. Long-term memory - Query RAG for rules specifically related to these senders/subjects
    senders_list = ", ".join(list(set([e['sender'] for e in emails])))
    subjects_list = ", ".join([e['subject'][:20] for e in emails])
    query_text = f"User preferences for emails from: {senders_list}. Topics: {subjects_list}"
    user_pref = find_relevant_preferences(query_text=query_text, n_results=3)

    # 4. LLM call
    results = get_llm_decision(enriched_emails, user_pref)

    for result in results:
        # Match the LLM result back to the original email to get the unsubscribe_url
        original_email = next((e for e in emails if e['id'] == result.email_id), None)
        
        if original_email:
            action = {
                "id": result.email_id,
                "action_id": result.email_id,
                "sender": original_email['sender'],
                "subject": original_email['subject'][:20],
                "decision": result.decision.lower(),
                "category": result.category,
                "reason": result.reason,
                "confidence_score": result.confidence_score,
                "unsubscribe_url": original_email['unsubscribe_url'],
                "result_data": result.dict() # Use .dict() for Pydantic models
            }
            
            # 5. Force unsubscribe when LLM suggested 'delete' and user has deleted them 3+ times
            if action['decision'] == 'delete' and get_past_delete_count(action['sender']) >= 3:
                if action['unsubscribe_url']:
                    action['decision'] = 'unsubscribe'
                    action['reason'] = "Proactive suggestion: User repeatedly deletes this sender."
            
            category = action["category"].lower()
            if category in ['job_hunt', 'career', 'transactional']:
                stats["instant"] += 1
            else:
                stats["approved"] += 1

            # 6. ROUTE ONLY (NO EXECUTION HERE)
            route_action(action)
            
    return stats
