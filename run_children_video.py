"""
Children's 3D Animated Video Generator
========================================
Generates a ~45-second Pixar-quality 3D animated children's story video
and uploads it to YouTube.

Usage:
    python run_children_video.py           # Generate only (no upload)
    python run_children_video.py --auto    # Generate + upload to YouTube
"""

import os
import sys
import json
import argparse
import datetime
import time

# Fix Windows console encoding for emoji/unicode support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import Config
from modules.excel_tracker import ExcelTracker


# ─────────────────────────────────────────────────────────────
# PRE-WRITTEN CHILDREN'S STORY — "Biscuit the Brave Little Robot"
# 45 seconds | 6 scenes | Pixar-quality 3D visuals
# ─────────────────────────────────────────────────────────────
TOPIC = {
    "title": "Biscuit the Brave Little Robot",
    "premise": "A tiny, clumsy robot learns that being brave means trying even when you're scared.",
    "humor_type": "heartwarming comedy",
    "characters": ["Biscuit", "Lily"],
    "suggested_duration": 45,
    "viral_score": 9,
}

SCRIPT = {
    "hook": "What if a tiny robot was MORE scared of butterflies than dragons?",
    "characters": ["Biscuit", "Lily"],
    "target_duration": 45,
    "script_lines": [
        {"speaker": "NARRATOR", "line": "This is Biscuit — the smallest, clumsiest robot in the whole world.", "tone": "excited"},
        {"speaker": "NARRATOR", "line": "Biscuit was afraid of EVERYTHING. Puddles. Loud noises. And especially... butterflies.", "tone": "dramatic"},
        {"speaker": "Biscuit", "line": "B-b-butterfly! Run away!", "tone": "scared"},
        {"speaker": "Lily", "line": "Biscuit! My kite is stuck in the big tree. Can you help me?", "tone": "excited"},
        {"speaker": "Biscuit", "line": "Me? Up there? Oh no, no, no... But... okay. I will try!", "tone": "confused"},
        {"speaker": "NARRATOR", "line": "Biscuit climbed higher and higher — beep boop beep — and grabbed the kite! Everyone cheered!", "tone": "excited"},
        {"speaker": "Biscuit", "line": "I did it! I was scared... but I did it! Beep beep hooray!", "tone": "laughing"},
        {"speaker": "NARRATOR", "line": "Because being brave doesn't mean you're not scared. It means you try anyway!", "tone": "dramatic"},
    ],
    "conflict": "Biscuit must overcome his fears to help his friend Lily get her kite from a tall tree.",
    "twist": "Biscuit succeeds and learns that bravery is trying even when you're scared.",
    "total_word_count": 95,
}

