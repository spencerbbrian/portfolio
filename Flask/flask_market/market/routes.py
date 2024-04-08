from market import app, db
from market.models import Item
from flask import render_template,request,redirect

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/add',methods=["GET","POST"])
def add_page():
    # Add an Item
    if request.method == "POST":
        current_item_name = request.form['item-name']
        current_item_price = request.form['item-price']
        current_item_barcode = request.form['item-barcode']
        current_item_description = request.form['item-description']
        new_item = Item(name=current_item_name,
                        price=current_item_price,
                        barcode=current_item_barcode,
                        description=current_item_description)
        try:
             db.session.add(new_item)
             db.session.commit()
             return redirect("/market")
        except Exception as e:
             print(f"ERROR:{e}")
             return f"ERROR:{e}"
    return render_template('additem.html')

@app.route('/market')
def market_page():
    items = Item.query.all()
    return render_template('market.html',items=items)