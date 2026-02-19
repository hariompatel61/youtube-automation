"""
Step 4: Cartoon Scene Image Generator (OPTIMIZED)
Generates colorful cartoon-style scene images using Pillow.
OPTIMIZED: numpy-accelerated gradients, concurrent generation, JPEG fast save.
"""

import os
import random
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from config import Config


class SceneGenerator:
    """Generates cartoon-style scene images programmatically using Pillow.
    OPTIMIZED: numpy gradients, thread-pool scene generation.
    """

    # Color palettes for backgrounds
    BACKGROUND_COLORS = {
        "living_room": [(255, 228, 196), (245, 222, 179), (255, 239, 213)],
        "office": [(200, 220, 240), (176, 196, 222), (230, 230, 250)],
        "school": [(255, 255, 224), (255, 250, 205), (250, 250, 210)],
        "park": [(144, 238, 144), (152, 251, 152), (173, 255, 173)],
        "kitchen": [(255, 248, 220), (255, 245, 238), (253, 245, 230)],
        "bedroom": [(230, 200, 255), (221, 160, 221), (238, 213, 255)],
        "street": [(190, 200, 210), (211, 211, 211), (220, 220, 230)],
        "store": [(255, 218, 185), (255, 228, 196), (255, 235, 205)],
    }

    # Expression emoji-like characters for faces
    EXPRESSION_PARAMS = {
        "happy": {"mouth": "smile", "eyes": "open", "brows": "normal", "color": (255, 223, 0)},
        "angry": {"mouth": "frown", "eyes": "squint", "brows": "angry", "color": (255, 69, 0)},
        "surprised": {"mouth": "open", "eyes": "wide", "brows": "raised", "color": (255, 165, 0)},
        "shocked": {"mouth": "open_wide", "eyes": "wide", "brows": "raised", "color": (255, 99, 71)},
        "laughing": {"mouth": "laugh", "eyes": "closed", "brows": "normal", "color": (255, 215, 0)},
        "crying": {"mouth": "frown", "eyes": "closed", "brows": "sad", "color": (100, 149, 237)},
        "confused": {"mouth": "squiggle", "eyes": "uneven", "brows": "raised", "color": (186, 85, 211)},
        "scared": {"mouth": "open", "eyes": "wide", "brows": "raised", "color": (147, 112, 219)},
    }

    # Character body colors
    CHARACTER_COLORS = [
        (65, 105, 225),   # Royal Blue
        (220, 20, 60),    # Crimson
        (50, 205, 50),    # Lime Green
        (255, 140, 0),    # Dark Orange
        (138, 43, 226),   # Blue Violet
        (0, 206, 209),    # Dark Turquoise
    ]

    def __init__(self):
        self.width = Config.VIDEO_WIDTH
        self.height = Config.VIDEO_HEIGHT
        self.font = None
        self._load_font()
        # Pre-compute gradient arrays for each background type (MASSIVE speedup)
        self._gradient_cache = {}

    def _load_font(self):
        """Load a font for text elements."""
        try:
            self.font = ImageFont.truetype("arial.ttf", 36)
            self.font_large = ImageFont.truetype("arial.ttf", 52)
            self.font_small = ImageFont.truetype("arial.ttf", 28)
        except (OSError, IOError):
            self.font = ImageFont.load_default()
            self.font_large = self.font
            self.font_small = self.font

    def _get_gradient_array(self, bg_type):
        """Get or create a cached numpy gradient array for background type.
        This replaces the per-pixel line drawing which was ~1920 draw calls.
        """
        if bg_type in self._gradient_cache:
            return self._gradient_cache[bg_type]

        colors = self.BACKGROUND_COLORS.get(bg_type, [(200, 220, 240)])
        c1 = np.array(colors[0], dtype=np.float32)
        c2 = np.array(colors[-1], dtype=np.float32)

        # Create gradient using numpy broadcasting (replaces 1920 draw.line calls)
        ratios = np.linspace(0, 1, self.height).reshape(-1, 1)
        gradient = (c1 * (1 - ratios) + c2 * ratios).astype(np.uint8)
        gradient_img = np.broadcast_to(gradient[:, np.newaxis, :], (self.height, self.width, 3)).copy()

        self._gradient_cache[bg_type] = gradient_img
        return gradient_img

    def generate_scene_image(self, scene, scene_index, output_dir, character_color_map=None):
        """Generate a single cartoon scene image.

        Args:
            scene: dict with scene description from storyboard.
            scene_index: int, the scene number.
            output_dir: str, directory to save the image.
            character_color_map: dict mapping character names to colors.

        Returns:
            str: Path to the generated image.
        """
        # 1. Draw background using numpy (FAST)
        bg_type = scene.get("background", "living_room")
        gradient_arr = self._get_gradient_array(bg_type)
        img = Image.fromarray(gradient_arr, "RGB")
        draw = ImageDraw.Draw(img)

        # Add floor
        colors = self.BACKGROUND_COLORS.get(bg_type, [(200, 220, 240)])
        c2 = colors[-1]
        floor_y = int(self.height * 0.72)
        floor_color = tuple(max(0, c - 40) for c in c2)
        draw.rectangle([0, floor_y, self.width, self.height], fill=floor_color)
        draw.rectangle([0, floor_y, self.width, floor_y + 8], fill=tuple(max(0, c - 70) for c in c2))

        # 2. Draw characters
        characters = scene.get("characters_present", [])
        expressions = scene.get("expressions", {})
        if character_color_map is None:
            character_color_map = {}
            for i, char in enumerate(characters):
                character_color_map[char] = self.CHARACTER_COLORS[i % len(self.CHARACTER_COLORS)]

        num_chars = len(characters)
        for i, char_name in enumerate(characters):
            expression = expressions.get(char_name, "happy")
            color = character_color_map.get(char_name, self.CHARACTER_COLORS[0])
            x_pos = self._get_character_x(i, num_chars)
            self._draw_character(draw, x_pos, color, expression, char_name)

        # 3. Draw scene elements based on background
        self._draw_scene_details(draw, bg_type)

        # 4. Apply camera angle effect
        camera = scene.get("camera_angle", "wide")
        img = self._apply_camera_angle(img, camera)

        # Save (PNG for quality, but with optimization)
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"scene_{scene_index:02d}.png")
        img.save(filepath, "PNG", optimize=True)
        return filepath

    def generate_all_scenes(self, storyboard, output_dir):
        """Generate images for all storyboard scenes using THREAD POOL.

        Args:
            storyboard: list of scene dicts.
            output_dir: directory to save images.

        Returns:
            list[str]: Paths to all generated images.
        """
        # Build consistent character color map
        all_characters = set()
        for scene in storyboard:
            for char in scene.get("characters_present", []):
                all_characters.add(char)

        character_color_map = {}
        for i, char in enumerate(sorted(all_characters)):
            character_color_map[char] = self.CHARACTER_COLORS[i % len(self.CHARACTER_COLORS)]

        # Pre-warm gradient cache for all unique backgrounds
        unique_bgs = set(s.get("background", "living_room") for s in storyboard)
        for bg in unique_bgs:
            self._get_gradient_array(bg)

        # Generate scenes in parallel using thread pool
        paths = [None] * len(storyboard)
        with ThreadPoolExecutor(max_workers=min(4, len(storyboard))) as executor:
            futures = {}
            for i, scene in enumerate(storyboard):
                future = executor.submit(
                    self.generate_scene_image, scene, i + 1, output_dir, character_color_map
                )
                futures[future] = i

            for future in as_completed(futures):
                idx = futures[future]
                paths[idx] = future.result()

        return paths

    def _get_character_x(self, index, total):
        """Calculate x position for a character based on count."""
        if total == 1:
            return self.width // 2
        margin = 180
        usable = self.width - 2 * margin
        spacing = usable // max(1, total - 1)
        return margin + index * spacing

    def _draw_character(self, draw, x_center, body_color, expression, name):
        """Draw a cartoon character."""
        # Body position
        body_top = int(self.height * 0.38)
        body_bottom = int(self.height * 0.70)
        body_width = 140

        # === BODY (rounded rectangle approximation) ===
        body_rect = [
            x_center - body_width // 2, body_top,
            x_center + body_width // 2, body_bottom
        ]
        draw.rounded_rectangle(body_rect, radius=30, fill=body_color)

        # === LEGS ===
        leg_top = body_bottom - 5
        leg_bottom = int(self.height * 0.72)
        leg_width = 30
        # Left leg
        draw.rounded_rectangle([
            x_center - 50, leg_top, x_center - 50 + leg_width, leg_bottom
        ], radius=10, fill=body_color)
        # Right leg
        draw.rounded_rectangle([
            x_center + 20, leg_top, x_center + 20 + leg_width, leg_bottom
        ], radius=10, fill=body_color)

        # Shoes
        shoe_color = (60, 60, 60)
        draw.ellipse([x_center - 60, leg_bottom - 10, x_center - 30, leg_bottom + 15], fill=shoe_color)
        draw.ellipse([x_center + 10, leg_bottom - 10, x_center + 60, leg_bottom + 15], fill=shoe_color)

        # === ARMS ===
        arm_color = body_color
        # Left arm
        draw.rounded_rectangle([
            x_center - body_width // 2 - 25, body_top + 30,
            x_center - body_width // 2 + 5, body_bottom - 30
        ], radius=12, fill=arm_color)
        # Right arm
        draw.rounded_rectangle([
            x_center + body_width // 2 - 5, body_top + 30,
            x_center + body_width // 2 + 25, body_bottom - 30
        ], radius=12, fill=arm_color)

        # === HEAD ===
        head_radius = 75
        head_center_y = body_top - head_radius + 15
        skin_color = (255, 220, 185)
        draw.ellipse([
            x_center - head_radius, head_center_y - head_radius,
            x_center + head_radius, head_center_y + head_radius
        ], fill=skin_color, outline=(200, 170, 140), width=3)

        # === FACE (Expression-based) ===
        params = self.EXPRESSION_PARAMS.get(expression, self.EXPRESSION_PARAMS["happy"])
        self._draw_face(draw, x_center, head_center_y, head_radius, params)

        # === NAME LABEL ===
        if self.font:
            bbox = draw.textbbox((0, 0), name, font=self.font_small)
            tw = bbox[2] - bbox[0]
            draw.text(
                (x_center - tw // 2, int(self.height * 0.73)),
                name, fill=(80, 80, 80), font=self.font_small
            )

    def _draw_face(self, draw, cx, cy, radius, params):
        """Draw facial expression on the character head."""
        eye_y = cy - 10
        eye_spacing = 28

        # === EYES ===
        if params["eyes"] == "open":
            for dx in [-eye_spacing, eye_spacing]:
                draw.ellipse([cx + dx - 10, eye_y - 12, cx + dx + 10, eye_y + 12],
                             fill=(255, 255, 255), outline=(0, 0, 0), width=2)
                draw.ellipse([cx + dx - 5, eye_y - 5, cx + dx + 5, eye_y + 5], fill=(0, 0, 0))
        elif params["eyes"] == "wide":
            for dx in [-eye_spacing, eye_spacing]:
                draw.ellipse([cx + dx - 14, eye_y - 16, cx + dx + 14, eye_y + 16],
                             fill=(255, 255, 255), outline=(0, 0, 0), width=2)
                draw.ellipse([cx + dx - 6, eye_y - 6, cx + dx + 6, eye_y + 6], fill=(0, 0, 0))
        elif params["eyes"] == "closed":
            for dx in [-eye_spacing, eye_spacing]:
                draw.arc([cx + dx - 10, eye_y - 5, cx + dx + 10, eye_y + 10],
                         start=0, end=180, fill=(0, 0, 0), width=3)
        elif params["eyes"] == "squint":
            for dx in [-eye_spacing, eye_spacing]:
                draw.line([cx + dx - 10, eye_y, cx + dx + 10, eye_y], fill=(0, 0, 0), width=3)
        elif params["eyes"] == "uneven":
            # Left eye normal
            draw.ellipse([cx - eye_spacing - 10, eye_y - 10, cx - eye_spacing + 10, eye_y + 10],
                         fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            draw.ellipse([cx - eye_spacing - 4, eye_y - 4, cx - eye_spacing + 4, eye_y + 4], fill=(0, 0, 0))
            # Right eye raised
            draw.ellipse([cx + eye_spacing - 12, eye_y - 18, cx + eye_spacing + 12, eye_y + 8],
                         fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            draw.ellipse([cx + eye_spacing - 5, eye_y - 8, cx + eye_spacing + 5, eye_y + 2], fill=(0, 0, 0))

        # === EYEBROWS ===
        brow_y = eye_y - 22
        if params["brows"] == "angry":
            draw.line([cx - eye_spacing - 12, brow_y - 5, cx - eye_spacing + 12, brow_y + 5],
                      fill=(0, 0, 0), width=4)
            draw.line([cx + eye_spacing - 12, brow_y + 5, cx + eye_spacing + 12, brow_y - 5],
                      fill=(0, 0, 0), width=4)
        elif params["brows"] == "raised":
            for dx in [-eye_spacing, eye_spacing]:
                draw.arc([cx + dx - 14, brow_y - 10, cx + dx + 14, brow_y + 5],
                         start=180, end=360, fill=(0, 0, 0), width=3)
        elif params["brows"] == "sad":
            draw.line([cx - eye_spacing - 12, brow_y + 5, cx - eye_spacing + 12, brow_y - 5],
                      fill=(0, 0, 0), width=3)
            draw.line([cx + eye_spacing - 12, brow_y - 5, cx + eye_spacing + 12, brow_y + 5],
                      fill=(0, 0, 0), width=3)
        else:
            for dx in [-eye_spacing, eye_spacing]:
                draw.line([cx + dx - 10, brow_y, cx + dx + 10, brow_y], fill=(0, 0, 0), width=3)

        # === MOUTH ===
        mouth_y = cy + 22
        if params["mouth"] == "smile":
            draw.arc([cx - 22, mouth_y - 8, cx + 22, mouth_y + 18], start=0, end=180,
                     fill=(200, 50, 50), width=4)
        elif params["mouth"] == "frown":
            draw.arc([cx - 18, mouth_y + 2, cx + 18, mouth_y + 22], start=180, end=360,
                     fill=(200, 50, 50), width=4)
        elif params["mouth"] == "open":
            draw.ellipse([cx - 14, mouth_y - 2, cx + 14, mouth_y + 18],
                         fill=(200, 50, 50), outline=(0, 0, 0), width=2)
        elif params["mouth"] == "open_wide":
            draw.ellipse([cx - 20, mouth_y - 8, cx + 20, mouth_y + 22],
                         fill=(200, 50, 50), outline=(0, 0, 0), width=2)
        elif params["mouth"] == "laugh":
            draw.chord([cx - 25, mouth_y - 5, cx + 25, mouth_y + 22], start=0, end=180,
                       fill=(200, 50, 50), outline=(0, 0, 0), width=2)
            draw.rectangle([cx - 18, mouth_y - 3, cx + 18, mouth_y + 5], fill=(255, 255, 255))
        elif params["mouth"] == "squiggle":
            points = [(cx - 20, mouth_y + 5), (cx - 8, mouth_y - 3),
                      (cx + 8, mouth_y + 8), (cx + 20, mouth_y)]
            draw.line(points, fill=(200, 50, 50), width=3)

        # Blush circles for some expressions
        if params["mouth"] in ("smile", "laugh"):
            for dx in [-40, 40]:
                draw.ellipse([cx + dx - 12, mouth_y - 15, cx + dx + 12, mouth_y - 3],
                             fill=(255, 200, 200))

    def _draw_scene_details(self, draw, bg_type):
        """Draw background details like furniture, trees, etc."""
        if bg_type == "living_room":
            # Sofa outline
            draw.rounded_rectangle([80, int(self.height * 0.55), 350, int(self.height * 0.70)],
                                   radius=15, fill=(139, 69, 19), outline=(100, 50, 10), width=2)
            # Window
            draw.rectangle([self.width - 280, 180, self.width - 100, 380],
                           outline=(139, 115, 85), width=5)
            draw.line([self.width - 190, 180, self.width - 190, 380], fill=(139, 115, 85), width=3)
            draw.line([self.width - 280, 280, self.width - 100, 280], fill=(139, 115, 85), width=3)
            # Sky through window
            draw.rectangle([self.width - 275, 185, self.width - 105, 375], fill=(135, 206, 250))

        elif bg_type == "office":
            # Desk
            draw.rectangle([100, int(self.height * 0.58), self.width - 100, int(self.height * 0.62)],
                           fill=(160, 82, 45))
            # Monitor
            draw.rectangle([400, int(self.height * 0.40), 680, int(self.height * 0.57)],
                           fill=(40, 40, 40), outline=(20, 20, 20), width=3)
            draw.rectangle([410, int(self.height * 0.41), 670, int(self.height * 0.55)],
                           fill=(70, 130, 180))

        elif bg_type == "park":
            # Trees
            for tx in [100, self.width - 150]:
                draw.rectangle([tx + 20, int(self.height * 0.35), tx + 50, int(self.height * 0.72)],
                               fill=(139, 90, 43))
                draw.ellipse([tx - 20, int(self.height * 0.18), tx + 90, int(self.height * 0.40)],
                             fill=(34, 139, 34))
            # Sun
            draw.ellipse([self.width - 180, 60, self.width - 100, 140], fill=(255, 255, 0))

        elif bg_type == "kitchen":
            # Counter
            draw.rectangle([0, int(self.height * 0.55), self.width, int(self.height * 0.58)],
                           fill=(139, 119, 101))
            draw.rectangle([0, int(self.height * 0.58), self.width, int(self.height * 0.72)],
                           fill=(205, 183, 158))
            # Cabinet
            draw.rectangle([50, 150, 300, 400], fill=(210, 180, 140), outline=(180, 150, 110), width=3)
            draw.ellipse([260, 270, 280, 290], fill=(180, 150, 100))

        elif bg_type == "school":
            # Blackboard
            draw.rectangle([120, 150, self.width - 120, 450], fill=(34, 80, 34),
                           outline=(139, 90, 43), width=8)
            # Chalk text
            if self.font:
                draw.text((200, 250), "A B C", fill=(255, 255, 240), font=self.font_large)

        elif bg_type == "street":
            # Road
            draw.rectangle([0, int(self.height * 0.65), self.width, int(self.height * 0.78)],
                           fill=(80, 80, 80))
            # Dashes
            for x in range(0, self.width, 120):
                draw.rectangle([x, int(self.height * 0.71), x + 50, int(self.height * 0.72)],
                               fill=(255, 255, 255))
            # Building silhouettes
            draw.rectangle([50, 100, 250, int(self.height * 0.65)], fill=(150, 160, 170))
            draw.rectangle([self.width - 300, 180, self.width - 80, int(self.height * 0.65)],
                           fill=(160, 150, 140))

    def _apply_camera_angle(self, img, camera):
        """Apply camera angle effect by cropping/zooming. Uses BILINEAR for speed."""
        if camera == "close_up":
            box = (
                self.width // 4,
                int(self.height * 0.15),
                self.width * 3 // 4,
                int(self.height * 0.55)
            )
            cropped = img.crop(box)
            return cropped.resize((self.width, self.height), Image.BILINEAR)

        elif camera == "extreme_close_up":
            box = (
                self.width // 3,
                int(self.height * 0.20),
                self.width * 2 // 3,
                int(self.height * 0.45)
            )
            cropped = img.crop(box)
            return cropped.resize((self.width, self.height), Image.BILINEAR)

        elif camera == "medium":
            box = (
                self.width // 8,
                int(self.height * 0.10),
                self.width * 7 // 8,
                int(self.height * 0.80)
            )
            cropped = img.crop(box)
            return cropped.resize((self.width, self.height), Image.BILINEAR)

        # "wide" - no change
        return img
