from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Email, DataRequired, ValidationError 

class RegisterForm(FlaskForm):
    email_address = StringField(label="Email Address:", validators=[Email(), DataRequired()])
    student_id = StringField(label='Student ID', validators=[Length(min=12, max=30), DataRequired()])
    submit = SubmitField(label='Submit')

class LoginForm(FlaskForm):
    email_address = StringField(label='Email Address:', validators=[DataRequired()])
    student_id = StringField(label='Student ID', validators=[Length(min=12, max=30), DataRequired()])
    submit = SubmitField(label='Sign In')