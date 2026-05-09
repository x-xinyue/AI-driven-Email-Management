import pytest
from unittest.mock import patch, MagicMock
from llm.llm_engine import get_llm_decision

# Intercept the exact path where the Gemini client is called
@patch('llm.llm_engine.client.models.generate_content')
def test_get_llm_decision_job_hunt(mock_generate_content):
    # 1. SETUP: Create a fake API response
    mock_response = MagicMock()
    
    # We simulate the dictionary that your modified code now expects
    mock_response.parsed = {
        "category": "job_hunt",
        "decision": "keep",
        "reason": "It is an interview invitation.",
        "confidence_score": 0.98,
        "company_name": "Shopee",
        "job_role": "Data Product Operations",
        "status_update": "Interviewing"
    }
    mock_generate_content.return_value = mock_response

    # 2. INPUT: Provide the fake email data
    email_data = {
        'sender': 'recruitment@shopee.com',
        'subject': 'Shopee Assessment: Data Product Operations',
        'body_snippet': 'Congratulations, you have been selected for the live business problem round. Please prepare a calculator, pen, and paper.'
    }
    user_pref = "No specific preference found."

    # 3. EXECUTE: Run your actual function
    result = get_llm_decision(email_data, user_pref)

    # 4. ASSERT: Did it behave exactly as expected?
    assert result['category'] == 'job_hunt'
    assert result['company_name'] == 'Shopee'
    assert result['status_update'] == 'Interviewing'
    
    # Verify that we actually triggered our mock and didn't accidentally bypass it
    mock_generate_content.assert_called_once()