import os
import sys
import subprocess
import datetime
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from scheduler import run_pipeline

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Status tracking
status = {
    "is_running": False,
    "last_run": "Never",
    "last_result": "N/A",
    "logs": []
}

def log_to_dashboard(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    status["logs"].append(f"[{timestamp}] {message}")
    if len(status["logs"]) > 50:
        status["logs"].pop(0)

def background_video_generation():
    status["is_running"] = True
    log_to_dashboard("🚀 Starting manual video generation...")
    
    success = run_pipeline()
    
    status["is_running"] = False
    status["last_run"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status["last_result"] = "✅ Success" if success else "❌ Failed"
    log_to_dashboard(f"Pipeline finished: {status['last_result']}")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "status": status})

@app.post("/generate")
async def generate(background_tasks: BackgroundTasks):
    if status["is_running"]:
        return {"message": "Already running!"}
    
    background_tasks.add_task(background_video_generation)
    return {"message": "Generation started in background!"}

@app.get("/status")
async def get_status():
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
