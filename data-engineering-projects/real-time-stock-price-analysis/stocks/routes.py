from stocks import app, db
from stocks.models import Stock
from flask import Flask, render_template, request, redirect, url_for, flash


@app.route('/home', methods=['GET'])
def home_page():
    if request.method == 'GET':
        stock_items = Stock.query.all()
        return render_template('home.html',stock_items=stock_items)
    