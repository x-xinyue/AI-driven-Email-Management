import time
from processor import process_emails

if __name__ == "__main__":
    # 1. Total emails to handle
    TARGET_TOTAL = 20 
    BATCH_SIZE = 10
    
    print("🚀 Astra is starting the Great Inbox Drain...")
    
    processed_count = 0
    try:
        while processed_count < TARGET_TOTAL:
            print(f"\n--- Starting Batch: {processed_count + 1} to {processed_count + BATCH_SIZE} ---")
            
            # This will fetch 20, classify, ask for confirmation on promos, and execute.
            # It returns the list of actions taken.
            actions = process_emails(n=BATCH_SIZE)
            
            if not actions and processed_count > 0:
                print("🏁 No more emails found in INBOX. Mission accomplished!")
                break
                
            processed_count += BATCH_SIZE
            
            # 2. Rate Limit Safety (Gemini Free Tier is 15 RPM)
            # Your process_emails already has some sleep, but a 10s gap 
            # between batches helps keep the Google APIs happy.
            print(f"⏳ Batch complete. Total processed: ~{processed_count}. Cooling down...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user. Exiting gracefully...")
