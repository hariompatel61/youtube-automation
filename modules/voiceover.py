"""
Step 5: Voiceover Generator (OPTIMIZED)
Creates expressive voiceover audio using edge-tts with async batch processing.
"""

import os
import asyncio
import edge_tts
from config import Config


class VoiceoverGenerator:
    """Generates per-scene voiceover audio clips using Microsoft Edge TTS.
    OPTIMIZED: Uses asyncio.gather for parallel TTS synthesis.
    """

    # Voice mapping for different speaker types
    VOICE_MAP = {
        "NARRATOR": Config.NARRATOR_VOICE,
        "male": Config.CHARACTER_VOICE_MALE,
        "female": Config.CHARACTER_VOICE_FEMALE,
    }

    # Tone to speech adjustments
    TONE_ADJUSTMENTS = {
        "excited": {"rate": "+15%", "pitch": "+10Hz"},
        "angry": {"rate": "+10%", "pitch": "-5Hz"},
        "sad": {"rate": "-15%", "pitch": "-10Hz"},
        "confused": {"rate": "-5%", "pitch": "+5Hz"},
        "dramatic": {"rate": "-10%", "pitch": "-5Hz"},
        "scared": {"rate": "+20%", "pitch": "+15Hz"},
        "laughing": {"rate": "+10%", "pitch": "+10Hz"},
        "whisper": {"rate": "-20%", "pitch": "-10Hz"},
        "normal": {"rate": "+0%", "pitch": "+0Hz"},
    }

    def __init__(self):
        pass

    def generate_scene_voiceover(self, scene, scene_index, output_dir, character_voices=None):
        """Generate voiceover audio for a single scene.

        Args:
            scene: dict with 'dialogue', 'speaker', and optional 'tone'.
            scene_index: int, scene number.
            output_dir: str, directory to save audio files.
            character_voices: dict mapping character names to edge-tts voice names.

        Returns:
            str: Path to the generated MP3 file, or None if no dialogue.
        """
        dialogue = scene.get("dialogue", "")
        if isinstance(dialogue, list):
            dialogue = " ".join(str(d) for d in dialogue if d).strip()
        elif isinstance(dialogue, str):
            dialogue = dialogue.strip()
        else:
            dialogue = ""

        if not dialogue:
            return None

        speaker = scene.get("speaker", "NARRATOR")
        tone = scene.get("tone", "normal")

        voice = self._get_voice(speaker, character_voices)
        adj = self.TONE_ADJUSTMENTS.get(tone, self.TONE_ADJUSTMENTS["normal"])

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"voice_{scene_index:02d}.mp3")

        asyncio.run(self._synthesize(dialogue, voice, adj, filepath))
        return filepath

    def generate_all_voiceovers(self, storyboard, output_dir):
        """Generate voiceover for all scenes using PARALLEL async processing.

        Args:
            storyboard: list of scene dicts.
            output_dir: directory to save audio files.

        Returns:
            list[str|None]: Paths to generated audio files (None for silent scenes).
        """
        # Build character voice mapping
        all_characters = set()
        for scene in storyboard:
            for char in scene.get("characters_present", []):
                all_characters.add(char)

        character_voices = {}
        voice_options = [Config.CHARACTER_VOICE_MALE, Config.CHARACTER_VOICE_FEMALE]
        for i, char in enumerate(sorted(all_characters)):
            character_voices[char] = voice_options[i % len(voice_options)]

        voiceover_dir = os.path.join(output_dir, "voiceovers")
        os.makedirs(voiceover_dir, exist_ok=True)

        # Run ALL TTS jobs in parallel using asyncio.gather
        paths = asyncio.run(
            self._batch_synthesize(storyboard, voiceover_dir, character_voices)
        )
        return paths

    async def _batch_synthesize(self, storyboard, voiceover_dir, character_voices):
        """Synthesize all voiceovers in parallel."""
        tasks = []
        paths = []

        for i, scene in enumerate(storyboard):
            dialogue = scene.get("dialogue", "")
            if isinstance(dialogue, list):
                dialogue = " ".join(str(d) for d in dialogue if d).strip()
            elif isinstance(dialogue, str):
                dialogue = dialogue.strip()
            else:
                dialogue = ""

            if not dialogue:
                paths.append(None)
                continue

            speaker = scene.get("speaker", "NARRATOR")
            tone = scene.get("tone", "normal")
            voice = self._get_voice(speaker, character_voices)
            adj = self.TONE_ADJUSTMENTS.get(tone, self.TONE_ADJUSTMENTS["normal"])

            filepath = os.path.join(voiceover_dir, f"voice_{i + 1:02d}.mp3")
            paths.append(filepath)
            tasks.append(self._synthesize(dialogue, voice, adj, filepath))

        if tasks:
            await asyncio.gather(*tasks)

        return paths

    def _get_voice(self, speaker, character_voices=None):
        """Determine the TTS voice for a speaker."""
        if speaker == "NARRATOR":
            return self.VOICE_MAP["NARRATOR"]
        if character_voices and speaker in character_voices:
            return character_voices[speaker]
        return self.VOICE_MAP.get("male", Config.CHARACTER_VOICE_MALE)

    async def _synthesize(self, text, voice, adjustments, output_path):
        """Run edge-tts synthesis.

        Args:
            text: The text to speak.
            voice: edge-tts voice name.
            adjustments: dict with 'rate' and 'pitch'.
            output_path: where to save the MP3.
        """
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=adjustments.get("rate", "+0%"),
            pitch=adjustments.get("pitch", "+0Hz"),
        )
        await communicate.save(output_path)

    def generate_narration(self, full_text, output_path):
        """Generate a single narration audio from full script text.

        Args:
            full_text: Complete narration text.
            output_path: Where to save the MP3.

        Returns:
            str: Path to the generated file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        adj = self.TONE_ADJUSTMENTS["dramatic"]
        asyncio.run(self._synthesize(full_text, Config.NARRATOR_VOICE, adj, output_path))
        return output_path
