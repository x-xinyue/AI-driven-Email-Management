"""
Standard CRUD Operations
"""

import os
import psycopg
import json

from dotenv import load_dotenv


load_dotenv()


def connect_db():
    conn = psycopg.connect(os.getenv("POSTGRES_URL").replace("postgresql+psycopg://", "postgresql://"))
    return conn


def store_pending_action(action):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO pending_actions (
            action_id, sender, subject, decision, category,
            reason, confidence_score, result_data, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
        ON CONFLICT (action_id) DO NOTHING;
    """, (
        action.get("action_id"),
        action.get("sender"),
        action.get("subject"),
        action.get("decision"),
        action.get("category"),
        action.get("reason"),
        action.get("confidence_score"),
        json.dumps(action)
    ))

    conn.commit()
    cur.close()
    conn.close()


def get_pending_actions():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            action_id, sender, subject, decision, category, 
            reason, confidence_score, result_data
        FROM pending_actions
        WHERE status = 'PENDING'
        ORDER BY created_at DESC;
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


def approve_action(action_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE pending_actions
        SET status = 'APPROVED'
        WHERE action_id = %s
    """, (action_id,))

    conn.commit()
    cur.close()
    conn.close()


def reject_action(action_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE pending_actions
        SET status = 'REJECTED'
        WHERE action_id = %s
    """, (action_id,))

    conn.commit()
    cur.close()
    conn.close()


def get_past_delete_count(sender):
    """
    Counts how many times the user has approved deleting emails from this sender.
    Used to build the 'Closed-Loop Memory' for proactive unsubscribing.
    """
    conn = connect_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COUNT(*) FROM pending_actions
            WHERE sender = %s
            AND decision = 'delete'
            AND status = 'APPROVED'
        """, (sender,))
        
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        print(f"Database error in get_past_delete_count: {e}")
        return 0
    finally:
        cur.close()
        conn.close()
