import random, math
from stocks import app, db
from sqlalchemy import desc
from stocks.models import Stock
from flask import Flask, render_template, request, redirect, url_for, flash

@app.route('/stocks_market')
@app.route('/',methods = ['GET','POST'])
def home_page():
    if request.method == 'POST':
        week_number = request.form.get('week_number')
        stock_items = Stock.query.filter_by(week=week_number).all()
    else:
        latest_market_week = db.session.query(db.func.max(Stock.week)).scalar()
        stock_items = Stock.query.filter_by(week=latest_market_week).all()
        week_number = latest_market_week
    
    return render_template('home.html', stock_items=stock_items, latest_market_week=week_number)

@app.route('/simulate', methods=['GET','POST'])
def simulate_page():
    if request.method == 'POST':
        latest_week = db.session.query(db.func.max(Stock.week)).scalar()
        next_week = latest_week + 1

        for stock_data in Stock.query.filter_by(week=latest_week):
            volume_change = random.uniform(-0.2,0.2)
            new_volume = stock_data.volume * (1 + volume_change)
            if new_volume > 10000:
                new_price = stock_data.price * random.uniform(1.01,1.05)
            elif new_volume < 1000:
                new_price = stock_data.price * random.uniform(0.95,0.99)
            else:
                new_price = stock_data.price * random.uniform(0.99,1.01)

            new_volume = math.floor(new_volume * 100)/100
            new_price = math.floor(new_price * 100) / 100
            # Add a new_stock object
            new_stock = Stock(stock=stock_data.stock,price=new_price,volume=new_volume, week=next_week)
            db.session.add(new_stock)

        db.session.commit()

        print("New stock records inserted for week", next_week)
        flash("New stock records inserted for week" + str(next_week),category='success')
        return redirect('/simulate')
    else:
        return render_template('simulate.html')
