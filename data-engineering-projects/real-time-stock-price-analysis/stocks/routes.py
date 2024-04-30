from stocks import app, db
from stocks.models import Stock
from stocks.forms import SimulateForm
from flask import Flask, render_template, request, redirect, url_for, flash

@app.route('/', methods=['GET','POST'])
def home_page():
    simulate_form = SimulateForm()
     #Simulate Logic
    if request.method == 'POST':
        stock_to_simulate = request.form.get('simulate_stock')
        stocks_check = Stock.query.filter_by(stock=stock_to_simulate).first()
        if stocks_check:
            print('stocks_check')

    if request.method == 'GET':
        stock_items = Stock.query.filter_by(week=1)
    return render_template('home.html',stock_items=stock_items,simulate_form=simulate_form)
