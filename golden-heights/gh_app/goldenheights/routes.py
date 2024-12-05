from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from goldenheights import app, students, courses, departments, transcripts, employees
from pymongo import ASCENDING, DESCENDING
from goldenheights.models import User  # Ensure your User model is defined correctly
from goldenheights.forms import RegisterForm, LoginForm  # Import both forms



@app.route('/')
@app.route('/home')
def home_page():
    total_courses = departments.count_documents({})
    total_students = students.count_documents({})
    As = transcripts.count_documents({"grade": {'$in' : ["A", "A-"]}})
    Bs = transcripts.count_documents({"grade": {'$in' :  ["B+", "B", "B-"]}})
    Cs = transcripts.count_documents({"grade":  {'$in' : ["C+", "C", "C-"]}})
    Ds = transcripts.count_documents({"grade": {'$in' : ["D+", "D"]}})
    Total =  As + Bs + Cs + Ds
    As1 =  round((As / Total) * 100)
    Bs1 =  round((Bs / Total) * 100)
    Cs1 =  round((Cs / Total) * 100)
    Ds1 =  round((Ds / Total) * 100)

    return render_template('gh-home.html', total_courses=total_courses,
                           total_students=total_students, As1=As1, Bs1=Bs1, Cs1=Cs1,  Ds1=Ds1)

@app.route('/students')
def students_page():
    college_filter = request.args.get('college')
    year_filter = request.args.get('enrollment_year')
    page = int(request.args.get('page', 1))
    per_page = 10

    # Build query and fetch results
    query = {}
    if college_filter:
        query['college'] = college_filter
    if year_filter:
        query['enrollment_year'] = int(year_filter)

    # Fetch and sort students by last_name, then first_name
    filtered_students_cursor = students.find(query).sort([('last_name', 1), ('first_name', 1)])
    filtered_students = list(filtered_students_cursor)

    total_students = len(filtered_students)
    total_pages = (total_students + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_students = filtered_students[start_idx:end_idx]

    # Generate query string for "Clear All Filters"
    clear_filters_url = url_for('students_page')

    return render_template(
        'gh-students.html',
        students=paginated_students,
        current_page=page,
        total_pages=total_pages,
        college_filter=college_filter,
        year_filter=year_filter,
        clear_filters_url=clear_filters_url,
        max=max,
        min=min
    )


@app.route('/departments')
def departments_page():
    departments_list = list(departments.find({}).sort('department', ASCENDING))
    departments_with_heads = []

    for department in departments_list:
        head_of_department = None
        if 'head_of_department' in department:
            head_of_department = employees.find_one({'employee_id': department['head_of_department']})
            department['head_of_department'] = f"{head_of_department['first_name']} {head_of_department['last_name']}"
        departments_with_heads.append(department)

    return render_template('gh-departments.html', departments_list=departments_with_heads)

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

@app.route('/catalogue', methods=['GET'])
def catalogue_page():
    CBAS = [x['department'] for x in departments.find({"college": "CBAS"})]
    CHSS = [x['department'] for x in departments.find({"college": "CHSS"})]
    CBE = [x['department'] for x in departments.find({"college": "CBE"})]
    CHSP = [x['department'] for x in departments.find({"college": "CHSP"})]
    
    return render_template('gh-catalogue.html', CBAS=CBAS,CHSS=CHSS,CHSP=CHSP,CBE=CBE)

@app.route('/courses', methods=['GET'])
@login_required
def courses_page():
    student_id = current_user.student_id
    user_data = students.find_one({"student_id": student_id})

    if user_data:
        graded_courses = user_data.get("graded_course", [])
        courses_names = []
        course_grades = []
        course_grade_points = []

        for course in graded_courses:
            course_name = courses.find_one({"course_code": course})['title']
            courses_names.append(course_name)
            course_grade = transcripts.find_one({"course": course, "student_id":student_id})['grade']
            course_grades.append(course_grade)
            course_grade_point =  transcripts.find_one({"course": course, "student_id":student_id})['grade_point']
            course_grade_points.append(course_grade_point)

        courses_data = [{'course_id': course, 'course_name': course_name, 'course_grade': course_grade, 'course_grade_point': course_grade_point} for 
                (course, course_name, course_grade, course_grade_point) in 
                zip(graded_courses, courses_names, course_grades, course_grade_points)]

        graded_electives = user_data.get("graded_electives", [])
        electives_names = []
        electives_grades = []
        electives_grade_points = []

        for course in graded_electives:
            course_name = courses.find_one({"course_code": course})['title']
            electives_names.append(course_name)
            course_grade = transcripts.find_one({"course": course, "student_id":student_id})['grade']
            electives_grades.append(course_grade)
            course_grade_point =  transcripts.find_one({"course": course, "student_id":student_id})['grade_point']
            electives_grade_points.append(course_grade_point)

        electives_data = [{'course_id': course, 'course_name': course_name, 'course_grade': course_grade, 'course_grade_point': course_grade_point} for 
                (course, course_name, course_grade, course_grade_point) in 
                zip(graded_electives, electives_names, electives_grades, electives_grade_points)]
        
        gpa = students.find_one({'student_id': current_user.student_id})['gpa']

        return render_template("gh-courses.html", courses_data=courses_data, electives_data=electives_data, gpa=gpa)
    else:
        return "No user found", 404