from goldenheights import app, db
from flask import render_template, request, redirect,url_for

app.route('/')
app.route('/home')
def home_page():
    return render_template('gh-home.html')