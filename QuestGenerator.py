import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google import genai
from Quests import Quest

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class QuestGenerator:
    """Generate study quests for a Goal using Gemini API.
    
    This class takes a Goal's constraints (exam date, total hours, themes)
    and generates a structured study plan with multiple quests that:
    - Fit within the total study hours willing to commit
    - Have dates before the exam date
    - Cover all themes appropriately
    - Are generated with Gemini AI for relevance
    """

    @staticmethod
    def generate_quests(
        goal_name: str,
        exam_subject: str,
        exam_date: str,  # ISO format: "2026-06-15"
        hours_willing: float,
        themes: List[str],
        days_before_exam: int = 14,  # Generate quest dates within this many days before exam
    ) -> List[Quest]:
        """
        Generate a list of Quest objects for a goal.
        
        Args:
            goal_name: Name of the goal/exam
            exam_subject: Subject being studied
            exam_date: ISO format date string (e.g., "2026-06-15")
            hours_willing: Total hours the user is willing to study
            themes: List of topics/themes to cover (e.g., ["Algebra", "Geometry"])
            days_before_exam: How many days before exam to schedule quests
        
        Returns:
            List of Quest objects ready to be saved to database
        
        Raises:
            ValueError: If Gemini API returns invalid JSON or missing fields
        """
        
        # Validate inputs
        if not themes or len(themes) == 0:
            raise ValueError("At least one theme must be provided")
        if hours_willing <= 0:
            raise ValueError("hours_willing must be positive")
        
        try:
            exam_dt = datetime.fromisoformat(exam_date)
        except ValueError:
            raise ValueError(f"Invalid exam_date format: {exam_date}. Use ISO format (YYYY-MM-DD)")
        
        # Calculate earliest date for quests
        earliest_date = exam_dt - timedelta(days=days_before_exam)
        
        # Build the prompt for Gemini
        prompt = QuestGenerator._build_prompt(
            goal_name=goal_name,
            exam_subject=exam_subject,
            exam_date=exam_date,
            hours_willing=hours_willing,
            themes=themes,
            earliest_date=earliest_date.isoformat(),
            latest_date=exam_date,
        )
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2-flash",  # Use the latest fast model
            contents=prompt,
        )
        
        # Parse the JSON response
        try:
            # Extract JSON from response (handle potential markdown formatting)
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            quests_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {response.text}") from e
        
        if not isinstance(quests_data, dict) or "quests" not in quests_data:
            raise ValueError("Gemini response must contain 'quests' key")
        
        # Convert to Quest objects
        quests = []
        for quest_data in quests_data["quests"]:
            try:
                quest = Quest(
                    name=quest_data["name"],
                    theme=quest_data["theme"],
                    study_time=float(quest_data["study_time"]),
                    date=quest_data["date"],  # Should be ISO format from Gemini
                    xp_reward=int(quest_data.get("xp_reward", 50)),
                    stat_points=quest_data.get("stat_points", {}),
                    description=quest_data.get("description", ""),
                )
                quests.append(quest)
            except (KeyError, ValueError, TypeError) as e:
                raise ValueError(f"Invalid quest data from Gemini: {quest_data}") from e
        
        return quests

    @staticmethod
    def _build_prompt(
        goal_name: str,
        exam_subject: str,
        exam_date: str,
        hours_willing: float,
        themes: List[str],
        earliest_date: str,
        latest_date: str,
    ) -> str:
        """Build the prompt to send to Gemini for quest generation."""
        
        themes_str = ", ".join(themes)
        
        prompt = f"""You are a study planner. Generate a structured study plan for a goal.

GOAL DETAILS:
- Goal Name: {goal_name}
- Subject: {exam_subject}
- Exam Date: {latest_date}
- Total Study Hours Available: {hours_willing} hours
- Topics to Cover: {themes_str}
- Quest Date Range: {earliest_date} to {latest_date} (all quests must be on or before exam date)

REQUIREMENTS:
1. Create multiple quests that together total approximately {hours_willing} hours (can be slightly under/over by 10%)
2. Each quest must have a study_time that is realistic and between 1.5 and 8 hours
3. Distribute quests across the available dates ({earliest_date} to {latest_date})
4. Assign one theme to each quest from the provided topics
5. Create meaningful quest names that reflect the topic and specific learning objectives
6. Include brief descriptions explaining what will be learned in each quest
7. Assign reasonable XP rewards (30-100 points) and stat_points based on difficulty
8. Ensure earlier quests have foundational topics and later quests build on them
9. Space quests reasonably across the date range (not all on same date)

RETURN FORMAT - Return ONLY valid JSON with NO additional text:
{{
    "quests": [
        {{
            "name": "Quest Name - Specific Topic",
            "theme": "One of the provided topics",
            "study_time": 2.5,
            "date": "YYYY-MM-DD",
            "xp_reward": 50,
            "stat_points": {{"intelligence": 2, "focus": 1}},
            "description": "Brief description of what will be learned in this quest."
        }},
        ...more quests...
    ]
}}

IMPORTANT:
- Return ONLY the JSON object, no markdown, no explanation
- Ensure total study_time across all quests ≈ {hours_willing} hours
- All dates must be within {earliest_date} to {latest_date}
- All quests must cover the provided themes
"""
        
        return prompt

    @staticmethod
    def validate_quests(
        quests: List[Quest],
        expected_hours: float,
        tolerance_percent: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Validate generated quests meet constraints.
        
        Args:
            quests: List of Quest objects to validate
            expected_hours: Expected total study hours
            tolerance_percent: Acceptable deviation from expected hours (default 10%)
        
        Returns:
            Dict with validation results including:
            - valid: bool
            - total_hours: float
            - num_quests: int
            - messages: list of validation messages
        """
        
        messages = []
        total_hours = sum(q.study_time for q in quests)
        deviation = abs(total_hours - expected_hours)
        deviation_percent = (deviation / expected_hours * 100) if expected_hours > 0 else 0
        
        valid = True
        
        if len(quests) == 0:
            messages.append("ERROR: No quests generated")
            valid = False
        else:
            messages.append(f"✓ Generated {len(quests)} quests")
        
        if deviation_percent <= tolerance_percent:
            messages.append(f"✓ Total hours: {total_hours:.1f}h (expected ~{expected_hours}h)")
        else:
            messages.append(
                f"⚠ Total hours: {total_hours:.1f}h (expected ~{expected_hours}h, "
                f"deviation: {deviation_percent:.1f}%)"
            )
            valid = False
        
        # Check all quests have valid dates
        all_valid_dates = all(
            hasattr(q, 'date') and q.date and isinstance(q.date, str)
            for q in quests
        )
        if all_valid_dates:
            messages.append("✓ All quests have valid dates")
        else:
            messages.append("ERROR: Some quests have invalid dates")
            valid = False
        
        # Check all quests have themes
        all_have_themes = all(hasattr(q, 'theme') and q.theme for q in quests)
        if all_have_themes:
            messages.append("✓ All quests have themes assigned")
        else:
            messages.append("ERROR: Some quests missing themes")
            valid = False
        
        return {
            "valid": valid,
            "total_hours": total_hours,
            "num_quests": len(quests),
            "messages": messages,
        }