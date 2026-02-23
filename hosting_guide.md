# Free Hosting Guide: YouTube Automation

Since the video generation requires Python and all your dependencies, you need a "Web Service" host rather than a static one like GitHub Pages.

## 🚀 Option 1: Render (Recommended)
Render has a very generous free tier and is easy to set up.

1. **GitHub Link**: Link your GitHub repository to Render.
2. **New Web Service**: Create a new "Web Service".
3. **Settings**:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py` (for the dashboard)
4. **Environment Variables**: Go to the "EnvVars" tab and add all the keys from your `.env` file (like `BYTEZ_API_KEY`, `EMAIL_USER`, etc.).

---

## 🚂 Option 2: Railway
Railway is ultra-fast but has a 500-hour/month limit on the free trial.

1. Create a new Project and select "Deploy from GitHub".
2. It will automatically detect the Python environment.
3. Add your EnvVars in the "Variables" tab.

---

## 📂 Important: File Persistence
Free servers use "Ephemeral Storage". This means:
- **Generated Videos**: They will delete themselves when the server restarts (usually once a day).
- **Solution**: Since the system uploads them to YouTube immediately, this is usually NOT a problem. Your videos will be safe on YouTube!
- **Logs**: Your `content_log.xlsx` and `processed_emails.txt` might be reset. If you need to keep them forever, you would need a "Volume" (usually paid) or a database.

---

## 🕐 What about the Scheduler?
On a server, you have two ways to keep the scheduler running:
1. **The Web App**: Since `app.py` imports `run_pipeline`, the code is there.
2. **Background Thread**: I have already added `start_trigger_thread()` to the dashboard's background logic.
3. **Automatic Cron**: You can use Render's "Cron Job" (paid) or simply keep the Web Service running.

**Note**: Most free servers "sleep" if nobody visits the website. To keep the scheduler awake, you can use a free service like [cron-job.org](https://cron-job.org) to ping your `http://your-app.onrender.com` URL every 10 minutes.
