import json

from gmail_manager import fetch_emails, get_gmail_service
from llm_engine import get_llm_decision


def test_classification():

    service = get_gmail_service()
    specific_day_query = "after:2026/04/28 before:2026/04/30"
    emails = fetch_emails(service, max_results=7, query=specific_day_query)
    for i, email in enumerate(emails):
        print(f"email {i+1}: {email}\n")
        # response = get_llm_decision(email, user_pref="None")
        # print(f"LLM Response for email {i+1}: {response}\n")



if __name__ == "__main__":

    test_classification()
    