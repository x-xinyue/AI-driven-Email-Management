import pytest

from unittest.mock import patch, MagicMock
from postgres.vectordb_manager import find_relevant_preference, update_preferences, save_preferences


@patch('postgres.vectordb_manager.vector_store.similarity_search')
def test_find_relevant_preference_found(mock_similarity_search):
    # Setup a fake LangChain Document object return
    mock_doc = MagicMock()
    mock_doc.page_content = "User has confirmed they want to keep all emails from hr@company.com."
    mock_similarity_search.return_value = [mock_doc]

    result = find_relevant_preference("Email from hr@company.com with subject: Interview")

    assert result == "User has confirmed they want to keep all emails from hr@company.com."
    mock_similarity_search.assert_called_once()


@patch('postgres.vectordb_manager.vector_store.similarity_search')
def test_find_relevant_preference_not_found(mock_similarity_search):
    # Setup empty return
    mock_similarity_search.return_value = []

    result = find_relevant_preference("Email from unknown@spam.com")
    assert result == "No specific user preference found."

@patch('postgres.vectordb_manager.vector_store.add_texts')
def test_save_preferences(mock_add_texts):
    # Setup
    docs = ["Rule 1", "Rule 2"]
    ids = ["id1", "id2"]

    # Execute
    save_preferences(docs, ids)

    # Assert: Ensure it calls LangChain's add_texts correctly
    mock_add_texts.assert_called_once_with(texts=docs, ids=ids)

@patch('postgres.vectordb_manager.save_preferences')
def test_update_preferences_logic(mock_save):
    # Setup: A mix of approved and non-approved senders
    approved_senders = ["boss@work.com"]
    rule_map = {
        1: {"sender": "boss@work.com", "decision": "keep"},
        2: {"sender": "spam@ads.com", "decision": "delete"} # Should be ignored
    }

    # Execute
    update_preferences(approved_senders, rule_map)

    # Assert: Ensure save_preferences was called ONLY for the boss
    # Note: Remember the order is (docs, ids) in your vectordb.py
    expected_rule = ["User has confirmed they want to keep all emails from boss@work.com."]
    expected_id = ["confirmed_boss@work.com"]
    
    mock_save.assert_called_once_with(expected_rule, expected_id)

def test_update_preferences_empty_case():
    with patch('postgres.vectordb_manager.save_preferences') as mock_save:
        # Execute with no matches
        update_preferences(["none@none.com"], {1: {"sender": "test@test.com"}})
        
        # Assert: save_preferences should NEVER be called
        mock_save.assert_not_called()