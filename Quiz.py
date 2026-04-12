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
        
        try:
            quizDic = json.loads(response.text)
            self.name = quizDic["quiz_name"]
            self.questions = quizDic["questions"]
            
        except json.JSONDecodeError:
            print("Something went wrong with the quiz generation")
        
        """{'quiz_name': 'Study Algebra Basics', 'questions': [{'question': 'Solve for x: 2x + 5 = 13.', 'options': ['4', '9', '8', '6']}, {'question': 'If f(x) = 4x - 3, what is the value of f(5)?', 'options': ['17', '20', '23', '12']}, {'question': "In the linear equation y = mx + b, what does 'b' represent?", 'options': ['The y-intercept', 'The slope', 'The x-intercept', 'The variable']}, {'question': 'Which of these is the solution for x in the equation x / 3 = 7?', 'options': ['21', '10', '4', '14']}, {'question': 'What is the result of simplifying the expression 3(x + 4)?', 'options': ['3x + 12', '3x + 4', 'x + 12', '7x']}]}
"""