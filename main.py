import streamlit as st
import time

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
st.title("Welcome Xin Yue!")


# ----------------------------
# Manual Email Processing
# ----------------------------
st.subheader("✉ Email Processing Centre")

batch_col, run_col = st.columns([1, 2], vertical_alignment="bottom")

with batch_col:
    batch_size = st.number_input("Batch Size", min_value=1, value=5)

with run_col:
    run_button = st.button(label="▶ Run Batch", use_container_width=True)

    if run_button:
        with st.spinner("Agent is running..."):
            # Capture the stats returned by the processor
            summary = process_emails(n=batch_size)
            
            if summary and summary["processed"] > 0:
                st.success(f"✅ Processed {summary['processed']} emails!")
                
                # Use columns or metrics to show the breakdown
                col1, col2 = st.columns(2)
                col1.metric("Automated Actions", summary["instant"])
                col2.metric("Sent to Review", summary["approved"])
                
                if summary["instant"] > 0:
                    st.toast(f"Executed {summary['instant']} instant actions (Labels/Sheets)")
            else:
                st.warning("No new emails found to process.")
                
            # Give the user a moment to see the stats before rerunning
            time.sleep(2) 
            st.rerun()


# ----------------------------
# Action Review Section
# ----------------------------
st.divider()
st.subheader("⚙ Actions Review Centre")

num_of_actions = len(grouped_actions)
st.write(f"You have **{num_of_actions}** action{'s' if num_of_actions != 1 else ''} to review...")


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
    with st.container(border=True):
        left, approve_col, reject_col = st.columns([4.5, 1.5, 1.5])

        with left:
            st.write(f"Always **{decision.upper()}** emails from:  \n*{sender}*")

            num_of_emails = len(actions)
            avg_confidence_score = sum(action['confidence_score'] for action in actions) / len(actions)
            first_reason = actions[0].get('reason', 'No reason provided')
            st.caption(
                f"{num_of_emails} email{'s' if num_of_emails != 1 else ''} found  \n"
                f"AI confidence (overall): {avg_confidence_score:.0%}  \n"
                f"Reason: {first_reason}"
            )

        with approve_col:
            approve_button = st.button(
                label="✓ Approve",
                key=f"approve_{sender}_{decision}",
                use_container_width=True
            )

            if approve_button:
                handle_approval(sender, decision, actions)
                st.rerun()

        with reject_col:
            reject_button = st.button(
                label="✕ Reject",
                key=f"reject_{sender}_{decision}",
                use_container_width=True
            )

            if reject_button:
                handle_rejection(actions)
                st.rerun()
        
        with st.expander("View affected emails"):
            for action in actions[:3]:
                st.write(f"• {action['subject']}")


# ----------------------------
# Action Output Summary
# ----------------------------
st.success(
        f"{st.session_state.approved_count} rule{'s' if st.session_state.approved_count != 1 else ''} approved. "
        f"{st.session_state.rejected_count} rule{'s' if st.session_state.rejected_count != 1 else ''} rejected."
    )
