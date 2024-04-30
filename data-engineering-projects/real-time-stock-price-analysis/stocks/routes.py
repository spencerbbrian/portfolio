from stocks import app, db
from stocks.models import Stock
from flask import request,render_template


@app.route('/home', methods=['GET','POST'])
def home_page():
    if request.method == 'GET':
        stock_items = Stock.query.all()
        return render_template('home.html',stock_items=stock_items)