from flask_wtf import FlaskForm
from wtforms import SubmitField

class SimulateForm(FlaskForm):
    submit = SubmitField(label="Simulate")