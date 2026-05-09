"""
Routes email action based on its type:
1. Instant actions
2. Actions subject to user's approval
"""
from core.executor import execute_actions
from postgres.db_manager import store_pending_action


def route_action(action):
    category = action["category"].lower()
    
    if category in ['job_hunt', 'career', 'transactional']:
        action["action_type"] = "instant"
        return execute_actions([action])

    else:  # Promotional/Review emails
        action["action_type"] = "approval"
        return store_pending_action(action)
