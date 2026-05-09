import pytest

from unittest.mock import patch, MagicMock
from postgres.db_manager import store_pending_action, get_pending_actions, approve_action

@patch('postgres.db_manager.psycopg.connect')
def test_store_pending_action(mock_connect):
    # Setup mock database connection and cursor
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_connect.return_value = mock_conn

    # Input data
    action = {
        "action_id": "msg_123",
        "sender": "newsletter@brand.com",
        "subject": "Weekly Update",
        "decision": "delete",
        "category": "promotional",
        "reason": "Marketing spam",
        "confidence_score": 0.95
    }

    # Execute
    store_pending_action(action)

    # Assert the SQL execute was called and committed
    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch('postgres.db_manager.psycopg.connect')
def test_get_pending_actions(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_connect.return_value = mock_conn

    # Fake database returning one row
    mock_cur.fetchall.return_value = [
        ("msg_123", "newsletter@brand.com", "Weekly Update", "delete", "promotional", "Marketing spam", 0.95, "{}")
    ]

    rows = get_pending_actions()
    
    assert len(rows) == 1
    assert rows[0][0] == "msg_123"