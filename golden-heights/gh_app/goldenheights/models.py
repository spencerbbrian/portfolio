from flask_login import UserMixin
from goldenheights import students

class User(UserMixin):
    def __init__(self, student_id, email):
        self.student_id = student_id
        self.email = email

    @classmethod
    def find_by_student_id(cls, student_id):
        user_data = students.find_one({"student_id": student_id})
        if user_data:
            return cls(
                student_id=user_data['student_id'],
                email=user_data['email']
            )
        return None
        
    def get_id(self):
        return self.student_id