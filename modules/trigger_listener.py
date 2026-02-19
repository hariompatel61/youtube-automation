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
        """Check for unread emails with subject 'upload new video'.
           Returns: True if trigger found, sender_email if found.
        """
        if not self.imap:
            if not self.connect():
                return False, None

        try:
            self.imap.select("INBOX")
            # Search for unread emails with specific subject
            status, messages = self.imap.search(None, '(UNSEEN SUBJECT "upload new video")')
            
            if status != "OK" or not messages[0]:
                return False, None

            # Process the first matching email
            email_ids = messages[0].split()
            latest_id = email_ids[-1]
            
            # Fetch the email
            res, msg_data = self.imap.fetch(latest_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    sender = msg.get("From")
                    return True, sender

        except Exception as e:
            print(f"⚠️ Email check error: {e}")
            # Reconnect usually fixes socket errors
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
