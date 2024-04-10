from flask import Flask,render_template,request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = "False"
app.config['SECRET_KEY'] = 'b2fefc360330792a78552f7c'
db = SQLAlchemy(app)

# with app.app_context():
#         db.create_all()

from market import routes