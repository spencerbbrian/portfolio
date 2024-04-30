from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['SECRET_KEY'] = '76ce885ef548f08bec2696bd' #os.urandom(12).hex

db = SQLAlchemy(app)

# with app.app_context():
#     from .models import Stock
#     db.create_all()

from stocks import routes
