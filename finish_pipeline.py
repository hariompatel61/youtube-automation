import os
import json
import sys
from modules.seo_metadata import SEOMetadataGenerator
from modules.thumbnail import ThumbnailGenerator
from modules.youtube_uploader import YouTubeUploader
from config import Config

def finish_run():
    run_dir = r"c:\Users\Hariom_patel\Desktop\automate\output\run_20260219_163849"
    
    print(f"Resuming run in: {run_dir}")

    # Load data
    with open(os.path.join(run_dir, "selected_topic.json"), "r", encoding="utf-8") as f:
        topic = json.load(f)
    with open(os.path.join(run_dir, "script.json"), "r", encoding="utf-8") as f:
        script = json.load(f)
        
    # Step 8: Metadata
    print("Generating Metadata...")
    meta_gen = SEOMetadataGenerator()
    metadata = meta_gen.generate_metadata(topic, script)
    with open(os.path.join(run_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print("Metadata saved.")

    # Step 9: Thumbnail
    print("Generating Thumbnail...")
    thumb_gen = ThumbnailGenerator()
    thumb_path = thumb_gen.generate_thumbnail(
        title=topic.get("title", "Funny Cartoon"),
        expression="surprised",
        output_path=os.path.join(run_dir, "thumbnail.png")
    )
    print(f"Thumbnail saved to {thumb_path}")

    # Step 10: Upload
    print("Uploading to YouTube...")
    video_path = os.path.join(run_dir, "final_short.mp4")
    uploader = YouTubeUploader()
    if os.path.exists(video_path):
        result = uploader.upload_video(video_path, metadata, thumb_path)
        print("Upload Result:", result)
        with open(os.path.join(run_dir, "upload_result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    else:
        print("Error: final_short.mp4 not found!")

if __name__ == "__main__":
    finish_run()
