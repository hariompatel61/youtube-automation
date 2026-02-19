"""Upload the latest generated video to YouTube."""
import os
import sys
import json

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Find the latest run directory
output_dir = os.path.join(os.path.dirname(__file__), "output")
runs = sorted([d for d in os.listdir(output_dir) if d.startswith("run_")])
if not runs:
    print("❌ No runs found in output/")
    exit(1)

run_dir = os.path.join(output_dir, runs[-1])
print(f"📂 Using latest run: {runs[-1]}")

video_path = os.path.join(run_dir, "final_short.mp4")
thumbnail_path = os.path.join(run_dir, "thumbnail.png")
metadata_path = os.path.join(run_dir, "metadata.json")

# Check files exist
for path, label in [(video_path, "Video"), (thumbnail_path, "Thumbnail"), (metadata_path, "Metadata")]:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  ✅ {label}: {path} ({size / 1024:.1f}KB)")
    else:
        print(f"  ❌ {label} not found: {path}")
        exit(1)

# Load metadata
with open(metadata_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"\n📌 Title: {metadata.get('title', 'N/A')}")
print(f"📝 Description: {metadata.get('description', 'N/A')[:100]}...")
print(f"🏷️  Tags: {len(metadata.get('tags', []))} tags")

# Upload
print("\n📤 Starting YouTube upload...")
from modules.youtube_uploader import YouTubeUploader
uploader = YouTubeUploader()
result = uploader.upload_video(video_path, metadata, thumbnail_path)

if "error" in result:
    print(f"\n❌ Upload failed: {result['error']}")
else:
    print(f"\n✅ Uploaded successfully!")
    print(f"   🔗 URL: {result.get('url', 'N/A')}")
    print(f"   📋 Video ID: {result.get('video_id', 'N/A')}")
    # Save result
    result_path = os.path.join(run_dir, "upload_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"   💾 Saved: {result_path}")
