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
DAILY_COUNT = int(os.getenv("DAILY_VIDEO_COUNT", "4"))
START_HOUR = int(os.getenv("SCHEDULE_START_HOUR", "5"))
END_HOUR = int(os.getenv("SCHEDULE_END_HOUR", "23"))

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
        """Generate N random future times for today."""
        self.schedule = []
        now = datetime.datetime.now()
        
        # Calculate window
        start_mins = START_HOUR * 60
        end_mins = END_HOUR * 60
        window_duration = end_mins - start_mins
        
        if window_duration <= 0:
            logger.error("Invalid schedule window!")
            return

        # Generate unique random minutes
        try:
            random_minutes = sorted(random.sample(range(window_duration), DAILY_COUNT))
        except ValueError:
             # Window too small for count
            random_minutes = sorted(random.sample(range(window_duration), min(DAILY_COUNT, window_duration)))

        for m in random_minutes:
            total_minutes = start_mins + m
            hour = total_minutes // 60
            minute = total_minutes % 60
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
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


def run_pipeline():
    """Execute the full YouTube Shorts pipeline with auto-upload."""
    logger.info("=" * 60)
    logger.info("🎬 Starting Automation Pipeline...")
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

        if result.returncode == 0:
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
                    
                    success = run_pipeline()
                    
                    if success:
                        listener.send_reply(sender, "Video Uploaded ✅", "Your video is live! Check the channel.")
                    else:
                        listener.send_reply(sender, "Video Failed ❌", "Something went wrong. Check logs.")
                
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
    logger.info(f"   Daily Goal: {DAILY_COUNT} videos")
    logger.info(f"   Window: {START_HOUR}:00 - {END_HOUR}:00 IST (Local Time)")

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
                # No more runs today — wait until tomorrow start hour
                tomorrow = now + datetime.timedelta(days=1)
                next_start = tomorrow.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
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
