from gmail_manager import delete_email, get_gmail_service, apply_label_to_email, unsubscribe_from_email
from spreadsheet_manager import upsert_job_entry, get_spreadsheet_service


def execute_actions(actions):
    service = get_gmail_service()
    spreadsheet_service = get_spreadsheet_service()
    SHEET_ID = "1A52Egh3s8BfkwaL5L1o6mvacDvqTVxr7cqiKBZcBCVw"
    SHEET_NAME = "Applications 2026"

    for action in actions:
        msg_id = action['id']
        decision = action['decision']
        category = action['category']
        confidence_score = action['confidence_score']
        
        if decision == 'keep':
            label_map = {
                'job_hunt': 'Job Hunt',
                'career': 'Career',
                'transactional': 'Transactional',
                'promotional': 'Promotional'
            }
            label = label_map.get(category, 'Review')
            apply_label_to_email(service, msg_id, label)
            
            if category == 'job_hunt' and confidence_score >= 0.8:
                upsert_job_entry(spreadsheet_service, SHEET_ID, SHEET_NAME, action)
                

        elif decision in ['delete', 'unsubscribe']:
            delete_email(service, msg_id)
            print(f"Email ID {action['id']} moved to trash.")

        # UNSUBSCRIBE LOGIC
        if action['decision'] == 'unsubscribe' and action['unsubscribe_url']:
            unsubscribe_from_email(service, msg_id, action['unsubscribe_url'])


    print("\nProcessing Complete.")