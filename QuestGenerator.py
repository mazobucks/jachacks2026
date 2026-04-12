import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google import genai
from Quests import Quest

# Initialize the client - ensuring the API key is handled correctly
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class QuestGenerator:
    """Enhanced study quest generator using Gemini's structured output features."""

    @staticmethod
    def generate_quests(
        goal_name: str,
        exam_subject: str,
        exam_date: str,
        hours_willing: float,
        themes: List[str],
        days_before_exam: int = 21,  # Increased window for better distribution
    ) -> List[Quest]:
        """
        Generate a list of Quest objects using structured JSON output.
        """
        if not themes:
            raise ValueError("At least one theme must be provided")
        if hours_willing <= 0:
            raise ValueError("hours_willing must be positive")
        
        try:
            exam_dt = datetime.fromisoformat(exam_date)
        except ValueError:
            raise ValueError(f"Invalid date format: {exam_date}. Use YYYY-MM-DD.")
        
        earliest_date = exam_dt - timedelta(days=days_before_exam)
        # Ensure we don't start in the past
        today = datetime.now()
        if earliest_date < today:
            earliest_date = today

        prompt = QuestGenerator._build_prompt(
            goal_name=goal_name,
            exam_subject=exam_subject,
            exam_date=exam_date,
            hours_willing=hours_willing,
            themes=themes,
            earliest_date=earliest_date.strftime("%Y-%m-%d"),
        )

        try:
            # We use response_mime_type to force JSON output without backticks
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                }
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response. Check safety settings or API status.")

            data = json.loads(response.text)
            
            # Defensive check for the expected root key
            quests_list = data.get("quests", [])
            
            quests = []
            for q in quests_list:
                # Map structured data to the Quest object
                quests.append(Quest(
                    name=q["name"],
                    theme=q["theme"],
                    study_time=float(q["study_time"]),
                    date=q["date"],
                    xp_reward=int(q.get("xp_reward", 50)),
                    stat_points=q.get("stat_points", {"intelligence": 1}),
                    description=q.get("description", "")
                ))
            
            return quests

        except Exception as e:
            # If the JSON is invalid or key missing, we log it and raise
            print(f"Generation Error: {str(e)}")
            raise ValueError(f"Failed to generate study plan: {e}")

    @staticmethod
    def _build_prompt(goal_name, exam_subject, exam_date, hours_willing, themes, earliest_date):
        themes_str = ", ".join(themes)
        return f"""
        Act as an expert Academic Coach. Design a high-impact study curriculum.
        
        CONTEXT:
        - Goal: {goal_name} ({exam_subject})
        - Deadline: {exam_date}
        - Total Budget: {hours_willing} hours
        - Core Topics: {themes_str}
        - Start Date: {earliest_date}

        STRATEGY:
        1. Distribution: Spread the {hours_willing} hours across the time remaining.
        2. Progression: Start with foundational concepts, move to applications, and end with review/mock tests.
        3. Variety: Ensure every theme ({themes_str}) is addressed at least once.
        4. Engagement: Give quests "RPG-style" names (e.g., "The Foundations of {themes[0]}", "Mastering the {themes[0]} Trial").
        5. Gamification: Harder quests (longer hours) should have higher xp_reward (up to 200).

        OUTPUT FORMAT (JSON):
        {{
            "quests": [
                {{
                    "name": "string",
                    "theme": "string (must be from the Core Topics list)",
                    "study_time": number (between 1.0 and 6.0),
                    "date": "YYYY-MM-DD",
                    "xp_reward": integer,
                    "stat_points": {{"intelligence": integer, "focus": integer, "willpower": integer}},
                    "description": "string"
                }}
            ]
        }}
        """

    @staticmethod
    def validate_quests(quests: List[Quest], expected_hours: float):
        """Simple validation check for the UI."""
        total = sum(q.study_time for q in quests)
        return {
            "valid": len(quests) > 0 and (0.8 * expected_hours <= total <= 1.2 * expected_hours),
            "total_hours": round(total, 1),
            "count": len(quests)
        }