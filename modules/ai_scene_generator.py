"""
Step 4: AI Scene Generator (Pollinations.ai)
Generates high-quality 3D Disney-style images using the free Pollinations API.
"""

import os
import time
import requests
import random
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config


class AISceneGenerator:
    """Generates scenes using Pollinations.ai (Free AI Image API)."""

    def __init__(self):
        self.width = Config.VIDEO_WIDTH
        self.height = Config.VIDEO_HEIGHT
        self.model = Config.POLLINATIONS_MODEL
        # Pollinations uses 1080x1920 for vertical. 
        # API format: https://pollinations.ai/p/{prompt}?width={w}&height={h}&model={model}&seed={seed}

    def generate_scene_image(self, scene, scene_index, output_dir):
        """Generate a single scene image using AI."""
        
        # Construct the prompt
        description = scene.get("description", "A funny cartoon scene")
        characters = ", ".join(scene.get("characters_present", ["cartoon character"]))
        
        # Get dominant expression
        expressions = scene.get("expressions", {})
        expression = "neutral"
        if expressions:
            expression = list(expressions.values())[0]

        camera = scene.get("camera_angle", "cinematic shot")
        
        prompt = Config.SCENE_PROMPT_TEMPLATE.format(
            scene_description=description,
            characters=characters,
            expression=expression,
            camera_angle=camera
        )

        # Optimize prompt for URL
        encoded_prompt = quote(prompt)
        seed = random.randint(1000, 999999)
        
        # Use image.pollinations.ai for direct image file
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={self.width}&height={self.height}"
            f"&model={self.model}&seed={seed}&nologo=true"
        )

        return self._download_image(url, scene_index, output_dir, scene)

    def _download_image(self, url, index, output_dir, scene):
        """Download image from URL with retries, fallback to 2D generator."""
        filepath = os.path.join(output_dir, f"scene_{index:02d}.jpg")
        os.makedirs(output_dir, exist_ok=True)

        for attempt in range(3):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return filepath
            except Exception:
                pass
            time.sleep(2)

        # Fallback to 2D generator if AI fails
        print(f"   ⚠️  AI generation failed for scene {index}. Using 2D fallback.")
        return self._generate_fallback(scene, index, output_dir)

    def _generate_fallback(self, scene, index, output_dir):
        """Use the basic SceneGenerator (Pillow) as fallback."""
        try:
            from modules.scene_generator import SceneGenerator
            fallback_gen = SceneGenerator()
            # SceneGenerator returns a path, usually .png
            return fallback_gen.generate_scene_image(scene, index, output_dir)
        except Exception as e:
            print(f"   ❌ Fallback generation failed: {e}")
            return None

    def generate_all_scenes(self, storyboard, output_dir):
        """Generate all scenes in parallel."""
        paths = [None] * len(storyboard)
        
        print(f"   🎨 generating {len(storyboard)} scenes using AI ({self.model})...")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for i, scene in enumerate(storyboard):
                future = executor.submit(self.generate_scene_image, scene, i + 1, output_dir)
                futures[future] = i

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    path = future.result()
                    if path:
                        paths[idx] = path
                        print(f"     ✅ Scene {idx+1} generated")
                except Exception as e:
                    print(f"     ❌ Scene {idx+1} failed: {e}")

        # Filter out failed generations
        valid_paths = [p for p in paths if p is not None]
        return valid_paths
