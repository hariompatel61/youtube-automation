"""
Step 6: Background Music & SFX Manager (ULTRA-OPTIMIZED)
Generates comedy background music and cartoon sound effects using numpy.
OPTIMIZED: All-numpy pipeline (no list conversions), parallel SFX, direct bytes output.
"""

import os
import math
import struct
import wave
import random
from concurrent.futures import ThreadPoolExecutor
from config import Config

import numpy as np


class MusicSFXManager:
    """Generates comedy background music and cartoon SFX using wave synthesis.
    ULTRA-OPTIMIZED: Pure numpy pipeline, no list conversions, parallel SFX generation.
    """

    SAMPLE_RATE = 44100
    CHANNELS = 1
    SAMPLE_WIDTH = 2  # 16-bit audio

    def __init__(self):
        os.makedirs(Config.MUSIC_DIR, exist_ok=True)
        os.makedirs(Config.SFX_DIR, exist_ok=True)

    # ── Core Synthesis (pure numpy, zero list conversion) ─────

    def _generate_sine(self, frequency, duration_ms, volume=0.3):
        """Generate a sine wave as numpy array (no list conversion)."""
        num_samples = int(self.SAMPLE_RATE * duration_ms / 1000)
        t = np.arange(num_samples, dtype=np.float32) / self.SAMPLE_RATE
        samples = (volume * np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        return samples

    def _apply_fade(self, samples, fade_in_ms=10, fade_out_ms=30):
        """Apply fade in/out to numpy array samples."""
        fade_in_samples = int(self.SAMPLE_RATE * fade_in_ms / 1000)
        fade_out_samples = int(self.SAMPLE_RATE * fade_out_ms / 1000)

        arr = samples.astype(np.float64)
        fi = min(fade_in_samples, len(arr))
        fo = min(fade_out_samples, len(arr))
        if fi > 0:
            arr[:fi] *= np.linspace(0, 1, fi)
        if fo > 0:
            arr[-fo:] *= np.linspace(1, 0, fo)
        return arr.astype(np.int16)

    def _mix_samples(self, *sample_arrays):
        """Mix multiple numpy sample arrays together."""
        max_len = max(len(s) for s in sample_arrays)
        mixed = np.zeros(max_len, dtype=np.float64)
        for samples in sample_arrays:
            mixed[:len(samples)] += samples.astype(np.float64)
        peak = np.abs(mixed).max()
        if peak > 32767:
            mixed = mixed * (32767 / peak)
        return mixed.astype(np.int16)

    def _concat_samples(self, *sample_arrays):
        """Concatenate numpy arrays (replaces list extend)."""
        return np.concatenate(sample_arrays)

    def _save_wav(self, samples, filepath):
        """Save numpy int16 array as WAV file."""
        # Ensure minimum duration of 0.5 second to avoid MoviePy errors with very short access
        min_samples = int(self.SAMPLE_RATE * 0.5)
        if len(samples) < min_samples:
            padding = np.zeros(min_samples - len(samples), dtype=np.int16)
            samples = np.concatenate([samples, padding])

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        arr = np.clip(samples, -32768, 32767).astype(np.int16)
        with wave.open(filepath, "w") as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(self.SAMPLE_WIDTH)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(arr.tobytes())

    def _silence(self, duration_ms):
        """Generate silent numpy samples."""
        return np.zeros(int(self.SAMPLE_RATE * duration_ms / 1000), dtype=np.int16)

    # ── Background Music ──────────────────────────────────────

    def generate_comedy_bgm(self, duration_ms=30000, output_path=None):
        """Generate a light comedy background music loop.

        Args:
            duration_ms: Duration in milliseconds.
            output_path: Where to save the file.

        Returns:
            str: Path to the generated WAV.
        """
        if output_path is None:
            output_path = os.path.join(Config.MUSIC_DIR, "comedy_bgm.wav")

        if output_path.endswith(".mp3"):
            output_path = output_path[:-4] + ".wav"

        # Create a bouncy comedy melody
        notes = [
            (523, 200), (587, 200), (659, 200), (698, 200),
            (659, 200), (587, 200), (523, 400),
            (698, 200), (659, 200), (587, 200), (523, 200),
            (587, 300), (523, 300),
        ]

        melody_parts = []
        for freq, dur in notes:
            tone = self._generate_sine(freq, dur, volume=0.15)
            tone = self._apply_fade(tone, fade_in_ms=10, fade_out_ms=30)
            melody_parts.append(tone)
        melody_samples = np.concatenate(melody_parts)

        # Bass line
        bass_notes = [
            (262, 400), (196, 400), (220, 400), (262, 400),
            (196, 400), (220, 400), (262, 800),
        ]
        bass_parts = []
        for freq, dur in bass_notes:
            tone = self._generate_sine(freq, dur, volume=0.10)
            tone = self._apply_fade(tone, fade_in_ms=5, fade_out_ms=50)
            bass_parts.append(tone)
        bass_samples = np.concatenate(bass_parts)

        # Loop melody and bass to fill duration
        target_samples = int(self.SAMPLE_RATE * duration_ms / 1000)

        reps = (target_samples // len(melody_samples)) + 1
        melody_loop = np.tile(melody_samples, reps)[:target_samples]

        reps = (target_samples // len(bass_samples)) + 1
        bass_loop = np.tile(bass_samples, reps)[:target_samples]

        bgm = self._mix_samples(melody_loop, bass_loop)
        bgm = self._apply_fade(bgm, fade_in_ms=500, fade_out_ms=1000)

        self._save_wav(bgm, output_path)
        return output_path

    # ── Sound Effects ─────────────────────────────────────────

    def generate_sfx(self, sfx_type, output_path=None):
        """Generate a cartoon sound effect."""
        if output_path is None:
            output_path = os.path.join(Config.SFX_DIR, f"{sfx_type}.wav")

        if output_path.endswith(".mp3"):
            output_path = output_path[:-4] + ".wav"

        generators = {
            "boing": self._gen_boing,
            "slap": self._gen_slap,
            "pop": self._gen_pop,
            "whoosh": self._gen_whoosh,
            "crash": self._gen_crash,
            "laugh": self._gen_laugh_track,
            "silence": self._gen_silence_sfx,
        }

        gen_func = generators.get(sfx_type, self._gen_pop)
        samples = gen_func()

        self._save_wav(samples, output_path)
        return output_path

    def generate_all_sfx(self):
        """Pre-generate all SFX types IN PARALLEL.

        Returns:
            dict: Mapping sfx_type -> file path.
        """
        sfx_types = ["boing", "slap", "pop", "whoosh", "crash", "laugh"]
        paths = {}

        with ThreadPoolExecutor(max_workers=len(sfx_types)) as executor:
            futures = {
                executor.submit(self.generate_sfx, sfx_type): sfx_type
                for sfx_type in sfx_types
            }
            for future in futures:
                sfx_type = futures[future]
                paths[sfx_type] = future.result()

        return paths

    def get_sfx_for_scene(self, scene, sfx_paths):
        """Get the appropriate SFX file path for a scene."""
        sfx_type = scene.get("sfx", "silence")
        if sfx_type == "silence" or sfx_type not in sfx_paths:
            return None
        return sfx_paths[sfx_type]

    # ── SFX Generators (all-numpy, no list conversion) ────────

    def _gen_boing(self):
        parts = []
        for i in range(8):
            freq = 300 + i * 100
            parts.append(self._generate_sine(freq, 50, volume=0.4))
        for i in range(4):
            freq = 1100 - i * 150
            parts.append(self._generate_sine(freq, 50, volume=0.3))
        return self._apply_fade(np.concatenate(parts), fade_in_ms=5, fade_out_ms=100)

    def _gen_slap(self):
        layers = []
        for freq in [200, 800, 1600, 3200]:
            layers.append(self._generate_sine(freq, 80, volume=0.3))
        mixed = self._mix_samples(*layers)
        return self._apply_fade(mixed, fade_in_ms=2, fade_out_ms=60)

    def _gen_pop(self):
        pop = self._generate_sine(1200, 30, volume=0.5)
        tail = self._generate_sine(600, 70, volume=0.2)
        samples = np.concatenate([pop, tail])
        return self._apply_fade(samples, fade_in_ms=2, fade_out_ms=50)

    def _gen_whoosh(self):
        parts = []
        for i in range(20):
            freq = 200 + i * 150
            vol = 0.1 + i * 0.015
            parts.append(self._generate_sine(freq, 20, volume=min(vol, 0.4)))
        return self._apply_fade(np.concatenate(parts), fade_in_ms=50, fade_out_ms=100)

    def _gen_crash(self):
        layers = []
        for freq in [100, 250, 500, 1000, 2000, 4000]:
            layers.append(self._generate_sine(freq, 300, volume=0.15))
        mixed = self._mix_samples(*layers)
        return self._apply_fade(mixed, fade_in_ms=5, fade_out_ms=200)

    def _gen_laugh_track(self):
        parts = []
        for i in range(5):
            freq = 400 + random.randint(-50, 50)
            ha = self._generate_sine(freq, 120, volume=0.3)
            ha = self._apply_fade(ha, fade_in_ms=10, fade_out_ms=40)
            parts.append(ha)
            parts.append(self._silence(60))
        return np.concatenate(parts)

    def _gen_silence_sfx(self):
        return self._silence(200)
