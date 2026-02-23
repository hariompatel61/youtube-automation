import os
import json
from modules.video_editor import VideoEditor
from config import Config

def debug_assembly():
    run_dir = r"c:\Users\Hariom_patel\Desktop\automate\output\run_20260219_163849"
    
    # Load assets
    with open(os.path.join(run_dir, "storyboard.json"), "r", encoding="utf-8") as f:
        storyboard = json.load(f)
        
    with open(os.path.join(run_dir, "script.json"), "r", encoding="utf-8") as f:
        script = json.load(f)

    scenes_dir = os.path.join(run_dir, "scenes")
    scene_paths = sorted([os.path.join(scenes_dir, f) for f in os.listdir(scenes_dir) if f.endswith(".png")])
    
    vo_dir = os.path.join(run_dir, "voiceovers")
    voiceover_paths = sorted([os.path.join(vo_dir, f) for f in os.listdir(vo_dir) if f.endswith(".mp3")])
    
    bgm_path = os.path.join(run_dir, "bgm.wav")
    sfx_paths = {} # Simplified for debug
    
    output_path = os.path.join(run_dir, "debug_output.mp4")
    
    print(f"Debug: Assembling video to {output_path}")
    print(f"Scenes: {len(scene_paths)}")
    print(f"VOs: {len(voiceover_paths)}")
    
    editor = VideoEditor()
    editor.assemble_video(
        storyboard=storyboard,
        scene_image_paths=scene_paths,
        voiceover_paths=voiceover_paths,
        bgm_path=bgm_path,
        sfx_paths=sfx_paths,
        hook_text=script.get("hook", "Debug Hook"),
        output_path=output_path,
        duration=script.get("target_duration", 60)
    )
    print("Debug: Assembly complete.")

if __name__ == "__main__":
    debug_assembly()
