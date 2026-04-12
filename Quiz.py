import json
import os
from Quests import Quest
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Quiz:
    def __init__(self, quest):
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents = f"""Using this info: {quest.quizInfoString()},
            Generate a multiple choice quiz as JSON.
            Format:
            {{
            "quiz_name": string,
            "questions": [
                {{
                "question": string,
                "options": [correct, wrong, wrong, wrong]
                }}
            ]
            }}
            Rules:
            - First option is always correct
            - Exactly 4 options per question
            - Return ONLY valid JSON, no extra text
            """
            )
        print(json.loads(response.text))
        #print(response)