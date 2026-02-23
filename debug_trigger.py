from modules.trigger_listener import EmailTriggerListener
import os

def check_trigger_status():
    print("Checking Email Trigger status...")
    listener = EmailTriggerListener()
    
    if not listener.connect():
        print("X Failed to connect to Gmail. Check credentials and App Password.")
        return

    print("Success: Connected to Gmail successfully.")
    
    try:
        listener.imap.select("INBOX")
        # Search for all emails with the subject (including seen ones for debugging)
        status, messages = listener.imap.search(None, '(SUBJECT "upload new video")')
        
        if status != "OK":
            print("Error searching for emails.")
            return

        if not messages[0]:
            print("No emails found with subject 'upload new video'.")
            print("Make sure the subject is exactly 'upload new video' (case-insensitive usually).")
        else:
            ids = messages[0].split()
            print(f"Found {len(ids)} email(s) with the trigger subject.")
            
            # Check for unseen ones specifically
            status, unseen_messages = listener.imap.search(None, '(UNSEEN SUBJECT "upload new video")')
            if unseen_messages[0]:
                unseen_ids = unseen_messages[0].split()
                print(f"Trigger found: Found {len(unseen_ids)} UNREAD trigger email(s).")
            else:
                print("Info: No UNREAD trigger emails found.")

    except Exception as e:
        print(f"Error during check: {e}")

if __name__ == "__main__":
    check_trigger_status()
