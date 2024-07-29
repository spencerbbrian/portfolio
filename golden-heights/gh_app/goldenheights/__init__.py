from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///goldenheights.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['SECRET_KEY'] = 'c1b25318efe3ab4a0609d688'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

from goldenheights import routes

# with app.app_context():
#     db.create_all()