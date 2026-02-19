"""
Step 9: Thumbnail Generator (OPTIMIZED)
Creates eye-catching YouTube thumbnails with cartoon characters and bold text.
OPTIMIZED: numpy gradient backgrounds, faster rendering.
"""

import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import Config


class ThumbnailGenerator:
    """Creates bright, engaging YouTube thumbnails for comedy shorts."""

    # High contrast color pairs (background gradient, text color)
    COLOR_SCHEMES = [
        {"bg1": (255, 50, 50), "bg2": (255, 150, 0), "text": (255, 255, 255), "outline": (0, 0, 0)},
        {"bg1": (0, 200, 255), "bg2": (100, 0, 255), "text": (255, 255, 0), "outline": (0, 0, 0)},
        {"bg1": (255, 0, 150), "bg2": (100, 0, 255), "text": (255, 255, 255), "outline": (30, 0, 60)},
        {"bg1": (50, 200, 50), "bg2": (0, 100, 200), "text": (255, 255, 0), "outline": (0, 50, 0)},
        {"bg1": (255, 200, 0), "bg2": (255, 50, 0), "text": (255, 255, 255), "outline": (100, 30, 0)},
    ]

    THUMB_WIDTH = 1280
    THUMB_HEIGHT = 720

    def __init__(self):
        self.font = None
        self.font_large = None
        self._load_fonts()

    def _load_fonts(self):
        """Load fonts for thumbnail text."""
        try:
            self.font_large = ImageFont.truetype("arialbd.ttf", 90)
            self.font_medium = ImageFont.truetype("arialbd.ttf", 50)
        except (OSError, IOError):
            try:
                self.font_large = ImageFont.truetype("arial.ttf", 90)
                self.font_medium = ImageFont.truetype("arial.ttf", 50)
            except (OSError, IOError):
                self.font_large = ImageFont.load_default()
                self.font_medium = ImageFont.load_default()

    def generate_thumbnail(self, title, expression="surprised", output_path=None):
        """Generate a YouTube thumbnail.

        Args:
            title: Short text for the thumbnail (3-4 words ideal).
            expression: Character expression for the face.
            output_path: Where to save the thumbnail PNG.

        Returns:
            str: Path to the generated thumbnail.
        """
        if output_path is None:
            output_path = os.path.join(Config.OUTPUT_DIR, "thumbnail.png")

        # Random color scheme
        scheme = random.choice(self.COLOR_SCHEMES)

        # 1. Draw gradient background using NUMPY (replaces 720 draw.line calls)
        img = self._create_gradient_bg_fast(scheme)
        draw = ImageDraw.Draw(img)

        # 2. Add radial burst lines for energy
        self._draw_burst_lines(draw, scheme)

        # 3. Draw large cartoon face (right side)
        self._draw_large_face(draw, expression, scheme)

        # 4. Add bold text (left side)
        self._draw_title_text(draw, title, scheme)

        # 5. Add border glow
        self._add_border(draw, scheme)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "PNG", optimize=True)
        return output_path

    def _create_gradient_bg_fast(self, scheme):
        """Create gradient background using numpy (replaces per-line drawing)."""
        c1 = np.array(scheme["bg1"], dtype=np.float32)
        c2 = np.array(scheme["bg2"], dtype=np.float32)

        ratios = np.linspace(0, 1, self.THUMB_HEIGHT).reshape(-1, 1)
        gradient = (c1 * (1 - ratios) + c2 * ratios).astype(np.uint8)
        gradient_img = np.broadcast_to(
            gradient[:, np.newaxis, :], (self.THUMB_HEIGHT, self.THUMB_WIDTH, 3)
        ).copy()

        return Image.fromarray(gradient_img, "RGB")

    def _draw_burst_lines(self, draw, scheme):
        """Draw radiating lines from center-right for dynamic feel."""
        cx = self.THUMB_WIDTH * 3 // 4
        cy = self.THUMB_HEIGHT // 2
        burst_color = tuple(min(255, c + 40) for c in scheme["bg1"])

        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            x2 = int(cx + 800 * math.cos(rad))
            y2 = int(cy + 800 * math.sin(rad))
            draw.line([(cx, cy), (x2, y2)], fill=burst_color, width=3)

    def _draw_large_face(self, draw, expression, scheme):
        """Draw a large cartoon face on the right side of the thumbnail."""
        cx = self.THUMB_WIDTH * 3 // 4
        cy = self.THUMB_HEIGHT // 2
        radius = 180

        # Head
        skin_color = (255, 220, 185)
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=skin_color, outline=(0, 0, 0), width=5
        )

        # Eyes based on expression
        eye_y = cy - 30
        eye_spacing = 55

        if expression in ("surprised", "shocked", "scared"):
            # Wide eyes
            for dx in [-eye_spacing, eye_spacing]:
                draw.ellipse(
                    [cx + dx - 28, eye_y - 32, cx + dx + 28, eye_y + 32],
                    fill=(255, 255, 255), outline=(0, 0, 0), width=4
                )
                draw.ellipse(
                    [cx + dx - 12, eye_y - 12, cx + dx + 12, eye_y + 12],
                    fill=(0, 0, 0)
                )
                # Shine
                draw.ellipse(
                    [cx + dx - 6, eye_y - 22, cx + dx + 2, eye_y - 14],
                    fill=(255, 255, 255)
                )
        elif expression in ("laughing", "happy"):
            # Closed happy eyes
            for dx in [-eye_spacing, eye_spacing]:
                draw.arc(
                    [cx + dx - 25, eye_y - 10, cx + dx + 25, eye_y + 20],
                    start=0, end=180, fill=(0, 0, 0), width=5
                )
        elif expression in ("angry",):
            # Squint eyes with angry brows
            for dx in [-eye_spacing, eye_spacing]:
                draw.ellipse(
                    [cx + dx - 20, eye_y - 15, cx + dx + 20, eye_y + 15],
                    fill=(255, 255, 255), outline=(0, 0, 0), width=3
                )
                draw.ellipse(
                    [cx + dx - 8, eye_y - 8, cx + dx + 8, eye_y + 8],
                    fill=(0, 0, 0)
                )
            # Angry brows
            draw.line([cx - eye_spacing - 25, eye_y - 40, cx - eye_spacing + 25, eye_y - 25],
                      fill=(0, 0, 0), width=6)
            draw.line([cx + eye_spacing - 25, eye_y - 25, cx + eye_spacing + 25, eye_y - 40],
                      fill=(0, 0, 0), width=6)
        else:
            # Default open eyes
            for dx in [-eye_spacing, eye_spacing]:
                draw.ellipse(
                    [cx + dx - 22, eye_y - 25, cx + dx + 22, eye_y + 25],
                    fill=(255, 255, 255), outline=(0, 0, 0), width=3
                )
                draw.ellipse(
                    [cx + dx - 10, eye_y - 10, cx + dx + 10, eye_y + 10],
                    fill=(0, 0, 0)
                )

        # Eyebrows (if not drawn above)
        if expression not in ("angry",):
            brow_y = eye_y - 45
            if expression in ("surprised", "shocked"):
                for dx in [-eye_spacing, eye_spacing]:
                    draw.arc([cx + dx - 28, brow_y - 15, cx + dx + 28, brow_y + 10],
                             start=180, end=360, fill=(0, 0, 0), width=5)
            else:
                for dx in [-eye_spacing, eye_spacing]:
                    draw.line([cx + dx - 20, brow_y, cx + dx + 20, brow_y],
                              fill=(0, 0, 0), width=5)

        # Mouth
        mouth_y = cy + 50
        if expression in ("surprised", "shocked"):
            draw.ellipse([cx - 35, mouth_y - 15, cx + 35, mouth_y + 35],
                         fill=(200, 50, 50), outline=(0, 0, 0), width=4)
        elif expression in ("laughing", "happy"):
            draw.chord([cx - 45, mouth_y - 15, cx + 45, mouth_y + 40],
                       start=0, end=180, fill=(200, 50, 50), outline=(0, 0, 0), width=4)
            draw.rectangle([cx - 30, mouth_y - 10, cx + 30, mouth_y + 5],
                           fill=(255, 255, 255))
        elif expression == "angry":
            draw.arc([cx - 30, mouth_y + 5, cx + 30, mouth_y + 35],
                     start=180, end=360, fill=(0, 0, 0), width=5)
        else:
            draw.arc([cx - 30, mouth_y - 5, cx + 30, mouth_y + 25],
                     start=0, end=180, fill=(200, 50, 50), width=5)

        # Blush
        for dx in [-80, 80]:
            draw.ellipse([cx + dx - 20, mouth_y - 25, cx + dx + 20, mouth_y - 5],
                         fill=(255, 200, 200))

    def _draw_title_text(self, draw, title, scheme):
        """Draw bold title text on the left side of the thumbnail."""
        # Split title into max 2 lines
        words = title.upper().split()
        if len(words) <= 2:
            lines = [" ".join(words)]
        else:
            mid = len(words) // 2
            lines = [" ".join(words[:mid]), " ".join(words[mid:])]

        text_color = scheme["text"]
        outline_color = scheme["outline"]

        y = self.THUMB_HEIGHT // 2 - len(lines) * 55
        for line in lines:
            # Draw text outline (shadow effect) — reduced iterations for speed
            for dx in range(-3, 4, 3):
                for dy in range(-3, 4, 3):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((60 + dx, y + dy), line, fill=outline_color, font=self.font_large)
            # Draw main text
            draw.text((60, y), line, fill=text_color, font=self.font_large)
            y += 110

    def _add_border(self, draw, scheme):
        """Add a colored border around the thumbnail."""
        border_color = scheme["text"]
        w = self.THUMB_WIDTH - 1
        h = self.THUMB_HEIGHT - 1
        for i in range(5):
            draw.rectangle([i, i, w - i, h - i], outline=border_color, width=1)
