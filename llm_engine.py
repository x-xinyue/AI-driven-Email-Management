import json
import ollama

def get_llm_decision(email, user_pref):
    with open('email_categories.json') as f:
        categories = json.load(f)

    prompt = f"""
    Email Details:
    Sender: {email['sender']}
    Subject: {email['subject']}
    Body: {email['body_snippet']}

    You are an email management assistant. Categorize the following email into EXACTLY one of these categories: {list(categories.keys())}. Use the category definitions to guide your decision.

    Category Definitions:
    {json.dumps(categories, indent=2)}

    If the category is 'promotional', use this User Preference: {user_pref}. Based on the preference, suggest ONE action: 'keep', 'delete', or 'unsubscribe'?
    
    Respond ONLY in JSON format:
    {{
        "category": "...",
        "decision": "keep/delete/unsubscribe",
        "reason": "..."
        "confidence_score": 0.0-1.0
    }}
    """

    response = ollama.generate(model='llama3.2', prompt=prompt, format='json')
    return json.loads(response['response'])


