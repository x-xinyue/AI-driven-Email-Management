import sqlite3
import requests


def execute_actions(actions, dry_run):
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()

    for action in actions:
        if action['decision'] == 'keep':
            cursor.execute("UPDATE emails SET status = 'KEPT' WHERE id = ?", (action['id'],))
            continue

        if dry_run:
            print(f"[DRY RUN] Would {action['decision']} ID {action['id']}")
            continue

        # TRASH LOGIC
        if action['decision'] in ['delete', 'unsubscribe']:
            cursor.execute("UPDATE emails SET status = 'TRASHED' WHERE id = ?", (action['id'],))
            print(f"✅ ID {action['id']} moved to trash.")

        # UNSUBSCRIBE LOGIC
        if action['decision'] == 'unsubscribe' and action['unsubscribe_url']:
            try:
                # Be careful: some links require a POST, but most work with a GET
                r = requests.get(action['unsubscribe_url'], timeout=5)
                if r.status_code < 400:
                    print(f"🔕 Successfully hit unsubscribe for {action['sender']}")
                else:
                    print(f"⚠️ Unsubscribe link for {action['sender']} returned status {r.status_code}")
            except Exception as e:
                print(f"❌ Failed to unsubscribe from {action['sender']}: {e}")

    conn.commit()
    conn.close()
    print("\nProcessing Complete.")