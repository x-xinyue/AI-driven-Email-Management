from collections import defaultdict
import json
import time
from db_manager import query_database, update_preferences, setup_database, populate_database
from executor import execute_actions
from gmail_manager import get_gmail_service, fetch_emails
from llm_engine import get_llm_decision


# Vector DB setup
collection = setup_database("user_preferences")

with open("user_preferences.json", "r") as f:
    user_preferences = json.load(f)["preferences"]

populate_database(collection, user_preferences, [f"rule_{i}" for i in range(len(user_preferences))])


def process_emails(n=10, specific_day_query=None):
    """
    Main function to process emails.

        1. Fetch unprocessed emails from Gmail through API
        2. For each email, query the RAG database to find the MOST relevant user preference (only 1)
        3. Send email details + relevant preferences to the LLM for categorization and action decision
        If email is categorised as "promotional" or "review", we will propose a new rule to the user for confirmation before executing any action. This is crucial for building trust and allowing the user to have control over the automation process.
        4. Collect proposed actions and group them by sender + decision for user confirmation
        5. Execute approved actions (e.g., delete, unsubscribe) and update the RAG database with any new confirmed rules for future automation
    """
    # 1. FETCH UNPROCESSED EMAILS
    service = get_gmail_service()
    emails = fetch_emails(service, max_results=n, query=specific_day_query)
    print(f"Fetched {len(emails)} emails for processing.")

    if not emails:
        print("No new emails to process!")
        return []

    instant_actions = []
    actions_to_take = []
    proposed_rules = defaultdict(list)

    for email in emails:
        email_id = email.get('id')
        sender = email.get('sender')
        subject = email.get('subject')
        body_snippet = email.get('body_snippet') # or 'snippet' depending on your fetcher
        unsub_url = email.get('unsubscribe_url')
        
        # 2. RAG QUERY TO FIND THE MOST RELEVANT USER PREFERENCE
        query_text = f"Email from {sender} with subject: {subject}"
        relevant_rule = query_database(collection, query_text, n_results=1)[0]

        # 3. LLM CALL
        email_data = {'sender': sender, 'subject': subject, 'body_snippet': body_snippet}
        res_data = get_llm_decision(email_data, relevant_rule)
        time.sleep(1)  # Short pause to respect rate limits and avoid overwhelming the LLM

        # TODO: update google sheet if email is categorised as job_hunt

        print(f"\n[Testing] {sender} | {subject[:40]}")
        print(f"   └─ Category: {res_data['category']}")
        print(f"   └─ Decision: {res_data['decision']}")
        print(f"   └─ Reason: {res_data['reason']}")
        
        # 4. COLLECT PROPOSED ACTIONS AND GROUP BY SENDER + DECISION
        action = {
            "id": email_id,
            "sender": sender,
            "subject": subject[:30], 
            "decision": res_data['decision'].lower(),
            "reason": res_data['reason'],
            "unsubscribe_url": unsub_url,
            "category": res_data['category'],
            "confidence_score": res_data['confidence_score'],
            "company_name": res_data.get('company_name'),
            "job_role": res_data.get('job_role'),
            "status_update": res_data.get('status_update')
        }

        if res_data['category'].lower() in ['job_hunt', 'career', 'transactional']:
            instant_actions.append(action)
            print(f"Email categorised as {res_data['category']} successfully!")

        else:  # Promotional/Review emails
            actions_to_take.append(action)
            # Dictionary key example: ("example@domain.com", "delete"): [id1, id2, id3]
            group_key = (sender, res_data['decision'])
            proposed_rules[group_key].append(email_id)
            


    if instant_actions:
        execute_actions(instant_actions)
        # print("Job hunt/Transactional emails Executed!")


    if proposed_rules:
        confirmation_action(collection, proposed_rules, actions_to_take)
    
    
        


def confirmation_action(collection, proposed_rules, actions_to_take):
    """
    Double confirmation step for the user to approve proposed rules before executing them permanently. This is crucial for building trust and allowing the user to have control over the automation process.
    1. Display proposed rules based on sender + action (e.g., "Always DELETE emails from
    2. Allow user to select which rules to approve (e.g., "1,3" or "all")
    3. Execute only the approved rules on the current batch of emails
    4. Update the RAG database with the approved rules for future decision-making
    """
    # 2. THE TOPIC-BASED CONFIRMATION
    print("\n--- PROPOSED RULES ---")
    rule_map = {}
    # enumerate logic : [1, ("example@domain.com", "delete")]  enumerate will give us an index starting from 1, and the key-value pair from proposed_rules where items() gives us the key (sender, decision) and the value (ids)
    for i, ((sender, decision), ids) in enumerate(proposed_rules.items(), 1): 
        print(f"[{i}] Always {decision.upper()} emails from: {sender} ({len(ids)} emails found)")
        # Output: [1] Always DELETE emails from: example@domain.com (3 emails found)
        rule_map[i] = {"sender": sender, "decision": decision, "ids": ids}

    choice = input("\nEnter the numbers you want to PERMANENTLY approve (e.g., 1,3) or 'all': ")

    # SELECTIVE EXECUTION
    final_actions = []
    approved_senders = []

    if choice.lower() == 'all':
        final_actions = actions_to_take
        approved_senders = [r['sender'] for r in rule_map.values()]
    else:
        # 1. Gather the senders the user actually approved
        if choice.lower() != 'none':
            try:
                selected_indices = [int(x.strip()) for x in choice.split(',')]
                for idx in selected_indices:
                    if idx in rule_map:
                        approved_senders.append(rule_map[idx]['sender'])
            except ValueError:
                print("Invalid input detected. Defaulting to 'none'.")

        # 2. Process ALL actions, but downgrade unapproved ones to 'keep'
        for action in actions_to_take:
            if action['sender'] in approved_senders:
                # The user approved the LLM's proposed destructive action
                final_actions.append(action)
            else:
                # The user did NOT approve. We override the LLM's decision.
                action['decision'] = 'keep'
                final_actions.append(action)
    # 4. DYNAMIC RAG UPDATE (The most important part!)
    if approved_senders:
        update_preferences(collection, approved_senders, rule_map)

    if final_actions:
        print("\nExecuting approved actions...")
        execute_actions(final_actions)
        