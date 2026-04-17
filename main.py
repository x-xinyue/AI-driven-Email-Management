import sys
from processor import process_emails

if __name__ == "__main__":
    # To run for real: python main.py --execute
    execute_mode = "--execute" in sys.argv
    
    if not execute_mode:
        print("🛡️  DRY RUN ACTIVE (No DB changes or Unsub requests will be sent)")
    else:
        print("💥 LIVE MODE ACTIVE (DB will be updated)")

    process_emails(dry_run=not execute_mode)
