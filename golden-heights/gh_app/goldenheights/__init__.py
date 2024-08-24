from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from pymongo import MongoClient
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///goldenheights.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['SECRET_KEY'] = 'c1b25318efe3ab4a0609d688'

# client = MongoClient(f"mongodb+srv://sbb:{os.getenv('password')}@golden-heights-universi.k3mfjir.mongodb.net/")
# db = client.

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = 'info'

from goldenheights import routes

# with app.app_context():
#     db.create_all()