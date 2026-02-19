"""
Step 3: Storyboard Creator
Breaks script into dynamically-scaled cartoon scenes with visual descriptions.
Supports 3–35 scenes based on video duration (30s–5min).
"""

import json
from modules.llm_client import LLMClient
from config import Config


class StoryboardCreator:
    """Creates scene-by-scene storyboard from an animated script."""

    PROMPT_TEMPLATE = """You are a storyboard artist for animated YouTube videos.

Break this script into {min_scenes}-{max_scenes} animated scenes for a {duration}-second video.

SCRIPT:
{script_text}

CHARACTERS: {characters}

For each scene provide:
1. scene_number (1-based)
2. duration_seconds - how long this scene lasts (all must total {duration} seconds)
3. description - what's happening visually (be specific about actions and movements)
4. characters_present - list of characters in this scene
5. expressions - facial expression for each character (happy, angry, surprised, shocked, laughing, crying, confused, scared)
6. background - scene setting (living_room, office, school, park, kitchen, bedroom, street, store, lab, workshop, playground, forest)
7. camera_angle - one of: wide, medium, close_up, extreme_close_up
8. dialogue - the spoken line(s) in this scene
9. speaker - who is speaking
10. sfx - any sound effect needed (boing, slap, pop, whoosh, crash, silence, laugh, beep, sparkle)

Return ONLY valid JSON array (no markdown, no code blocks):
[
  {{
    "scene_number": 1,
    "duration_seconds": 5,
    "description": "Character walks into room looking confused",
    "characters_present": ["Bob"],
    "expressions": {{"Bob": "confused"}},
    "background": "living_room",
    "camera_angle": "wide",
    "dialogue": "What happened to my lunch?",
    "speaker": "Bob",
    "sfx": "silence"
  }}
]

IMPORTANT: Scene durations MUST total exactly {duration} seconds.
"""

    def __init__(self):
        self.client = LLMClient()

    def create_storyboard(self, script):
        """Generate storyboard scenes from a script with dynamic scene count.

        Args:
            script: dict from ScriptWriter with 'script_lines', 'characters',
                    and 'target_duration'.

        Returns:
            list[dict]: Scene-by-scene storyboard.
        """
        # Get dynamic duration from script (set by topic_generator)
        duration = script.get("target_duration", Config.VIDEO_DURATION)
        settings = Config.get_duration_settings(duration)

        # Build full script text
        script_lines = script.get("script_lines", [])
        if script_lines:
            script_text = "\n".join(
                f"{line.get('speaker', 'NARRATOR')}: {line.get('line', '')}"
                for line in script_lines
            )
        else:
            script_text = script.get("hook", "A funny story")

        characters = ", ".join(script.get("characters", ["Character1", "Character2"]))

        prompt = self.PROMPT_TEMPLATE.format(
            min_scenes=settings["min_scenes"],
            max_scenes=settings["max_scenes"],
            duration=settings["duration"],
            script_text=script_text,
            characters=characters,
        )

        scenes = self.client.generate_json(prompt)

        # Handle dict response
        if isinstance(scenes, dict):
            for key in ("scenes", "storyboard", "results"):
                if key in scenes and isinstance(scenes[key], list):
                    scenes = scenes[key]
                    break
            else:
                scenes = [scenes]

        # Handle string response
        if isinstance(scenes, str):
            try:
                scenes = json.loads(scenes)
            except (json.JSONDecodeError, ValueError):
                scenes = [{"scene_number": 1, "duration_seconds": duration,
                           "description": scenes, "characters_present": [],
                           "expressions": {}, "background": "living_room",
                           "camera_angle": "wide", "dialogue": "", "speaker": "",
                           "sfx": "silence"}]

        # Ensure scene_number exists
        for i, scene in enumerate(scenes):
            if "scene_number" not in scene:
                scene["scene_number"] = i + 1

        # Validate and fix total duration
        total = sum(s.get("duration_seconds", 0) for s in scenes)
        if total != settings["duration"] and scenes:
            diff = settings["duration"] - total
            scenes[-1]["duration_seconds"] = max(1, scenes[-1].get("duration_seconds", 4) + diff)

        return scenes
