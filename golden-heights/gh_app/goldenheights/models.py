from goldenheights import db, bcrypt

class User(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    student_id = db.Column(db.String(length=30),nullable=False,unique=True)
    email_address = db.Column(db.String(length=50),nullable=False,unique=True)
    password_hash = db.Column(db.String(length=60),nullable=False)
    first_name = db.Column(db.String(length=20),nullable=False)
    last_name = db.Column(db.String(length=20))

    @property
    def password(self):
        return self.password
    
    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self,attempted_password):
        if bcrypt.check_password_hash(self.password_hash,attempted_password):
            return True