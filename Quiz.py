import json
import os
import time
from Quests import Quest
from google import genai
from Question import Question

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Quiz:
    def __init__(self, quest):
        time.sleep(2)
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
        
        self.name = ""
        self.questions = []
        try:
            quizDic = json.loads(response.text)
            self.name = quizDic["quiz_name"]
            for question in quizDic["questions"]:
                self.questions.append({
                    'question': question["question"],
                    'answers': question["options"]
                })
        except json.JSONDecodeError:
            print("Something went wrong with the quiz generation")
        
    def __str__(self):
        result = ""
        for question in self.questions:
            result += question.__str__()
        return result