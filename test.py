import sqlite3
import ollama
import chromadb


# 1. Setup Vector DB (The "Preference Store")
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

def process_emails():
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, sender, subject, body_snippet FROM emails WHERE status = 'Unprocessed'")
    emails = cursor.fetchall()

    for email in emails:
        e_id, sender, subject, snippet = email
        query_text = f"Email from {sender} with subject: {subject}"

        # 2. RETRIEVAL: Find the relevant preference
        results = collection.query(query_texts=[query_text], n_results=1)
        relevant_rule = results['documents'][0][0]

        # 3. GENERATION: Ask Ollama for a decision
        prompt = f"""
        User Preference: {relevant_rule}
        Email Sender: {sender}
        Email Subject: {subject}
        Body: {snippet}

        Based on the preference, should I 'keep', 'delete', or 'unsubscribe'? 
        Respond in JSON format: {{"decision": "...", "reason": "..."}}
        """

        response = ollama.generate(model='llama3.1', prompt=prompt, format='json')
        print(f"ID {e_id} | Decision: {response['response']}")

    conn.close()

if __name__ == "__main__":
    process_emails()
