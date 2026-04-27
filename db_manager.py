import sqlite3
import chromadb


def setup_database(db_name: str) -> chromadb.api.models.Collection.Collection:
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name=db_name)
    return collection


def populate_database(collection: chromadb.api.models.Collection.Collection, db_docs: list, db_ids: list):
    collection.add(documents=db_docs, ids=db_ids)


def connect_database(db_name: str):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    return cursor


def query_database(collection, query_text, n_results=1):
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return results['documents'][0]


def update_preferences(collection, approved_senders, rule_map):
    new_rules = []
    for i, rule in rule_map.items():
        if rule['sender'] in approved_senders:
            new_rule = f"User has confirmed they want to {rule['decision']} all emails from {rule['sender']}."
            new_rules.append(new_rule)
    
    # Add these new confirmed rules to your ChromaDB collection
    if new_rules:
        collection.add(
            documents=new_rules,
            ids=[f"confirmed_{sender}" for sender in approved_senders]
        )
        print(f"Updated your RAG brain with {len(new_rules)} new rules.")

