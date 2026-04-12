class Question:
    def __init__(self, question, answers):
        self.question = question
        self.answers = answers
    
    def to_dict(self):
        return {
            'question': self.question,
            'answers': self.answers
        }
        
    def __str__(self):
        return f"question: {self.question}, answers: {self.answers}"