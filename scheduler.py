"""
Scheduler: Runs the YouTube Automation pipeline multiple times daily.
Persists daily schedule to avoid re-randomizing and ensures exactly N videos/day.
"""

import os
import sys
import time
import datetime
import random
import argparse
import subprocess
import logging
import threading
from dotenv import load_dotenv
from modules.trigger_listener import EmailTriggerListener

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load config
load_dotenv()
DAILY_COUNT = 3  # Fixed to 3 videos per day: 7:00, 13:00, 19:00 IST
NOTIFICATION_EMAILS = ["hariiicodez@hmail.com", "hariompatel3369@gmail.com"]

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"scheduler_{datetime.date.today().isoformat()}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scheduler")


class DailyScheduler:
    def __init__(self):
        self.schedule = []
        self.current_date = datetime.date.today()
        self.generate_schedule()

    def generate_schedule(self):
        """Generate fixed schedule times: 7 AM, 1 PM, 7 PM IST."""
        self.schedule = []
        now = datetime.datetime.now()
        
        # Fixed hours: 7 AM, 1 PM (13:00), 7 PM (19:00)
        fixed_hours = [7, 13, 19]

        for hour in fixed_hours:
            scheduled_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            self.schedule.append(scheduled_time)
            
        logger.info(f"📅 Daily Schedule for {self.current_date}: {[t.strftime('%H:%M') for t in self.schedule]}")

    def get_next_run(self):
        """Get the next scheduled run time.
           If all runs for today are done, returns None (signal to wait for tomorrow).
        """
        # If date changed, refresh schedule
        if datetime.date.today() != self.current_date:
            self.current_date = datetime.date.today()
            self.generate_schedule()

        now = datetime.datetime.now()
        # Find first future scheduled time
        for t in self.schedule:
            if t > now:
                return t
        
        return None  # No more runs today


def run_pipeline(triggered_by=None):
    """Execute the full YouTube Shorts pipeline with auto-upload."""
    logger.info("=" * 60)
    logger.info(f"🎬 Starting Automation Pipeline... {'(Triggered by ' + triggered_by + ')' if triggered_by else ''}")
    logger.info("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, "main.py")

    try:
        # Increase timeout to 30 mins for longer videos
        result = subprocess.run(
            [sys.executable, main_py, "--auto"],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=1800, 
        )

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                logger.info(f"  {line}")

        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                logger.warning(f"  {line}")

        success = (result.returncode == 0)
        
        # Send notifications
        listener = EmailTriggerListener()
        status_emoji = "✅" if success else "❌"
        subject = f"YouTube Automation: Video Upload {status_emoji}"
        
        # Capture Video ID/Link from stdout if successful
        video_link = "Check YouTube Channel"
        if success and "URL: " in result.stdout:
            for line in result.stdout.split("\n"):
                if "URL: " in line:
                    video_link = line.split("URL: ")[1].strip()

        body = f"The pipeline has finished.\n\nStatus: {'SUCCESS' if success else 'FAILED'}\nVideo: {video_link}\n\nTime: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 1. Notify the trigger sender if applicable
        if triggered_by:
            listener.send_reply(triggered_by, subject, body)
            
        # 2. Notify the master notification emails
        for email_addr in NOTIFICATION_EMAILS:
            if email_addr != triggered_by: # Avoid double sending
                listener.send_reply(email_addr, subject, body)

        if success:
            logger.info("✅ Pipeline completed successfully!")
            return True
        else:
            logger.error(f"❌ Pipeline exited with code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("❌ Pipeline timed out after 30 minutes!")
        return False
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}")
        return False


def start_trigger_thread():
    """Start listening for 'upload new video' emails in background."""
    def _listener_loop():
        listener = EmailTriggerListener()
        if not listener.connect():
            logger.warning("Email trigger inactive (check credentials).")
            return

        logger.info("📧 Email Trigger Active: Listening for 'upload new video'...")
        while True:
            try:
                triggered, sender = listener.check_for_trigger()
                if triggered:
                    logger.info(f"📧 Trigger received from {sender}!")
                    listener.send_reply(sender, "Video Generation Started", "I'm on it! Creating a new video now...")
                    
                    # Run pipeline (it will send its own completion email now)
                    run_pipeline(triggered_by=sender)
                
            except Exception as e:
                logger.error(f"Trigger listener error: {e}")
            
            time.sleep(60) # check every minute

    t = threading.Thread(target=_listener_loop, daemon=True)
    t.start()


def main():
    parser = argparse.ArgumentParser(description="YouTube Automation Scheduler")
    parser.add_argument("--once", action="store_true", help="Run once immediately")
    args = parser.parse_args()

    logger.info("🕐 Scheduler Started")
    logger.info(f"   Daily Goal: {DAILY_COUNT} videos (Fixed at 7:00, 13:00, 19:00)")

    # Start email trigger listener
    start_trigger_thread()

    if args.once:
        run_pipeline()
        return

    scheduler = DailyScheduler()

    while True:
        try:
            next_run = scheduler.get_next_run()
            now = datetime.datetime.now()

            if next_run:
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"⏳ Next run at {next_run.strftime('%H:%M')} (in {wait_seconds/3600:.1f} hours)")
                
                # Sleep in chunks to allow interruption
                while wait_seconds > 0:
                    sleep_time = min(60, wait_seconds) # Check every minute
                    time.sleep(sleep_time)
                    wait_seconds -= sleep_time
                    # If date changed or reached target time, break
                    if datetime.date.today() != scheduler.current_date or datetime.datetime.now() >= next_run:
                        break
                
                # Check if we still want to run (date might have changed)
                if datetime.datetime.now() >= next_run and datetime.date.today() == scheduler.current_date:
                    logger.info(f"🚀 Launching pipeline at {datetime.datetime.now().strftime('%H:%M')}")
                    run_pipeline()
                    # Prevent double triggering
                    time.sleep(60)
            
            else:
                # No more runs today — wait until tomorrow morning 7 AM
                tomorrow = now + datetime.timedelta(days=1)
                next_start = tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)
                wait_seconds = (next_start - now).total_seconds()
                
                logger.info(f"💤 All tasks done for today. Sleeping until {next_start.strftime('%Y-%m-%d %H:%M')}")
                # Sleep in chunks to allow interruption
                while wait_seconds > 0:
                    sleep_time = min(3600, wait_seconds) # Sleep max 1 hour at a time
                    time.sleep(sleep_time)
                    wait_seconds -= sleep_time
                    # Check if date rolled over to trigger refresh
                    if datetime.date.today() != scheduler.current_date:
                        break

        except KeyboardInterrupt:
            logger.info("\n🛑 Scheduler stopped by user.")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
