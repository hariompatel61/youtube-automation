"""
YouTube Shorts Comedy Cartoon Automation Pipeline (ULTRA-OPTIMIZED)
===================================================
Fully automated content creation from topic idea to YouTube upload.
OPTIMIZED: Groq (ultra-fast LLM), parallel steps, concurrent I/O, speed metrics.

Usage:
    python main.py                     # Full automated pipeline (no upload)
    python main.py --auto              # Full pipeline + YouTube upload
    python main.py --topic "cat pizza" # Use a custom topic
    python main.py --steps 1,2,3      # Run specific steps only
    python main.py --dry-run           # Validate setup without API calls
"""

import os
import sys
import json
import argparse
import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix Windows console encoding for emoji/unicode support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import Config
from modules.excel_tracker import ExcelTracker


def print_banner():
    """Print a cool startup banner."""
    print("\n" + "=" * 60)
    print("🎬  YouTube Shorts Comedy Cartoon Automation  🎬")
    print("   ⚡ ULTRA-OPTIMIZED — Parallel Steps + Fast LLM ⚡")
    print("=" * 60)
    provider = Config.LLM_PROVIDER.upper()
    model = Config._get_llm_model()
    print(f"  🧠 LLM: {provider} ({model})")
    print(f"  📁 Output: {Config.OUTPUT_DIR}")
    print(f"  🎥 Format: {Config.VIDEO_WIDTH}x{Config.VIDEO_HEIGHT} @ {Config.VIDEO_FPS}fps")
    print(f"  ⏱️  Duration: {Config.VIDEO_DURATION}s")
    print(f"  🔧 CPU Cores: {os.cpu_count()}")
    print("=" * 60 + "\n")


def create_output_dir():
    """Create a timestamped output directory for this run."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(Config.OUTPUT_DIR, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def save_json(data, filepath):
    """Save data as formatted JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   💾 Saved: {os.path.basename(filepath)}")


def timed_step(step_name):
    """Decorator/context manager for timing steps."""
    class Timer:
        def __enter__(self):
            self.start = time.time()
            return self
        def __exit__(self, *args):
            elapsed = time.time() - self.start
            print(f"   ⏱️  {step_name} completed in {elapsed:.1f}s")
    return Timer()