STORYBOARD = [
    {
        "scene_number": 1,
        "duration_seconds": 7,
        "description": "A tiny cute robot named Biscuit stands in a colorful sunny garden, looking nervous and adorable, surrounded by big colorful flowers",
        "characters_present": ["Biscuit"],
        "expressions": {"Biscuit": "nervous and cute"},
        "background": "colorful magical garden with giant flowers",
        "camera_angle": "medium",
        "dialogue": "This is Biscuit — the smallest, clumsiest robot in the whole world.",
        "speaker": "NARRATOR",
        "tone": "excited",
        "sfx": "beep",
        "action": "standing proudly but wobbling slightly",
    },
    {
        "scene_number": 2,
        "duration_seconds": 7,
        "description": "Biscuit the tiny robot is startled and jumps in the air, arms flailing, as a beautiful butterfly lands on his nose",
        "characters_present": ["Biscuit"],
        "expressions": {"Biscuit": "surprised and terrified"},
        "background": "bright sunny meadow with colorful butterflies",
        "camera_angle": "close_up",
        "dialogue": "Biscuit was afraid of EVERYTHING. Puddles. Loud noises. And especially... butterflies!",
        "speaker": "NARRATOR",
        "tone": "dramatic",
        "sfx": "boing",
        "action": "jumping in shock from butterfly landing on nose",
    },
    {
        "scene_number": 3,
        "duration_seconds": 8,
        "description": "A cheerful little girl named Lily with pigtails and a red dress points up at a very tall magical tree where a rainbow kite is stuck in the branches",
        "characters_present": ["Lily", "Biscuit"],
        "expressions": {"Lily": "worried but hopeful", "Biscuit": "worried"},
        "background": "giant magical tree with rainbow kite stuck in branches, blue sky",
        "camera_angle": "wide",
        "dialogue": "Lily: Biscuit! My kite is stuck in the big tree. Can you help me? Biscuit: Me? Up there? Oh no no no!",
        "speaker": "Lily",
        "tone": "excited",
        "sfx": "whoosh",
        "action": "Lily pointing up at tall tree, Biscuit shivering with worry",
    },
    {
        "scene_number": 4,
        "duration_seconds": 8,
        "description": "Biscuit the tiny robot bravely starts climbing the huge magical tree, his little robot arms reaching out, looking determined but scared",
        "characters_present": ["Biscuit"],
        "expressions": {"Biscuit": "determined but scared"},
        "background": "climbing up a giant colorful fantasy tree with glowing fireflies",
        "camera_angle": "medium",
        "dialogue": "Biscuit climbed higher and higher — beep boop beep — getting closer to the kite!",
        "speaker": "NARRATOR",
        "tone": "excited",
        "sfx": "beep",
        "action": "carefully climbing tree branches with determination",
    },
    {
        "scene_number": 5,
        "duration_seconds": 8,
        "description": "Biscuit triumphantly stands at the top of the tree holding the rainbow kite above his head, glowing with joy, while Lily and woodland animals cheer below",
        "characters_present": ["Biscuit", "Lily"],
        "expressions": {"Biscuit": "overjoyed and proud", "Lily": "cheering with delight"},
        "background": "top of magical tree, sunset sky, cheering woodland animals, golden light",
        "camera_angle": "wide",
        "dialogue": "I did it! I was scared... but I did it! Beep beep hooray!",
        "speaker": "Biscuit",
        "tone": "laughing",
        "sfx": "sparkle",
        "action": "holding rainbow kite triumphantly as everyone cheers",
    },
    {
        "scene_number": 6,
        "duration_seconds": 7,
        "description": "Biscuit and Lily sit together under the tree watching the rainbow kite fly high in the golden sunset sky, both smiling peacefully",
        "characters_present": ["Biscuit", "Lily"],
        "expressions": {"Biscuit": "happy and content", "Lily": "happy and grateful"},
        "background": "beautiful golden sunset meadow, kite flying high in colorful sky",
        "camera_angle": "wide",
        "dialogue": "Being brave doesn't mean you're not scared. It means you try anyway!",
        "speaker": "NARRATOR",
        "tone": "dramatic",
        "sfx": "sparkle",
        "action": "sitting together peacefully watching kite fly in sunset",
    },
]


def save_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   💾 Saved: {os.path.basename(filepath)}")


def generate_children_scene(scene, scene_index, output_dir):
    """Generate a single Pixar-quality children's scene using Pollinations.ai."""
    import requests
    import random
    from urllib.parse import quote

    description = scene.get("description", "A colorful cartoon scene")
    characters = ", ".join(scene.get("characters_present", ["cartoon character"]))
    expression = list(scene.get("expressions", {}).values())
    expression_str = expression[0] if expression else "happy"
    camera = scene.get("camera_angle", "medium shot")
    action = scene.get("action", "standing and smiling")

    prompt = Config.CHILDREN_SCENE_PROMPT.format(
        scene_description=description,
        characters=characters,
        expression=expression_str,
        action=action,
        camera_angle=camera + " shot",
    )

    encoded_prompt = quote(prompt)
    seed = random.randint(1000, 999999)

    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={Config.VIDEO_WIDTH}&height={Config.VIDEO_HEIGHT}"
        f"&model=flux&seed={seed}&nologo=true&enhance=true"
    )

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"scene_{scene_index:02d}.jpg")

    for attempt in range(4):
        try:
            print(f"     🎨 Generating scene {scene_index} (attempt {attempt+1})...")
            response = requests.get(url, timeout=60)
            if response.status_code == 200 and len(response.content) > 10000:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"     ✅ Scene {scene_index} saved ({len(response.content)//1024}KB)")
                return filepath
        except Exception as e:
            print(f"     ⚠️  Attempt {attempt+1} failed: {e}")
        time.sleep(3)

    # Fallback — generate a colored background with Pillow
    print(f"     ⚠️  AI failed for scene {scene_index}, using colorful fallback")
    return _generate_fallback_scene(scene, scene_index, output_dir)


def _generate_fallback_scene(scene, scene_index, output_dir):
    """Generate a colorful Pillow fallback scene."""
    try:
        from modules.scene_generator import SceneGenerator
        gen = SceneGenerator()
        return gen.generate_scene_image(scene, scene_index, output_dir)
    except Exception as e:
        print(f"     ❌ Fallback failed: {e}")
        return None


