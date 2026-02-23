"""
Configuration module for YouTube Automation Pipeline.
Loads settings from .env file and provides defaults.
Supports dynamic video duration (30s–5min) based on story complexity.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration for the entire pipeline."""

    # ── LLM Settings ─────────────────────────────────────────
    # Provider: "bytez" (125+ models), "groq" (fast cloud), "ollama" (local), "gemini" (google)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bytez")

    # Bytez (125+ models, cloud API)
    BYTEZ_API_KEY = os.getenv("BYTEZ_API_KEY", "")
    BYTEZ_MODEL = os.getenv("BYTEZ_MODEL", "Qwen/Qwen3-4B")

    # Groq (fast, free cloud)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Ollama (local fallback)
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

    # Gemini (Google free tier)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Dynamic model selection based on provider
    @classmethod
    def _get_llm_model(cls):
        if cls.LLM_PROVIDER == "bytez":
            return cls.BYTEZ_MODEL
        elif cls.LLM_PROVIDER == "groq":
            return cls.GROQ_MODEL
        elif cls.LLM_PROVIDER == "ollama":
            return cls.OLLAMA_MODEL
        elif cls.LLM_PROVIDER == "gemini":
            return cls.GEMINI_MODEL
        return cls.BYTEZ_MODEL

    # Resolve LLM_MODEL at module load time
    LLM_MODEL = os.getenv("LLM_MODEL", "")

    # ── Image Generation Settings ─────────────────────────────
    # Provider: "pollinations" (free AI), "pillow" (simple 2D)
    IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "pollinations")
    POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "flux")  # flux, turbo

    # High-quality 3D Animation Prompt Template
    SCENE_PROMPT_TEMPLATE = (
        "High quality 3D render of {scene_description}. "
        "Style: Disney Pixar and DreamWorks animated movie, ultra detailed, cinematic lighting, "
        "volumetric fog, 8k resolution, Unreal Engine 5 render. "
        "Characters: {characters}. Expression: {expression}. "
        "Composition: {camera_angle}, vertical 9:16 aspect ratio. "
        "Colors: vivid, vibrant, studio lighting. "
        "Negative prompt: low quality, 2d, sketch, drawing, bad anatomy, blurry, watermark, text."
    )

    # Children's 3D Animated Video Scene Prompt — Pixar/DreamWorks quality
    CHILDREN_SCENE_PROMPT = (
        "Ultra high quality 3D render, Pixar animated movie style, "
        "8K cinematic rendering, Unreal Engine 5 quality, volumetric lighting. "
        "Scene: {scene_description}. "
        "Characters: {characters}. Expression: {expression}. Action: {action}. "
        "Style details: big expressive cartoon eyes, smooth skin, vibrant saturated colors, "
        "soft subsurface scattering, global illumination, rim lighting, depth of field blur on background. "
        "Camera: {camera_angle}, vertical 9:16 aspect ratio, centered composition. "
        "Background: richly detailed, colorful, child-friendly environment. "
        "Mood: joyful, magical, wonder-filled, safe for kids. "
        "Negative prompt: adult content, dark, scary, violence, text, watermark, low quality, "
        "blurry, 2D, flat, sketch, bad anatomy, deformed faces, realistic human."
    )

    # Child-friendly voice for children's videos (Microsoft edge-tts)
    CHILDREN_NARRATOR_VOICE = os.getenv("CHILDREN_NARRATOR_VOICE", "en-US-AriaNeural")
    CHILDREN_CHARACTER_VOICE = os.getenv("CHILDREN_CHARACTER_VOICE", "en-US-GuyNeural")

    # ── API Keys ──────────────────────────────────────────────
    YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")

    # ── Video Settings (Dynamic Duration) ────────────────────
    VIDEO_DURATION_MIN = int(os.getenv("VIDEO_DURATION_MIN", "30"))   # Shortest video (seconds)
    VIDEO_DURATION_MAX = int(os.getenv("VIDEO_DURATION_MAX", "300"))  # Longest video (seconds)
    VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", "60"))  # Fallback default
    VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
    VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", "24"))

    # ── Voice Settings ────────────────────────────────────────
    NARRATOR_VOICE = os.getenv("NARRATOR_VOICE", "en-US-GuyNeural")
    CHARACTER_VOICE_MALE = os.getenv("CHARACTER_VOICE_MALE", "en-US-ChristopherNeural")
    CHARACTER_VOICE_FEMALE = os.getenv("CHARACTER_VOICE_FEMALE", "en-US-JennyNeural")

    # ── Upload Settings ───────────────────────────────────────
    YOUTUBE_CATEGORY = os.getenv("YOUTUBE_CATEGORY", "24")  # 24 = Entertainment
    MADE_FOR_KIDS = os.getenv("MADE_FOR_KIDS", "false").lower() == "true"
    PLAYLIST_ID = os.getenv("PLAYLIST_ID", "")
    SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "")

    # ── Scheduler Settings ────────────────────────────────────
    DAILY_VIDEO_COUNT = int(os.getenv("DAILY_VIDEO_COUNT", "4"))
    SCHEDULE_START_HOUR = int(os.getenv("SCHEDULE_START_HOUR", "5"))   # 5 AM IST
    SCHEDULE_END_HOUR = int(os.getenv("SCHEDULE_END_HOUR", "23"))     # 11 PM IST

    # ── Paths ─────────────────────────────────────────────────
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
    MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
    SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")

    # ── Content Settings (New Themes) ─────────────────────────
    TOPIC_CATEGORIES = [
        # Animals with real-life problems
        "animals dealing with human problems (paying rent, job interviews, cooking disasters)",
        "pet adventures and mischief",
        "animals in strange situations (cat CEO, dog doctor, fish astronaut)",

        # Robots and kids
        "robots building things and playing with children",
        "kid teaches a robot about feelings and emotions",
        "robot pet that malfunctions in funny ways",

        # Comedy-tech
        "AI and technology gone hilariously wrong",
        "science experiments that cause chaos",
        "smart home devices rebelling against their owners",

        # Classic comedy
        "funny daily life situations",
        "school comedy",
        "office humor with a tech twist",
    ]

    @classmethod
    def get_duration_settings(cls, duration_seconds):
        """Get script and scene settings scaled to the chosen video duration.

        Args:
            duration_seconds: Target video length in seconds (30–300).

        Returns:
            dict with min_words, max_words, min_scenes, max_scenes.
        """
        # Clamp to valid range
        dur = max(cls.VIDEO_DURATION_MIN, min(cls.VIDEO_DURATION_MAX, duration_seconds))

        # ~2.5 words per second for natural speech pace
        words_per_sec = 2.5
        max_words = int(dur * words_per_sec)
        min_words = int(max_words * 0.85)  # Allow 15% flexibility

        # ~1 scene per 8-10 seconds
        min_scenes = max(3, int(dur / 10))
        max_scenes = max(5, int(dur / 7))

        return {
            "duration": dur,
            "min_words": min_words,
            "max_words": max_words,
            "min_scenes": min_scenes,
            "max_scenes": max_scenes,
        }

    # Legacy settings (backward compat — used when no dynamic duration)
    MAX_SCRIPT_WORDS = 100
    MIN_SCRIPT_WORDS = 80
    SCENE_COUNT_MIN = 5
    SCENE_COUNT_MAX = 7

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        errors = []

        provider = cls.LLM_PROVIDER

        if provider == "bytez":
            if not cls.BYTEZ_API_KEY or cls.BYTEZ_API_KEY == "your_bytez_api_key_here":
                errors.append("BYTEZ_API_KEY not set. Get your key at https://bytez.com/api")

        elif provider == "groq":
            if not cls.GROQ_API_KEY:
                errors.append("GROQ_API_KEY not set. Get free key at https://console.groq.com")
            else:
                try:
                    import requests
                    headers = {
                        "Authorization": f"Bearer {cls.GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    }
                    r = requests.get(
                        "https://api.groq.com/openai/v1/models",
                        headers=headers,
                        timeout=10,
                    )
                    if r.status_code != 200:
                        errors.append(f"Groq API returned status {r.status_code}")
                except Exception as e:
                    errors.append(f"Cannot connect to Groq: {e}")

        elif provider == "ollama":
            try:
                import requests
                r = requests.get(f"{cls.OLLAMA_URL}/api/tags", timeout=5)
                if r.status_code != 200:
                    errors.append(f"Ollama not responding at {cls.OLLAMA_URL}")
                else:
                    models = [m['name'] for m in r.json().get('models', [])]
                    model = cls.OLLAMA_MODEL
                    if not any(model in m for m in models):
                        errors.append(f"Model '{model}' not found. Run: ollama pull {model}")
            except Exception:
                errors.append(f"Cannot connect to Ollama at {cls.OLLAMA_URL}")

        elif provider == "gemini":
            if not cls.GEMINI_API_KEY:
                errors.append("GEMINI_API_KEY not set. Get free key at https://ai.google.dev")

        return errors

    @classmethod
    def ensure_directories(cls):
        """Create all required directories."""
        for directory in [cls.ASSETS_DIR, cls.FONTS_DIR, cls.MUSIC_DIR,
                          cls.SFX_DIR, cls.OUTPUT_DIR]:
            os.makedirs(directory, exist_ok=True)
