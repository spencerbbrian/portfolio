from flask import Flask
from flask_login import LoginManager, UserMixin
from pymongo import MongoClient
import os

# Initialize Flask application
app = Flask(__name__)

# Set up the secret key
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')  # Use an environment variable for the secret key

# Connect to MongoDB using MongoClient
try:
    client = MongoClient(f"mongodb+srv://sbb:{os.getenv('password')}@golden-heights-universi.k3mfjir.mongodb.net/")
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Connect to the database and collections
db = client.golheights  # Use your database name here
students = db.students
courses = db.course
employees = db.employees
departments = db.department
awards = db.awards
accounts = db.accounts
housing = db.housing
transcripts = db.transcript

# Set up Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login_page"  
login_manager.login_message_category = 'info'

from goldenheights.models import User

# User loader for Flask-Login
@login_manager.user_loader
def load_user(student_id):
    return User.find_by_student_id(student_id)

# Import routes after initializing the app and extensions
from goldenheights import routes
