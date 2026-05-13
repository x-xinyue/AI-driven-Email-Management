"""
LangChain RAG
"""
import os

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector


load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2-preview",
    output_dimensionality=768,
)

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="user_preferences",
    connection=os.getenv("POSTGRES_URL"),
    use_jsonb=True,
)


def save_preferences(db_docs: list, db_ids: list):
    """
    Saves a confirmed user preference into the vector db.
    """
    vector_store.add_texts(texts=db_docs, ids=db_ids)


def find_relevant_preferences(query_text: str, n_results=3):
    results = vector_store.similarity_search(query_text, k=n_results)
    
    if results:
        # Join all the retrieved rules into one string with bullet points
        return "\n".join([f"- {doc.page_content}" for doc in results])
    return "No specific user preference found."


def update_preferences(approved_senders, rule_map):
    """
    Inserts newly approved rules/user preferences into Postgres RAG.
    """
    new_rules = []
    new_ids = []
    
    for i, rule in rule_map.items():
        if rule['sender'] in approved_senders:
            new_rule = f"User has confirmed they want to {rule['decision']} all emails from {rule['sender']}."
            new_rules.append(new_rule)
            new_ids.append(f"confirmed_{rule['sender']}")
    
    if new_rules:
        save_preferences(new_rules, new_ids)
