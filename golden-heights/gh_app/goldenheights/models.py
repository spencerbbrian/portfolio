from flask_login import UserMixin
from goldenheights import students

class User(UserMixin):
    def __init__(self, student_id, email,first_name):
        self.student_id = student_id
        self.email = email
        self.first_name = first_name

    @classmethod
    def find_by_student_id(cls, student_id):
        user_data = students.find_one({"student_id": student_id})
        if user_data:
            return cls(
                student_id=user_data['student_id'],
                email=user_data['email'],
                first_name = user_data['first_name']
            )
        return None
        
    def get_id(self):
        return self.student_id