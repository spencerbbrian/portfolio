from flask import Flask

app = Flask(__name__)

@app.route("/potato")
def welcome():
    return "This is my first Flask app. Yay!"


app.run()