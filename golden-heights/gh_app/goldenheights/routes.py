from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from goldenheights import app, students, courses, departments
from goldenheights.models import User  # Ensure your User model is defined correctly
from goldenheights.forms import RegisterForm, LoginForm  # Import both forms



@app.route('/')
@app.route('/home')
def home_page():
    total_courses = departments.count_documents({})
    total_students = students.count_documents({})
    return render_template('gh-home.html', total_courses=total_courses,
                           total_students=total_students)

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        # Query the database for a student with the provided student_id and email_address
        existing_student = students.find_one({
            'student_id': form.student_id.data,
            'email': form.email_address.data
        })

        # If a matching student is found, log them in
        if existing_student:
            user_to_login = User(
                student_id=existing_student['student_id'],
                email=existing_student['email'],
                first_name=existing_student['first_name']
            )
            login_user(user_to_login)  # Log in the user
            flash('Login successful!', category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Student ID or email address is incorrect. Please try again.', category='danger')

    # If there are validation errors, display them
    if form.errors:
        for err_msg in form.errors.values():
            flash(f'{err_msg}', category='danger')

    return render_template('gh-register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    
    if form.validate_on_submit():
        # Strip input to avoid leading/trailing spaces and ensure case-insensitivity
        student_id = form.student_id.data
        email = form.email_address.data  
        print(f"Login attempt for student_id: {student_id}, email: {email}")
        # Query the database
        user_data = students.find_one({
            'student_id': student_id,
            'email': email
        })

        if user_data:
            print(f"User found: {user_data}")
            # Create User object and log in
            user_to_login = User(
                student_id=user_data['student_id'],
                email=user_data['email'],
                first_name=user_data['first_name']
            )
            login_user(user_to_login)
            print(current_user.first_name)
            print(user_to_login.first_name)
            flash('Login successful!', category='success')
            return redirect(url_for('home_page'))
        else:
            print(f"User not found for student_id: {student_id} and email: {email}")
            flash('Student ID or email address is incorrect. Please try again.', category='danger')

    return render_template('gh-login.html', form=form)

@app.route('/logout')
@login_required  # Ensure the user is logged in to access this route
def logout_page():
    logout_user()  # Log out the current user
    flash('You have been logged out.', category='info')
    return redirect(url_for('home_page'))

@app.route('/courses', methods=['GET'])
@login_required
def courses_page():
    student_id = current_user.student_id
    user_data = students.find_one({"student_id": student_id})

    if user_data:
        courses = user_data.get("graded_course", [])
        electives = user_data.get("graded_electives", [])
        return render_template("gh-courses.html", courses=courses, electives=electives)
    else:
        return "No user found", 404