def run_pipeline(args):
    """Run the full content creation pipeline."""
    Config.ensure_directories()
    print_banner()

    pipeline_start = time.time()

    # Parse which steps to run
    if args.steps:
        steps_to_run = set(int(s) for s in args.steps.split(","))
    else:
        steps_to_run = set(range(1, 11))

    # Skip upload unless --auto is specified
    if not args.auto and 10 in steps_to_run:
        steps_to_run.discard(10)

    # Dry run mode
    if args.dry_run:
        print("🧪 DRY RUN MODE - Validating setup...\n")
        errors = Config.validate()
        if errors:
            for e in errors:
                print(f"  ⚠️  {e}")
        else:
            print("  ✅ Configuration valid")
        print("\n  Checking module imports:")
        _test_imports()
        if errors:
            print(f"\n🧪 Dry run complete. {len(errors)} warning(s) — set up .env before running.")
        else:
            print("\n🧪 Dry run complete. All checks passed!")
        return

    # Validate config
    errors = Config.validate()
    if errors:
        print("❌ Configuration errors:")
        for e in errors:
            print(f"   - {e}")
        print("\n💡 Copy .env.example to .env and fill in your API keys.")
        sys.exit(1)

    run_dir = create_output_dir()
    print(f"📂 Run directory: {run_dir}\n")

    topic = None
    script = None
    storyboard = None
    scene_paths = []
    voiceover_paths = []
    bgm_path = None
    sfx_paths = {}
    metadata = None
    thumbnail_path = None
    video_path = None

    # ═══════════════════════════════════════════════════════════
    # STEP 1: Topic Generation
    # ═══════════════════════════════════════════════════════════
    if 1 in steps_to_run:
        print("━" * 50)
        print("📝 STEP 1: Generating Comedy Topic...")
        print("━" * 50)

        with timed_step("Topic Generation"):
            from modules.topic_generator import TopicGenerator
            gen = TopicGenerator()

            if args.topic:
                topic = gen.generate_from_custom(args.topic)
                print(f"   📌 Custom topic: {topic['title']}")
            else:
                topics = gen.generate_topics(count=3)  # Reduced from 5 to 3 for speed
                topic = topics[0]
                print(f"   🏆 Best topic: {topic['title']} (viral score: {topic.get('viral_score', '?')})")
                print(f"   ⏱️  Suggested duration: {topic.get('suggested_duration', '?')}s")
                save_json(topics, os.path.join(run_dir, "all_topics.json"))

            save_json(topic, os.path.join(run_dir, "selected_topic.json"))
            print(f"   💡 Premise: {topic.get('premise', '')}")
        print()

    # ═══════════════════════════════════════════════════════════
    # STEP 2: Script Writing
    # ═══════════════════════════════════════════════════════════
    if 2 in steps_to_run:
        print("━" * 50)
        print("✍️  STEP 2: Writing Comedy Script...")
        print("━" * 50)

        with timed_step("Script Writing"):
            if topic is None:
                topic = _load_json(run_dir, "selected_topic.json")

            from modules.script_writer import ScriptWriter
            writer = ScriptWriter()
            script = writer.write_script(topic)

            print(f"   🎣 Hook: {script.get('hook', 'N/A')}")
            print(f"   🎭 Characters: {', '.join(script.get('characters', []))}")
            print(f"   😂 Twist: {script.get('twist', 'N/A')}")
            print(f"   📊 Word count: {script.get('total_word_count', '?')}")

            save_json(script, os.path.join(run_dir, "script.json"))
        print()

    # ═══════════════════════════════════════════════════════════
    # STEP 3: Storyboard & Scene Breakdown
    # ═══════════════════════════════════════════════════════════
    if 3 in steps_to_run:
        print("━" * 50)
        print("🎬 STEP 3: Creating Storyboard...")
        print("━" * 50)

        with timed_step("Storyboard Creation"):
            if script is None:
                script = _load_json(run_dir, "script.json")

            from modules.storyboard import StoryboardCreator
            creator = StoryboardCreator()
            storyboard = creator.create_storyboard(script)

            for scene in storyboard:
                print(f"   🎞️  Scene {scene['scene_number']}: {scene.get('description', '')[:60]}... "
                      f"({scene.get('duration_seconds', '?')}s)")

            save_json(storyboard, os.path.join(run_dir, "storyboard.json"))
        print()

    # ═══════════════════════════════════════════════════════════
    # STEPS 4, 5, 6: PARALLEL — Scenes + Voiceover + Music/SFX
    # These three steps are INDEPENDENT and can run at the same time!
    # ═══════════════════════════════════════════════════════════
    parallel_steps = {4, 5, 6} & steps_to_run
    if parallel_steps:
        print("━" * 50)
        print("⚡ STEPS 4+5+6: PARALLEL Generation (Scenes + Voice + Music)...")
        print("━" * 50)

        parallel_start = time.time()

        if storyboard is None:
            storyboard = _load_json(run_dir, "storyboard.json")
        if script is None:
            script = _load_json(run_dir, "script.json")

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}

            # Step 4: Scene Generation
            if 4 in steps_to_run:
                def _gen_scenes():
                    from modules.scene_generator import SceneGenerator
                    scene_gen = SceneGenerator()
                    scenes_dir = os.path.join(run_dir, "scenes")
                    return scene_gen.generate_all_scenes(storyboard, scenes_dir)
                futures[executor.submit(_gen_scenes)] = "scenes"

            # Step 5: Voiceover Generation
            if 5 in steps_to_run:
                def _gen_voiceovers():
                    from modules.voiceover import VoiceoverGenerator
                    vo_gen = VoiceoverGenerator()
                    return vo_gen.generate_all_voiceovers(storyboard, run_dir)
                futures[executor.submit(_gen_voiceovers)] = "voiceovers"

            # Step 6: Music & SFX
            if 6 in steps_to_run:
                def _gen_music():
                    from modules.music_sfx import MusicSFXManager
                    music_mgr = MusicSFXManager()
                    duration = script.get("target_duration", Config.VIDEO_DURATION) if script else Config.VIDEO_DURATION
                    bgm = music_mgr.generate_comedy_bgm(
                        duration_ms=duration * 1000,
                        output_path=os.path.join(run_dir, "bgm.mp3")
                    )
                    sfx = music_mgr.generate_all_sfx()
                    return bgm, sfx
                futures[executor.submit(_gen_music)] = "music"

            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    if task_name == "scenes":
                        scene_paths = result
                        print(f"   🖼️  Scenes generated: {len(scene_paths)} images")
                    elif task_name == "voiceovers":
                        voiceover_paths = result
                        valid_vo = sum(1 for p in voiceover_paths if p)
                        print(f"   🎤 Voiceovers generated: {valid_vo}/{len(voiceover_paths)}")
                    elif task_name == "music":
                        bgm_path, sfx_paths = result
                        print(f"   🎶 Music + SFX generated: {os.path.basename(bgm_path)}")
                except Exception as e:
                    print(f"   ❌ {task_name} failed: {e}")

        elapsed = time.time() - parallel_start
        print(f"   ⏱️  Parallel steps completed in {elapsed:.1f}s")
        print()

    # ═══════════════════════════════════════════════════════════
    # STEP 7: Video Editing & Assembly (ULTRAFAST ENCODING)
    # ═══════════════════════════════════════════════════════════
    if 7 in steps_to_run:
        print("━" * 50)
        print("🎞️  STEP 7: Assembling Final Video (ultrafast)...")
        print("━" * 50)

        with timed_step("Video Assembly"):
            if storyboard is None:
                storyboard = _load_json(run_dir, "storyboard.json")
            if not scene_paths:
                scenes_dir = os.path.join(run_dir, "scenes")
                if os.path.exists(scenes_dir):
                    scene_paths = sorted(
                        [os.path.join(scenes_dir, f) for f in os.listdir(scenes_dir) if f.endswith(".png")]
                    )
            if not voiceover_paths:
                vo_dir = os.path.join(run_dir, "voiceovers")
                if os.path.exists(vo_dir):
                    vo_files = sorted(os.listdir(vo_dir))
                    voiceover_paths = [os.path.join(vo_dir, f) for f in vo_files]

            if not bgm_path:
                bgm_path = os.path.join(run_dir, "bgm.wav")
                if not os.path.exists(bgm_path):
                    bgm_path = os.path.join(run_dir, "bgm.mp3")
                    if not os.path.exists(bgm_path):
                        bgm_path = None

            from modules.video_editor import VideoEditor
            editor = VideoEditor()

            hook_text = ""
            if script:
                hook_text = script.get("hook", "")
            else:
                script_data = _load_json(run_dir, "script.json")
                if script_data:
                    hook_text = script_data.get("hook", "")

            video_path = os.path.join(run_dir, "final_short.mp4")
            editor.assemble_video(
                storyboard=storyboard,
                scene_image_paths=scene_paths,
                voiceover_paths=voiceover_paths,
                bgm_path=bgm_path,
                sfx_paths=sfx_paths,
                hook_text=hook_text,
                output_path=video_path,
                duration=script.get("target_duration", Config.VIDEO_DURATION) if script else None,
            )
            print(f"   🎬 Final video: {video_path}")
        print()

    # ═══════════════════════════════════════════════════════════
    # STEPS 8+9: PARALLEL — SEO Metadata + Thumbnail
    # (Both are independent and can run together)
    # ═══════════════════════════════════════════════════════════
    parallel_meta = {8, 9} & steps_to_run
    if parallel_meta:
        print("━" * 50)
        print("⚡ STEPS 8+9: PARALLEL (SEO Metadata + Thumbnail)...")
        print("━" * 50)

        meta_start = time.time()

        if topic is None:
            topic = _load_json(run_dir, "selected_topic.json")
        if script is None:
            script = _load_json(run_dir, "script.json")

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}

            if 8 in steps_to_run:
                def _gen_metadata():
                    from modules.seo_metadata import SEOMetadataGenerator
                    seo_gen = SEOMetadataGenerator()
                    return seo_gen.generate_metadata(topic, script)
                futures[executor.submit(_gen_metadata)] = "metadata"

            if 9 in steps_to_run:
                def _gen_thumbnail():
                    thumb_text = "FUNNY!"
                    if topic:
                        thumb_text = topic.get("title", "FUNNY!")[:20]
                    from modules.thumbnail import ThumbnailGenerator
                    thumb_gen = ThumbnailGenerator()
                    return thumb_gen.generate_thumbnail(
                        title=thumb_text,
                        expression="surprised",
                        output_path=os.path.join(run_dir, "thumbnail.png")
                    )
                futures[executor.submit(_gen_thumbnail)] = "thumbnail"

            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    if task_name == "metadata":
                        metadata = result
                        print(f"   📌 Title: {metadata.get('title', 'N/A')}")
                        print(f"   🏷️  Tags: {len(metadata.get('tags', []))} tags")
                        save_json(metadata, os.path.join(run_dir, "metadata.json"))
                    elif task_name == "thumbnail":
                        thumbnail_path = result
                        print(f"   🖼️  Thumbnail: {thumbnail_path}")
                except Exception as e:
                    print(f"   ❌ {task_name} failed: {e}")

        elapsed = time.time() - meta_start
        print(f"   ⏱️  Parallel steps completed in {elapsed:.1f}s")
        print()

    # ═══════════════════════════════════════════════════════════
    # STEP 10: YouTube Upload
    # ═══════════════════════════════════════════════════════════
    if 10 in steps_to_run:
        print("━" * 50)
        print("📤 STEP 10: Uploading to YouTube...")
        print("━" * 50)

        with timed_step("YouTube Upload"):
            if not video_path or not os.path.exists(video_path):
                video_path = os.path.join(run_dir, "final_short.mp4")
            if metadata is None:
                metadata = _load_json(run_dir, "metadata.json")
            if not thumbnail_path:
                thumbnail_path = os.path.join(run_dir, "thumbnail.png")

            from modules.youtube_uploader import YouTubeUploader
            uploader = YouTubeUploader()

            result = uploader.upload_video(video_path, metadata, thumbnail_path)

            if "error" in result:
                print(f"   ❌ Upload failed: {result['error']}")
            else:
                print(f"   ✅ Uploaded: {result.get('url', 'N/A')}")
                save_json(result, os.path.join(run_dir, "upload_result.json"))
        print()

    # ═══════════════════════════════════════════════════════════
    # STEP 11: Excel Tracking
    # ═══════════════════════════════════════════════════════════
    print("━" * 50)
    print("📊 Logging to Excel Tracker...")
    print("━" * 50)

    tracker = ExcelTracker()
    run_id = os.path.basename(run_dir)

    pipeline_status = "Completed"
    if not video_path or not os.path.exists(str(video_path or "")):
        pipeline_status = "Partial"

    upload_result_data = None
    upload_result_path = os.path.join(run_dir, "upload_result.json")
    if os.path.exists(upload_result_path):
        upload_result_data = _load_json(run_dir, "upload_result.json")

    if topic is None:
        topic = _load_json(run_dir, "selected_topic.json")
    if script is None:
        script = _load_json(run_dir, "script.json")

    tracker.log_run(
        run_id=run_id,
        topic=topic,
        script=script,
        video_path=video_path,
        upload_result=upload_result_data,
        status=pipeline_status,
    )
    print()

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    total_time = time.time() - pipeline_start
    print("=" * 60)
    print("🎉  PIPELINE COMPLETE!")
    print(f"⚡  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print("=" * 60)
    print(f"\n📂 All outputs saved to:\n   {run_dir}\n")

    # List output files
    if os.path.exists(run_dir):
        print("📦 Output files:")
        for root, dirs, files in os.walk(run_dir):
            for f in sorted(files):
                filepath = os.path.join(root, f)
                size = os.path.getsize(filepath)
                size_str = f"{size / 1024:.1f}KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f}MB"
                rel = os.path.relpath(filepath, run_dir)
                print(f"   📄 {rel} ({size_str})")

    print()


def _load_json(run_dir, filename):
    """Load a JSON file from the run directory."""
    filepath = os.path.join(run_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _test_imports():
    """Test that all modules can be imported."""
    modules = [
        ("modules.topic_generator", "TopicGenerator"),
        ("modules.script_writer", "ScriptWriter"),
        ("modules.storyboard", "StoryboardCreator"),
        ("modules.scene_generator", "SceneGenerator"),
        ("modules.voiceover", "VoiceoverGenerator"),
        ("modules.music_sfx", "MusicSFXManager"),
        ("modules.video_editor", "VideoEditor"),
        ("modules.seo_metadata", "SEOMetadataGenerator"),
        ("modules.thumbnail", "ThumbnailGenerator"),
        ("modules.youtube_uploader", "YouTubeUploader"),
    ]
    for module_name, class_name in modules:
        try:
            mod = __import__(module_name, fromlist=[class_name])
            getattr(mod, class_name)
            print(f"  ✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Comedy Cartoon Automation Pipeline (ULTRA-OPTIMIZED)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        # Generate content (no upload)
  python main.py --auto                 # Full pipeline + YouTube upload
  python main.py --topic "cat pizza"    # Use a custom topic idea
  python main.py --steps 1,2,3         # Run only specific steps
  python main.py --dry-run             # Validate setup only
        """,
    )
    parser.add_argument("--auto", action="store_true",
                        help="Enable YouTube upload (Step 10)")
    parser.add_argument("--topic", type=str, default=None,
                        help="Custom topic idea (skips topic generation)")
    parser.add_argument("--steps", type=str, default=None,
                        help="Comma-separated step numbers to run (e.g., 1,2,3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate setup without making API calls")

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
