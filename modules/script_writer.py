"""
Step 2: Script Writer
Generates comedy/animated scripts with dynamic duration scaling.
Supports 30-second shorts to 5-minute stories.
"""

import json
from modules.llm_client import LLMClient
from config import Config


class ScriptWriter:
    """Writes animated scripts scaled to dynamic video duration."""

    PROMPT_TEMPLATE = """You are a professional animated video scriptwriter.

Write a complete script for this topic:
Title: {title}
Premise: {premise}
Humor Type: {humor_type}
Characters: {characters}
Target Duration: {duration} seconds ({duration_desc})

STRICT RULES:
1. Total word count: {min_words}-{max_words} words (for a {duration}-second video)
2. Start with a STRONG HOOK in the first line (must grab attention in 3 seconds)
3. Build a clear STORY ARC with beginning, conflict, and resolution
4. End with a FUNNY TWIST or satisfying conclusion
5. Use dialogue format with character names
6. Include NARRATOR lines for scene description and transitions
7. Keep language engaging, visual, and punchy
8. Include stage directions in parentheses for animation cues

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "hook": "The attention-grabbing first line",
  "characters": ["Character1", "Character2"],
  "script_lines": [
    {{"speaker": "NARRATOR", "line": "...", "tone": "dramatic"}},
    {{"speaker": "Character1", "line": "...", "tone": "excited"}},
    {{"speaker": "Character2", "line": "...", "tone": "confused"}}
  ],
  "conflict": "Brief description of the conflict",
  "twist": "Brief description of the twist ending",
  "total_word_count": {max_words}
}}
"""

    def __init__(self):
        self.client = LLMClient()

    def write_script(self, topic):
        """Generate an animated script from a topic with dynamic duration.

        Args:
            topic: dict with 'title', 'premise', 'humor_type', 'suggested_duration' keys.

        Returns:
            dict: Structured script with hook, lines, conflict, twist.
        """
        # Get duration from topic (fallback to config default)
        duration = topic.get("suggested_duration", Config.VIDEO_DURATION)
        settings = Config.get_duration_settings(duration)

        # Duration description for the prompt
        if duration <= 60:
            duration_desc = "quick short — fast-paced, punchy"
        elif duration <= 180:
            duration_desc = "medium story — build character, develop conflict"
        else:
            duration_desc = "full story — rich narrative, multiple scenes, character arcs"

        # Characters from topic
        chars = topic.get("characters", ["Character1", "Character2"])
        if isinstance(chars, list):
            characters_str = ", ".join(chars)
        else:
            characters_str = str(chars)

        prompt = self.PROMPT_TEMPLATE.format(
            title=topic.get("title", "Funny Story"),
            premise=topic.get("premise", "A funny situation"),
            humor_type=topic.get("humor_type", "comedy"),
            characters=characters_str,
            duration=settings["duration"],
            duration_desc=duration_desc,
            min_words=settings["min_words"],
            max_words=settings["max_words"],
        )

        script = self.client.generate_json(prompt)

        # Handle string response — try to parse nested JSON strings
        for _ in range(3):
            if not isinstance(script, str):
                break
            try:
                script = json.loads(script)
            except (json.JSONDecodeError, ValueError):
                break
        if isinstance(script, str):
            script = {
                "hook": script[:80],
                "script_lines": [{"speaker": "NARRATOR", "line": script, "tone": "dramatic"}],
                "characters": chars if isinstance(chars, list) else ["Character1", "Character2"],
                "conflict": "A funny situation",
                "twist": "An unexpected ending",
            }

        # Handle wrapped response
        if isinstance(script, list):
            script = script[0] if script else {}

        # Try alternative key names for script_lines
        if "script_lines" not in script:
            for alt_key in ["lines", "dialogue", "script", "scenes", "dialog"]:
                if alt_key in script and isinstance(script[alt_key], list):
                    script["script_lines"] = script[alt_key]
                    break

        # Validate structure — build fallback if script_lines still missing
        if "script_lines" not in script:
            lines = []
            if "hook" in script:
                lines.append({"speaker": "NARRATOR", "line": str(script["hook"]), "tone": "dramatic"})
            if "conflict" in script:
                lines.append({"speaker": "NARRATOR", "line": str(script["conflict"]), "tone": "excited"})
            if "twist" in script:
                lines.append({"speaker": "NARRATOR", "line": str(script["twist"]), "tone": "surprised"})
            if not lines:
                for key, val in script.items():
                    if isinstance(val, str) and len(val) > 10:
                        lines.append({"speaker": "NARRATOR", "line": val, "tone": "neutral"})
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict) and ("line" in item or "text" in item or "content" in item):
                                lines.append({
                                    "speaker": item.get("speaker", item.get("character", "NARRATOR")),
                                    "line": item.get("line", item.get("text", item.get("content", ""))),
                                    "tone": item.get("tone", item.get("emotion", "neutral")),
                                })
            if lines:
                script["script_lines"] = lines
            else:
                print("   ⚠️  LLM returned unexpected format, using fallback script")
                script["script_lines"] = [
                    {"speaker": "NARRATOR", "line": "Well, this is awkward.", "tone": "dramatic"},
                    {"speaker": "Character1", "line": "I didn't sign up for this!", "tone": "confused"},
                    {"speaker": "Character2", "line": "Neither did I, but here we are.", "tone": "sarcastic"},
                ]
                script.setdefault("hook", "Well, this is awkward.")
                script.setdefault("conflict", "Two characters in a strange situation.")
                script.setdefault("twist", "Turns out it was all a dream.")

        # Ensure characters list exists
        if "characters" not in script:
            char_set = set()
            for line in script.get("script_lines", []):
                speaker = line.get("speaker", "")
                if speaker and speaker != "NARRATOR":
                    char_set.add(speaker)
            script["characters"] = list(char_set) or (chars if isinstance(chars, list) else ["Character1", "Character2"])

        # Store the duration in the script for downstream use
        script["target_duration"] = settings["duration"]

        return script

    def get_full_text(self, script):
        """Get the full script as plain text for voiceover.

        Args:
            script: dict from write_script().

        Returns:
            str: Full script text.
        """
        lines = []
        for entry in script.get("script_lines", []):
            lines.append(entry.get("line", ""))
        return " ".join(lines)

    def get_dialogue_segments(self, script):
        """Get script broken into timed segments for voiceover.

        Args:
            script: dict from write_script().

        Returns:
            list[dict]: Each with 'speaker', 'line', 'tone'.
        """
        return script.get("script_lines", [])