def run_children_pipeline(auto_upload=False):
    Config.ensure_directories()

    print("\n" + "=" * 60)
    print("🧸  Children's 3D Animated Video Generator  🧸")
    print("   ✨ Pixar-Quality 3D Scenes + Expressive Voiceover ✨")
    print("=" * 60)

    pipeline_start = time.time()

    # Create output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(Config.OUTPUT_DIR, f"children_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"📂 Output: {run_dir}\n")

    # Save data
    save_json(TOPIC, os.path.join(run_dir, "selected_topic.json"))
    save_json(SCRIPT, os.path.join(run_dir, "script.json"))
    save_json(STORYBOARD, os.path.join(run_dir, "storyboard.json"))

    # ─── STEP 4: Generate 3D Pixar-quality scenes ─────────────
    print("━" * 50)
    print("🎨 STEP 4: Generating Pixar-Quality 3D Scenes...")
    print("━" * 50)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    scenes_dir = os.path.join(run_dir, "scenes")
    scene_paths = [None] * len(STORYBOARD)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        for i, scene in enumerate(STORYBOARD):
            future = executor.submit(generate_children_scene, scene, i + 1, scenes_dir)
            futures[future] = i

        for future in as_completed(futures):
            idx = futures[future]
            try:
                path = future.result()
                scene_paths[idx] = path
            except Exception as e:
                print(f"     ❌ Scene {idx+1} error: {e}")

    valid_scenes = [p for p in scene_paths if p]
    print(f"\n   🖼️  {len(valid_scenes)}/{len(STORYBOARD)} scenes generated\n")

    # ─── STEP 5: Generate Voiceover ───────────────────────────
    print("━" * 50)
    print("🎤 STEP 5: Generating Child-Friendly Voiceover...")
    print("━" * 50)

    # Patch the narrator voice to a warm, child-friendly voice
    original_narrator = Config.NARRATOR_VOICE
    Config.NARRATOR_VOICE = Config.CHILDREN_NARRATOR_VOICE

    # Build character voice map
    character_voices = {
        "Lily": "en-US-JennyNeural",      # Warm female voice for Lily
        "Biscuit": "en-US-GuyNeural",     # Friendly male voice for Biscuit
        "NARRATOR": Config.CHILDREN_NARRATOR_VOICE,
    }

    import asyncio
    import edge_tts

    voiceover_dir = os.path.join(run_dir, "voiceovers")
    os.makedirs(voiceover_dir, exist_ok=True)

    TONE_ADJUSTMENTS = {
        "excited": {"rate": "+15%", "pitch": "+10Hz"},
        "dramatic": {"rate": "-5%", "pitch": "-3Hz"},
        "scared": {"rate": "+20%", "pitch": "+15Hz"},
        "confused": {"rate": "-5%", "pitch": "+5Hz"},
        "laughing": {"rate": "+10%", "pitch": "+10Hz"},
        "normal": {"rate": "+0%", "pitch": "+0Hz"},
    }

    async def _synthesize_all():
        tasks = []
        paths = []
        for i, scene in enumerate(STORYBOARD):
            dialogue = scene.get("dialogue", "")
            if not dialogue:
                paths.append(None)
                continue
            speaker = scene.get("speaker", "NARRATOR")
            tone = scene.get("tone", "normal")
            voice = character_voices.get(speaker, Config.CHILDREN_NARRATOR_VOICE)
            adj = TONE_ADJUSTMENTS.get(tone, TONE_ADJUSTMENTS["normal"])
            filepath = os.path.join(voiceover_dir, f"voice_{i+1:02d}.mp3")
            paths.append(filepath)

            async def _do_synth(text, v, a, fp):
                comm = edge_tts.Communicate(text, v, rate=a["rate"], pitch=a["pitch"])
                await comm.save(fp)

            tasks.append(_do_synth(dialogue, voice, adj, filepath))

        await asyncio.gather(*tasks)
        return paths

    voiceover_paths = asyncio.run(_synthesize_all())
    valid_vo = sum(1 for p in voiceover_paths if p)
    print(f"   🎤 {valid_vo}/{len(STORYBOARD)} voiceovers generated\n")

    # Restore Config
    Config.NARRATOR_VOICE = original_narrator

    # ─── STEP 6: Background Music ──────────────────────────────
    print("━" * 50)
    print("🎶 STEP 6: Adding Comic Background Music...")
    print("━" * 50)

    bgm_path = None
    sfx_paths = {}
    try:
        from modules.music_sfx import MusicSFXManager
        music_mgr = MusicSFXManager()
        bgm_path = music_mgr.generate_comedy_bgm(
            duration_ms=45 * 1000,
            output_path=os.path.join(run_dir, "bgm.mp3")
        )
        sfx_paths = music_mgr.generate_all_sfx()
        print(f"   🎶 BGM: {os.path.basename(bgm_path) if bgm_path else 'None'}\n")
    except Exception as e:
        print(f"   ⚠️  Music generation skipped: {e}\n")

    # ─── STEP 7: Assemble Final Video ──────────────────────────
    print("━" * 50)
    print("🎬 STEP 7: Assembling Final 3D Animated Video...")
    print("━" * 50)

    from modules.video_editor import VideoEditor
    editor = VideoEditor()

    video_path = os.path.join(run_dir, "final_short.mp4")
    editor.assemble_video(
        storyboard=STORYBOARD,
        scene_image_paths=valid_scenes,
        voiceover_paths=voiceover_paths,
        bgm_path=bgm_path,
        sfx_paths=sfx_paths,
        hook_text=SCRIPT["hook"],
        output_path=video_path,
        duration=45,
    )
    print(f"\n   🎬 Video ready: {video_path}\n")

    # ─── STEP 8+9: SEO Metadata + Thumbnail (Parallel) ─────────
    print("━" * 50)
    print("⚡ STEPS 8+9: SEO Metadata + Thumbnail...")
    print("━" * 50)

    metadata = None
    thumbnail_path = None

    from concurrent.futures import ThreadPoolExecutor, as_completed as asc

    def _gen_metadata():
        from modules.seo_metadata import SEOMetadataGenerator
        seo = SEOMetadataGenerator()
        return seo.generate_metadata(TOPIC, SCRIPT)

    def _gen_thumbnail():
        from modules.thumbnail import ThumbnailGenerator
        thumb = ThumbnailGenerator()
        return thumb.generate_thumbnail(
            title="Biscuit the Brave Robot",
            expression="happy",
            output_path=os.path.join(run_dir, "thumbnail.png"),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_meta = executor.submit(_gen_metadata)
        f_thumb = executor.submit(_gen_thumbnail)
        try:
            metadata = f_meta.result()
            save_json(metadata, os.path.join(run_dir, "metadata.json"))
            print(f"   📌 Title: {metadata.get('title', 'N/A')}")
        except Exception as e:
            print(f"   ⚠️  SEO metadata: {e}")
        try:
            thumbnail_path = f_thumb.result()
            print(f"   🖼️  Thumbnail: {thumbnail_path}")
        except Exception as e:
            print(f"   ⚠️  Thumbnail: {e}")

    print()

    # ─── STEP 10: YouTube Upload ───────────────────────────────
    if auto_upload:
        print("━" * 50)
        print("📤 STEP 10: Uploading to YouTube...")
        print("━" * 50)
        try:
            from modules.youtube_uploader import YouTubeUploader
            uploader = YouTubeUploader()
            result = uploader.upload_video(video_path, metadata, thumbnail_path)
            if "error" in result:
                print(f"   ❌ Upload failed: {result['error']}")
            else:
                print(f"   ✅ Uploaded! URL: {result.get('url', 'N/A')}")
                save_json(result, os.path.join(run_dir, "upload_result.json"))
        except Exception as e:
            print(f"   ❌ Upload error: {e}")
        print()

    # ─── Excel Tracker ─────────────────────────────────────────
    try:
        tracker = ExcelTracker()
        upload_result = None
        upload_path = os.path.join(run_dir, "upload_result.json")
        if os.path.exists(upload_path):
            with open(upload_path, "r") as f:
                upload_result = json.load(f)
        tracker.log_run(
            run_id=os.path.basename(run_dir),
            topic=TOPIC,
            script=SCRIPT,
            video_path=video_path,
            upload_result=upload_result,
            status="Uploaded" if auto_upload and upload_result else "Completed",
        )
    except Exception as e:
        print(f"   ⚠️  Excel tracker: {e}")

    # ─── Summary ───────────────────────────────────────────────
    total = time.time() - pipeline_start
    print("=" * 60)
    print("🎉  CHILDREN'S VIDEO COMPLETE!")
    print(f"⚡  Total time: {total:.1f}s ({total/60:.1f} min)")
    print("=" * 60)
    print(f"\n📂 Output: {run_dir}")
    print(f"🎬 Video: {video_path}")

    if os.path.exists(run_dir):
        print("\n📦 Output files:")
        for root, dirs, files in os.walk(run_dir):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                size = os.path.getsize(fpath)
                size_str = f"{size/1024:.0f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"
                rel = os.path.relpath(fpath, run_dir)
                print(f"   📄 {rel} ({size_str})")

    print()
    return video_path


def main():
    parser = argparse.ArgumentParser(
        description="Children's 3D Animated Video Generator — Pixar-Quality",
    )
    parser.add_argument("--auto", action="store_true",
                        help="Upload to YouTube after generation")
    args = parser.parse_args()
    run_children_pipeline(auto_upload=args.auto)


if __name__ == "__main__":
    main()
