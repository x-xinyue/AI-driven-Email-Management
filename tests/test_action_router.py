import pytest
from unittest.mock import patch
from core.action_router import route_action

# Intercept the execution and storage functions
@patch('core.action_router.execute_actions')
@patch('core.action_router.store_pending_action')
def test_route_action_instant_execution(mock_store, mock_execute):
    # 1. SETUP & INPUT: An action that should be executed instantly
    action = {
        "id": "msg_123",
        "category": "career",
        "decision": "keep",
        "subject": "New AI frameworks released"
    }
    
    # 2. EXECUTE
    route_action(action)
    
    # 3. ASSERT
    assert action["action_type"] == "instant"
    
    # Ensure it went to the executor, NOT the database
    mock_execute.assert_called_once_with([action])
    mock_store.assert_not_called()

@patch('core.action_router.execute_actions')
@patch('core.action_router.store_pending_action')
def test_route_action_pending_approval(mock_store, mock_execute):
    # 1. SETUP & INPUT: A marketing email that needs human review
    action = {
        "id": "msg_456",
        "category": "promotional",
        "decision": "unsubscribe",
        "subject": "Buy these new shoes!"
    }
    
    # 2. EXECUTE
    route_action(action)
    
    # 3. ASSERT
    assert action["action_type"] == "approval"
    
    # Ensure it went to the database, NOT the executor
    mock_store.assert_called_once_with(action)
    mock_execute.assert_not_called()