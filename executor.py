from gmail_manager import delete_email, get_gmail_service, apply_label_to_email, unsubscribe_from_email


def execute_actions(actions):
    service = get_gmail_service()

    for action in actions:
        msg_id = action['id']
        sender = action['sender']
        subject = action['subject']
        decision = action['decision']
        category = action['category']
        
        if decision == 'keep':
            label_map = {
                'job_hunt': 'Job Hunt',
                'career': 'Career',
                'transactional': 'Transactional',
                'promotional': 'Promotional'
            }
            label = label_map.get(category, 'Review')
            apply_label_to_email(service, msg_id, label)

        elif decision in ['delete', 'unsubscribe']:
            delete_email(service, msg_id)
            print(f"Email ID {action['id']} moved to trash.")

        # UNSUBSCRIBE LOGIC
        if action['decision'] == 'unsubscribe' and action['unsubscribe_url']:
            unsubscribe_from_email(service, msg_id, action['unsubscribe_url'])


    print("\nProcessing Complete.")