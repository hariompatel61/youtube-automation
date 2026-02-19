"""
Step 8: SEO Metadata Generator
Generates viral titles, descriptions, tags, and hashtags using Gemini API.
"""

import json
from modules.llm_client import LLMClient
from config import Config


class SEOMetadataGenerator:
    """Generates SEO-optimized YouTube metadata for comedy shorts."""

    PROMPT_TEMPLATE = """You are a YouTube SEO expert specializing in viral comedy Shorts.

Generate SEO-optimized metadata for this comedy cartoon YouTube Short:

TOPIC: {title}
PREMISE: {premise}
SCRIPT HOOK: {hook}

Provide:
1. title - Viral, curiosity-driven, max 60 characters. Use power words, emojis optional.
2. description - 150-200 words with keywords naturally included. Add 5 relevant hashtags at the end.
3. tags - 15-20 relevant tags for YouTube search (comedy shorts, cartoon shorts, funny story, etc.)
4. hashtags - Top 8 hashtags for maximum reach

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "title": "Your viral title here",
  "description": "Full description with hashtags at end...",
  "tags": ["tag1", "tag2", "tag3"],
  "hashtags": ["#FunnyShorts", "#ComedyCartoon"]
}}
"""

    def __init__(self):
        self.client = LLMClient()



    def generate_metadata(self, topic, script):
        """Generate SEO metadata for the video.

        Args:
            topic: dict with 'title' and 'premise'.
            script: dict with 'hook'.

        Returns:
            dict: With 'title', 'description', 'tags', 'hashtags'.
        """
        prompt = self.PROMPT_TEMPLATE.format(
            title=topic.get("title", "Funny Cartoon"),
            premise=topic.get("premise", "A funny situation"),
            hook=script.get("hook", "Wait for it..."),
        )

        metadata = self.client.generate_json(prompt)

        # Validate title length
        if len(metadata.get("title", "")) > 60:
            metadata["title"] = metadata["title"][:57] + "..."

        return metadata
