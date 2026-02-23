"""
Remote Trigger Listener:
Monitors Email (IMAP) for "upload new video" commands.
"""

import os
import imaplib
import smtplib
import email
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("EMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"

class EmailTriggerListener:
    def __init__(self):
        self.imap = None
        self.last_check = None
        self.processed_ids_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_emails.txt")
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self):
        if os.path.exists(self.processed_ids_file):
            with open(self.processed_ids_file, "r") as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_processed_id(self, msg_id):
        self.processed_ids.add(msg_id)
        with open(self.processed_ids_file, "a") as f:
            f.write(f"{msg_id}\n")

    def connect(self):
        """Connect to Gmail IMAP."""
        if not GMAIL_USER or not GMAIL_PASSWORD:
            print("[X] Email credentials missing in .env (EMAIL_USER, EMAIL_PASSWORD)")
            return False
        try:
            self.imap = imaplib.IMAP4_SSL(IMAP_SERVER)
            self.imap.login(GMAIL_USER, GMAIL_PASSWORD)
            return True
        except Exception as e:
            print(f"[X] Failed to connect to Gmail: {e}")
            return False

    def check_for_trigger(self):
        """Check for emails with subject 'upload new video'.
           Returns: True if new trigger found, sender_email if found.
        """
        if not self.imap:
            if not self.connect():
                return False, None

        try:
            self.imap.select("INBOX")
            # Search for emails with specific subject (all, not just unseen)
            status, messages = self.imap.search(None, '(SUBJECT "upload new video")')
            
            if status != "OK" or not messages[0]:
                return False, None

            email_ids = messages[0].split()
            # Check from newest to oldest
            for latest_id in reversed(email_ids):
                latest_id_str = latest_id.decode()
                
                if latest_id_str in self.processed_ids:
                    continue # Already handled

                # Fetch the email
                res, msg_data = self.imap.fetch(latest_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        sender = msg.get("From")
                        
                        # Mark as processed
                        self._save_processed_id(latest_id_str)
                        return True, sender

        except Exception as e:
            print(f"⚠️ Email check error: {e}")
            self.imap = None 
            
        return False, None

    def send_reply(self, to_email, subject, body):
        """Send a reply email via SMTP."""
        if not GMAIL_USER or not GMAIL_PASSWORD:
            return

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
                smtp.login(GMAIL_USER, GMAIL_PASSWORD)
                msg = f"Subject: {subject}\n\n{body}"
                smtp.sendmail(GMAIL_USER, to_email, msg)
                print(f"📧 Reply sent to {to_email}")
        except Exception as e:
            print(f"❌ Failed to send reply: {e}")
