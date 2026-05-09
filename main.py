import streamlit as st
import json

from postgres.db_manager import get_pending_actions, approve_action, reject_action
from collections import defaultdict
from core.executor import execute_actions
from postgres.vectordb_manager import update_preferences
from core.processor import process_emails

# ----------------------------
# Database State Management
# ----------------------------
def load_pending_grouped_actions():
    rows = get_pending_actions()
    grouped = defaultdict(list)

    for row in rows:
        action_data = row[7]
        group_key = (action_data.get('sender'), action_data.get('decision'))
        grouped[group_key].append(action_data)  # ("abc123@email.com", "delete"): [email_id1, email_id2...]

    return grouped


if "approved_count" not in st.session_state:
    st.session_state.approved_count = 0
if "rejected_count" not in st.session_state:
    st.session_state.rejected_count = 0

grouped_actions = load_pending_grouped_actions()


# ----------------------------
# Header
# ----------------------------
st.title("Welcome Xin Yue :grin:")
st.subheader(f"You have {len(grouped_actions)} actions to review")


# ----------------------------
# Action Handling
# ----------------------------
def handle_approval(sender, decision, actions):
    execute_actions(actions)

    action_ids = [a.get('action_id', a.get('id')) for a in actions]
    rule_map = {1: {"sender": sender, "decision": decision, "ids": action_ids}}
    update_preferences([sender], rule_map)

    for action_id in action_ids:
        approve_action(action_id)
    
    st.session_state.approved_count += 1


def handle_rejection(actions):
    for action in actions:
        action['decision'] = "keep"
    execute_actions(actions)

    for action in actions:
        action_id = action.get('action_id', action.get('id'))
        reject_action(action_id)
    
    st.session_state.rejected_count += 1


# ----------------------------
# Action Cards
# ----------------------------
for (sender, decision), actions in grouped_actions.items():
    with st.container():
        st.markdown("---")
        st.markdown(f"### Always **{decision.upper()}** emails from: {sender}")
        st.caption(f"{len(actions)} emails found (e.g., '{actions[0]['subject']}')")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("Approve Rule", key=f"approve_{sender}_{decision}"):
                handle_approval(sender, decision, actions)
                st.rerun()

        with col2:
            if st.button("Reject (Keep Emails)", key=f"reject_{sender}_{decision}"):
                handle_rejection(actions)
                st.rerun()


# ----------------------------
# Output summary
# ----------------------------
st.markdown("---")
st.success(f"{st.session_state.approved_count} rules approved! {st.session_state.rejected_count} rules rejected!")

batch_size = st.number_input("Batch Size", min_value=1, value=10)

if st.button("Run Manual Batch"):
    with st.spinner("Agent is fetching new emails..."):
        process_emails(n=batch_size)
        st.success("Batch Complete!")
        st.rerun()

# --- THE AUTOMATED ENDPOINT (For Google Cloud Scheduler) ---
if "mode" in st.query_params and st.query_params["mode"] == "auto":
    process_emails(n=20)
    st.write("Automated Batch Processed via Scheduler.")
