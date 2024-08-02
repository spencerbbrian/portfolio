from goldenheights import app, db
from goldenheights.models import User
from flask import render_template, request, redirect,url_for,flash
from goldenheights.forms import RegisterForm, LoginForm
from flask_login import login_user, logout_user

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('gh-home.html')

@app.route('/register',methods=['GET','POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              student_id=form.student_id.data,
                              password=form.password1.data,
                              first_name=form.first_name.data,
                              last_name=form.last_name.data)
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('home_page'))
    # if form.errors != {}: #If there are errors from the validations in the model
    #     for err_msg in form.errors.values():
    #         flash(f'{err_msg}', category='danger')
    return render_template('gh-register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first() 
        if attempted_user and attempted_user.check_password_correction(
            attempted_password=form.password.data) and attempted_user.check_student_id(    
            student_id=form.student_id.data):
            login_user(attempted_user)
            flash(f"Welcome! You are logged in as: {attempted_user.username}", category='success')
            return redirect(url_for('home_page'))
        else:
            flash("Username or password is incorrect! Please try again", category='danger')

    return render_template('gh-login.html',form=form)