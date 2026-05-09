import pytest
from unittest.mock import patch
from core.processor import process_emails

# We have to mock everything external so the test runs instantly and locally
@patch('core.processor.route_action')
@patch('core.processor.get_llm_decision')
@patch('core.processor.find_relevant_preference')
@patch('core.processor.fetch_emails')
@patch('core.processor.get_gmail_service')
def test_process_emails_success_path(mock_get_gmail, mock_fetch, mock_find_pref, mock_llm, mock_route):
    
    # 1. Mock Gmail fetching a relevant job hunt email
    mock_fetch.return_value = [{
        'id': 'msg_789',
        'sender': 'recruitment@shopee.com',
        'subject': 'Shopee Assessment: Data Product Operations',
        'body_snippet': 'Congratulations, please complete this technical assessment...',
        'unsubscribe_url': None
    }]

    # 2. Mock LangChain finding a rule
    mock_find_pref.return_value = "Always keep emails regarding job applications."

    # 3. Mock Gemini categorizing it correctly
    mock_llm.return_value = {
        "category": "job_hunt",
        "decision": "keep",
        "reason": "Technical assessment link.",
        "confidence_score": 0.99
    }

    # Execute the batch processor
    process_emails(n=1)

    # Assertions
    mock_fetch.assert_called_once()
    mock_find_pref.assert_called_once()
    mock_llm.assert_called_once()
    
    # Verify the router was called with the perfectly constructed dictionary
    mock_route.assert_called_once()
    
    routed_action = mock_route.call_args[0][0] # Grab the dictionary passed to route_action
    assert routed_action['id'] == 'msg_789'
    assert routed_action['category'] == 'job_hunt'
    assert routed_action['decision'] == 'keep'