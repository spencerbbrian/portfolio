from market import app, db
from market.models import Item,User
from flask import render_template,request,redirect, url_for, flash
from market.forms import RegisterForm,LoginForm, PurchaseItemForm, SellItemForm
from flask_login import login_user, logout_user, login_required, current_user

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

@app.route('/market', methods=["GET","POST"])
@login_required
def market_page():
    purchase_form = PurchaseItemForm()
    selling_form = SellItemForm()
    if request.method == "POST":
        #Purchase Item Logic
        purchased_item = request.form.get('purchased_item') #This is the name in the input of the modal which gets the value of that input
        p_item_object = Item.query.filter_by(name=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                p_item_object.buy(current_user)
                flash(f"Congratulations! You purchased {p_item_object.name} for ${p_item_object.price}",category='success')
            else:
                flash(f"Unfortunately, you don't have enough to purchase {p_item_object.name}!",category='danger')
        #Sell Item Logic
        sold_item = request.form.get('sold_item')
        s_item_object = Item.query.filter_by(name=sold_item).first()
        if s_item_object:
            #ensure ownership of item
            if current_user.can_sell(s_item_object):
                s_item_object.sell(current_user)
                flash(f"Congratulations! You sold {s_item_object.name} for ${s_item_object.price}",category='success')
            else:
                flash(f"Unfortunately, you couldn't sell {s_item_object.name}!",category='danger')
        return redirect(url_for('market_page'))
    
    if request.method == "GET":
        items = Item.query.filter_by(owner=None)
        owned_items = Item.query.filter_by(owner=current_user.id)
        return render_template('market.html',items=items,purchase_form=purchase_form,owned_items=owned_items,selling_form=selling_form)

@app.route('/register', methods=["GET", "POST"])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are logged in as: {user_to_create.username}", category='success')
        return redirect(url_for('market_page'))
    if form.errors != {}: #If there are errors from the validations in the model
        for err_msg in form.errors.values():
            flash(f'{err_msg}', category='danger')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET','POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first() 
        if attempted_user and attempted_user.check_password_correction(
            attempted_password=form.password.data):
            login_user(attempted_user)
            flash(f"Welcome! You are logged in as: {attempted_user.username}", category='success')
            return redirect(url_for('market_page'))
        else:
            flash("Username or password is incorrect! Please try again", category='danger')

    return render_template('login.html',form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for('home_page'))