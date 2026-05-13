"""
Executes instant and approved actions (delete, unsubscribe).
Updates the RAG database with any new confirmed rules for future automation.
"""

import os

from dotenv import load_dotenv
from integrations.gmail_manager import get_gmail_service, apply_label_to_email, delete_email, unsubscribe_from_email
from integrations.spreadsheet_manager import get_spreadsheet_service, upsert_job_entry


load_dotenv()


def execute_actions(actions):
    gmail_service = get_gmail_service()
    spreadsheet_service = get_spreadsheet_service()
    spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
    spreadsheet_name = os.getenv("GOOGLE_SHEET_NAME")

    for action in actions:
        email_id = action['id']
        decision = action['decision']
        category = action['category']
        confidence_score = action['confidence_score']
        unsubscribe_url = action['unsubscribe_url']
        result_data = action['result_data']
        
        if decision == 'keep':
            label_map = {
                'career': 'Career',
                'job_hunt': 'Job Hunt',
                'promotional': 'Promotional',
                'transactional': 'Transactional'
            }
            label = label_map.get(category, 'Review')
            apply_label_to_email(gmail_service, email_id, label)
            
            if category == 'job_hunt' and confidence_score >= 0.8:
                upsert_job_entry(spreadsheet_service, spreadsheet_id, spreadsheet_name, result_data)
                
        elif decision == 'delete':
            delete_email(gmail_service, email_id)

        elif decision == 'unsubscribe':
            if unsubscribe_url:
                unsubscribe_from_email(gmail_service, email_id, unsubscribe_url)
