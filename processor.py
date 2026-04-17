import sqlite3
import ollama
import chromadb
import json
from executor import execute_actions

# 1. Setup Vector DB
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="user_preferences")

preferences = [
    "I love McDonald's deals and want to keep them.",
    "I dislike KFC promotional emails and want to unsubscribe.",
    "Career-related emails from LinkedIn or companies are high priority.",
    "Bank statements and utility bills must never be deleted."
]
collection.add(
    documents=preferences,
    ids=[f"rule_{i}" for i in range(len(preferences))]
)

def process_emails(dry_run=True):
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, sender, subject, body_snippet, unsubscribe_url FROM emails WHERE status = 'Unprocessed'")
    emails = cursor.fetchall()

    if not emails:
        print("🎉 No new emails to process!")
        return []

    actions_to_take = []

    for email in emails:
        e_id, sender, subject, snippet, unsub_url = email
        query_text = f"Email from {sender} with subject: {subject}"

        # 2. RETRIEVAL
        results = collection.query(query_texts=[query_text], n_results=1)
        relevant_rule = results['documents'][0][0]

        # 3. GENERATION
        prompt = f"""
        User Preference: {relevant_rule}
        Email Sender: {sender}
        Email Subject: {subject}
        Body: {snippet}

        Based on the preference, should I 'keep', 'delete', or 'unsubscribe'? 
        Respond in JSON format: {{"decision": "...", "reason": "..."}}
        """

        response = ollama.generate(model='llama3.1', prompt=prompt, format='json')
        res_data = json.loads(response['response'])

        actions_to_take.append({
            "id": e_id,
            "sender": sender,
            "subject": subject[:30], 
            "decision": res_data['decision'].lower(),
            "reason": res_data['reason'],
            "unsubscribe_url": unsub_url
        })

    # PRINT SUMMARY TABLE
    print(f"\n{'ID':<4} | {'SENDER':<25} | {'DECISION':<12} | {'REASON'}")
    print("-" * 80)
    for a in actions_to_take:
        print(f"{a['id']:<4} | {a['sender']:<25} | {a['decision']:<12} | {a['reason']}")

    # 4. EXECUTION CALL
    confirm = input("\nProceed with these actions? (y/n): ").lower()
    if confirm == 'y':
        execute_actions(actions_to_take, dry_run)
    else:
        print("Aborted. No changes made.")
    
    conn.close()
    return actions_to_take
