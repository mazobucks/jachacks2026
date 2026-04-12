class Question:
    def __init__(self, question, answers):
        self.question = question
        self.answers = answers
        
    def __str__(self):
        return f"question: {self.question}, answers: {self.answers}"