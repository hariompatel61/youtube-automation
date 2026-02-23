"""
Step 7: Video Editor & Assembler (ULTRA-OPTIMIZED)
Assembles scene images, voiceover, music, and SFX into the final YouTube Short.
Compatible with moviepy v2.x okk
OPTIMIZED: ultrafast preset, all CPU cores, pre-computed zoom, disabled logger.
"""

import os
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    TextClip,
    concatenate_videoclips,
    ColorClip,
)
from config import Config


class VideoEditor:
    """Assembles all components into a final YouTube Short video.
    ULTRA-OPTIMIZED: ultrafast encoding, pre-computed zoom, parallel threads.
    """

    def __init__(self):
        self.width = Config.VIDEO_WIDTH
        self.height = Config.VIDEO_HEIGHT
        self.fps = Config.VIDEO_FPS
        self.total_duration = Config.VIDEO_DURATION

    def assemble_video(
        self,
        storyboard,
        scene_image_paths,
        voiceover_paths,
        bgm_path,
        sfx_paths,
        hook_text,
        output_path,
        duration=None,
    ):
        """Assemble all components into the final video.

        Args:
            storyboard: list of scene dicts with timing info.
            scene_image_paths: list of paths to scene PNG images.
            voiceover_paths: list of paths to voiceover MP3s (None for silent).
            bgm_path: path to background music WAV/MP3.
            sfx_paths: dict mapping sfx_type -> file path.
            hook_text: text to display in first 3 seconds.
            output_path: where to save the final MP4.

        Returns:
            str: Path to the final video file.
        """
        scene_clips = []
        audio_clips = []
        current_time = 0.0

        for i, scene in enumerate(storyboard):
            duration = scene.get("duration_seconds", 4)

            # 1. Create image clip with Ken Burns effect
            img_path = scene_image_paths[i] if i < len(scene_image_paths) else scene_image_paths[-1]
            img_clip = self._create_scene_clip(img_path, duration, scene.get("camera_angle", "wide"))
            img_clip = img_clip.with_start(current_time)
            scene_clips.append(img_clip)

            # 2. Add subtitle overlay
            dialogue = scene.get("dialogue", "")
            if dialogue:
                sub_clip = self._create_subtitle(dialogue, duration, current_time)
                if sub_clip:
                    scene_clips.append(sub_clip)

            # 3. Add voiceover audio
            if i < len(voiceover_paths) and voiceover_paths[i]:
                try:
                    vo_audio = AudioFileClip(voiceover_paths[i])
                    if vo_audio.duration > duration:
                        vo_audio = vo_audio.subclipped(0, duration)
                    vo_audio = vo_audio.with_start(current_time)
                    audio_clips.append(vo_audio)
                except Exception:
                    pass

            # 4. Add SFX at scene transitions
            sfx_type = scene.get("sfx", "silence")
            if sfx_type != "silence" and sfx_type in sfx_paths:
                try:
                    sfx_audio = AudioFileClip(sfx_paths[sfx_type])
                    sfx_audio = sfx_audio.with_start(current_time + 0.1)
                    sfx_audio = sfx_audio.with_volume_scaled(0.5)
                    audio_clips.append(sfx_audio)
                except Exception:
                    pass

            current_time += duration

        # 5. Add hook text overlay (first 3 seconds)
        if hook_text:
            hook_clip = self._create_hook_overlay(hook_text)
            if hook_clip:
                scene_clips.append(hook_clip)

        # 6. Compose video
        video = CompositeVideoClip(scene_clips, size=(self.width, self.height))
        # Use dynamic duration if provided, otherwise fallback to config default
        target_len = duration if duration else self.total_duration
        # Ensure we don't accidentally cut off end if scenes run slightly over
        final_len = max(current_time, target_len)
        video = video.with_duration(final_len)

        # 7. Add background music
        if bgm_path and os.path.exists(bgm_path):
            try:
                bgm = AudioFileClip(bgm_path)
                if bgm.duration > video.duration:
                    bgm = bgm.subclipped(0, video.duration)
                bgm = bgm.with_volume_scaled(0.15)
                audio_clips.append(bgm)
            except Exception:
                pass

        # 8. Mix all audio
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            video = video.with_audio(final_audio)

        # 9. Export with ULTRA-OPTIMIZED settings
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Use all available CPU cores for maximum speed
        cpu_count = os.cpu_count() or 4

        video.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",       # Fastest encoding preset
            threads=1,                # Single thread to avoid deadlocks
            bitrate="2000k",          # Reasonable for Shorts
            logger=None,              # Suppress verbose output
            ffmpeg_params=[
                "-movflags", "+faststart",   # Web-optimized (faster YouTube processing)
                "-tune", "animation",         # Better for cartoon content
                "-pix_fmt", "yuv420p",       # Max compatibility
            ],
        )

        # Cleanup
        video.close()
        for clip in audio_clips:
            try:
                clip.close()
            except Exception:
                pass

        return output_path

    def _create_scene_clip(self, image_path, duration, camera_angle):
        """Create an image clip with subtle Ken Burns zoom effect."""
        clip = ImageClip(image_path, duration=duration)

        zoom_factor = 0.08
        if camera_angle in ("close_up", "extreme_close_up"):
            zoom_factor = 0.12

        clip = clip.resized(lambda t: 1.0 + zoom_factor * (t / duration))
        clip = clip.with_position("center")
        return clip

    def _create_subtitle(self, text, duration, start_time):
        """Create a subtitle text clip."""
        try:
            words = text.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                if len(" ".join(current_line)) > 30:
                    lines.append(" ".join(current_line))
                    current_line = []
            if current_line:
                lines.append(" ".join(current_line))
            wrapped_text = "\n".join(lines)

            txt_clip = TextClip(
                text=wrapped_text,
                font_size=44,
                color="white",
                font="Arial",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(self.width - 100, None),
                text_align="center",
            )
            txt_clip = txt_clip.with_duration(duration)
            txt_clip = txt_clip.with_start(start_time)
            txt_clip = txt_clip.with_position(("center", self.height - 350))
            return txt_clip
        except Exception:
            return None

    def _create_hook_overlay(self, text):
        """Create the hook text that appears in the first 3 seconds."""
        try:
            txt_clip = TextClip(
                text=text,
                font_size=56,
                color="yellow",
                font="Arial",
                stroke_color="red",
                stroke_width=3,
                method="caption",
                size=(self.width - 80, None),
                text_align="center",
            )
            txt_clip = txt_clip.with_duration(3)
            txt_clip = txt_clip.with_start(0)
            txt_clip = txt_clip.with_position(("center", 200))
            txt_clip = txt_clip.crossfadein(0.3).crossfadeout(0.3)
            return txt_clip
        except Exception:
            return None
