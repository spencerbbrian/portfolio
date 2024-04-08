from flask import Flask,render_template,request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = "False"
db = SQLAlchemy(app)

with app.app_context():
        db.create_all()

from market import routes