from market import app, db
from market.models import Item,User
from flask import render_template,request,redirect, url_for, flash
from market.forms import RegisterForm,LoginForm
from flask_login import login_user, logout_user

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
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
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