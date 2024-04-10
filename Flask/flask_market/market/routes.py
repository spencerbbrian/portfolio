from market import app, db
from market.models import Item,User
from flask import render_template,request,redirect, url_for
from market.forms import RegisterForm

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
             return redirect(url_for('market_page'))
        except Exception as e:
             print(f"ERROR:{e}")
             return f"ERROR:{e}"
    return render_template('additem.html')

@app.route('/market')
def market_page():
    items = Item.query.all()
    return render_template('market.html',items=items)

@app.route('/register', methods=["GET", "POST"])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password_hash=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('market_page'))
    if form.errors != {}: #If there are no errors from the validations in the model
        for err_msg in form.errors.values():
            print(f'There was an error with creating a user: {err_msg}')
    return render_template('register.html', form=form)