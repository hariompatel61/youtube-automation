"""
Step 1: Topic Generator
Generates engaging animated story ideas with dynamic duration.
Themes: animals, robots+kids, comedy-tech, daily life comedy.
"""

import json
from modules.llm_client import LLMClient
from config import Config


class TopicGenerator:
    """Generates viral animated story topics with suggested duration."""

    PROMPT_TEMPLATE = """You are a creative YouTube animation content writer. Generate {count} unique,
entertaining animated story ideas. Each story should be suitable for animated videos
between 30 seconds to 5 minutes long.

Story themes to draw from: {categories}

IMPORTANT: For each idea, decide the ideal video duration based on story complexity:
- Simple gags / quick jokes → 30-60 seconds
- Short story arcs → 60-180 seconds (1-3 minutes)
- Complex narratives with character development → 180-300 seconds (3-5 minutes)

For each idea, provide:
1. title - A catchy, engaging title (max 10 words)
2. category - Which theme it fits
3. premise - 2-3 sentence description of the story
4. humor_type - Type of humor (slapstick, irony, absurd, relatable, wordplay, heartwarming)
5. viral_score - Rate 1-10 how viral/shareable this idea is
6. suggested_duration - Duration in seconds (30, 60, 90, 120, 180, 240, or 300)
7. characters - List of main character names and types

Return ONLY valid JSON array. No markdown, no code blocks. Example format:
[
  {{
    "title": "Robot Learns to Make Pancakes",
    "category": "robots and kids",
    "premise": "A kitchen robot tries to make breakfast for a little girl but keeps mixing up ingredients. Flour everywhere, eggs on the ceiling, but the girl thinks it's the best morning ever.",
    "humor_type": "slapstick",
    "viral_score": 9,
    "suggested_duration": 120,
    "characters": ["RoboChef", "Lily", "Dad"]
  }}
]
"""

    def __init__(self):
        self.client = LLMClient()

    def generate_topics(self, count=5):
        """Generate animated story topic ideas with suggested duration.

        Args:
            count: Number of topics to generate.

        Returns:
            list[dict]: List of topic dictionaries with suggested_duration.
        """
        categories = ", ".join(Config.TOPIC_CATEGORIES)
        prompt = self.PROMPT_TEMPLATE.format(count=count, categories=categories)

        topics = self.client.generate_json(prompt)

        # Handle case where LLM returns a single dict instead of a list
        if isinstance(topics, dict):
            for key in ("topics", "ideas", "results"):
                if key in topics and isinstance(topics[key], list):
                    topics = topics[key]
                    break
            else:
                topics = [topics]

        # Handle string response
        if isinstance(topics, str):
            try:
                topics = json.loads(topics)
            except (json.JSONDecodeError, ValueError):
                topics = [{
                    "title": topics[:50],
                    "category": "comedy",
                    "premise": topics,
                    "humor_type": "absurd",
                    "viral_score": 7,
                    "suggested_duration": 60,
                    "characters": ["Character1", "Character2"],
                }]

        # Ensure each topic has a suggested_duration
        for topic in topics:
            if "suggested_duration" not in topic:
                # Default: estimate from premise length
                premise_len = len(topic.get("premise", ""))
                if premise_len > 150:
                    topic["suggested_duration"] = 180
                elif premise_len > 80:
                    topic["suggested_duration"] = 90
                else:
                    topic["suggested_duration"] = 60
            # Clamp to valid range
            topic["suggested_duration"] = max(
                Config.VIDEO_DURATION_MIN,
                min(Config.VIDEO_DURATION_MAX, topic["suggested_duration"])
            )

        # Sort by viral_score descending
        topics.sort(key=lambda t: t.get("viral_score", 0), reverse=True)
        return topics

    def pick_best_topic(self, topics=None):
        """Generate topics and return the best one.

        Args:
            topics: Optional pre-generated topics list.

        Returns:
            dict: The highest-rated topic.
        """
        if topics is None:
            topics = self.generate_topics()
        return topics[0]

    def generate_from_custom(self, custom_topic):
        """Structure a user-provided custom topic.

        Args:
            custom_topic: A string describing the topic.

        Returns:
            dict: Structured topic dictionary with suggested_duration.
        """
        prompt = f"""Take this animated video idea and structure it as JSON:
Topic: {custom_topic}

Return ONLY valid JSON (no markdown). Format:
{{
  "title": "Short catchy title",
  "category": "best fitting category",
  "premise": "2-3 sentence story description",
  "humor_type": "type of humor",
  "viral_score": 8,
  "suggested_duration": 120,
  "characters": ["Character1", "Character2"]
}}"""

        result = self.client.generate_json(prompt)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, ValueError):
                result = {
                    "title": custom_topic[:50],
                    "category": "comedy",
                    "premise": custom_topic,
                    "humor_type": "absurd",
                    "viral_score": 7,
                    "suggested_duration": 90,
                    "characters": ["Character1", "Character2"],
                }
        if "suggested_duration" not in result:
            result["suggested_duration"] = 90
        return result
