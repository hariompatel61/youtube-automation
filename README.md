# 🎬 YouTube Shorts Comedy Cartoon Automation

Fully automated pipeline that generates comedy cartoon YouTube Shorts — from topic idea to final upload.

## ✨ Features

| Step | What It Does |
|------|-------------|
| 1️⃣ Topic Generation | AI generates viral comedy story ideas |
| 2️⃣ Script Writing | 30-second script with hook + twist |
| 3️⃣ Storyboard | 5-7 scene breakdown with visual directions |
| 4️⃣ Cartoon Scenes | Generates colorful cartoon images |
| 5️⃣ Voiceover | Expressive text-to-speech per character |
| 6️⃣ Music & SFX | Comedy background music + cartoon sounds |
| 7️⃣ Video Assembly | Final 1080×1920 vertical video |
| 8️⃣ SEO Metadata | Viral title, description, tags |
| 9️⃣ Thumbnail | Eye-catching 1280×720 thumbnail |
| 🔟 YouTube Upload | Auto-upload with metadata & thumbnail |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy the example env file
copy .env.example .env

# Edit .env and add your Gemini API key
# Get one free at https://ai.google.dev
```

### 3. Run the Pipeline

```bash
# Generate a video (no upload)
python main.py

# Use a custom topic
python main.py --topic "cat secretly ordering pizza"

# Full pipeline including YouTube upload
python main.py --auto

# Run specific steps only
python main.py --steps 1,2,3

# Validate setup
python main.py --dry-run
```

## 📁 Output Structure

Each run creates a timestamped folder in `output/`:

```
output/run_20260218_120000/
├── all_topics.json         # 5 generated topic ideas
├── selected_topic.json     # The chosen topic
├── script.json             # Full comedy script
├── storyboard.json         # Scene-by-scene breakdown
├── scenes/                 # Cartoon scene images
│   ├── scene_01.png
│   ├── scene_02.png
│   └── ...
├── voiceovers/             # Per-scene voiceover audio
│   ├── voice_01.mp3
│   └── ...
├── bgm.mp3                 # Background music
├── final_short.mp4         # ✅ The final video
├── metadata.json           # Title, description, tags
├── thumbnail.png           # YouTube thumbnail
└── upload_result.json      # Upload confirmation (if uploaded)
```

## ⚙️ Configuration

All settings are in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | *required* |
| `VIDEO_DURATION` | Video length in seconds | 30 |
| `NARRATOR_VOICE` | edge-tts voice for narrator | en-US-GuyNeural |
| `MADE_FOR_KIDS` | YouTube kids content flag | false |
| `SCHEDULE_TIME` | Schedule upload (ISO 8601) | *(immediate)* |
| `PLAYLIST_ID` | YouTube playlist to add to | *(none)* |

## 🎤 Available Voices

| Voice | Name | Style |
|-------|------|-------|
| `en-US-GuyNeural` | Guy | Male, friendly |
| `en-US-ChristopherNeural` | Christopher | Male, warm |
| `en-US-JennyNeural` | Jenny | Female, cheerful |
| `en-US-AriaNeural` | Aria | Female, professional |

## 📤 YouTube Upload Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable **YouTube Data API v3**
3. Create OAuth 2.0 credentials (Desktop App)
4. Download `client_secret.json` to the project root
5. Run `python main.py --auto` — a browser will open for authorization
6. Subsequent runs use the cached token automatically

## 🧩 Architecture

```
main.py (orchestrator)
  ├── modules/topic_generator.py    → Gemini API
  ├── modules/script_writer.py      → Gemini API
  ├── modules/storyboard.py         → Gemini API
  ├── modules/scene_generator.py    → Pillow
  ├── modules/voiceover.py          → edge-tts
  ├── modules/music_sfx.py          → pydub
  ├── modules/video_editor.py       → moviepy
  ├── modules/seo_metadata.py       → Gemini API
  ├── modules/thumbnail.py          → Pillow
  └── modules/youtube_uploader.py   → YouTube API
```
we need to chill now ❤❤
