from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, login_manager
from datetime import date, datetime
from app.models import (
    add_student, mark_attendance, get_attendance, get_attendance_stats, 
    get_student_attendance, get_all_students, update_student, delete_student, 
    get_dashboard_stats, get_user_by_username, create_user, get_teacher_by_user_id,
    get_classes_by_teacher, create_class, get_students_by_class, get_student_by_user_id,
    get_attendance_for_student
)
from app.auth_models import User

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# --- Auth Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = get_user_by_username(username)
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], username=user_data['username'], 
                        role=user_data['role'], email=user_data['email'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role', 'student') # Default to student
        
        hashed_password = generate_password_hash(password)
        try:
            create_user(username, hashed_password, email, role)
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed: ' + str(e))
            
    return render_template('register.html')

# --- Portals & Dashboard ---

@app.route('/')
@login_required
def home():
    if current_user.role == 'teacher':
        teacher = get_teacher_by_user_id(current_user.id)
        classes = get_classes_by_teacher(teacher['id']) if teacher else []
        return render_template("teacher_dashboard.html", classes=classes, teacher=teacher)
    elif current_user.role == 'student':
        student = get_student_by_user_id(current_user.id)
        attendance = get_attendance_for_student(student['id']) if student else []
        return render_template("student_dashboard.html", attendance=attendance, student=student)
    
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)

# --- Teacher API & Routes ---

@app.route('/create_class', methods=['POST'])
@login_required
def api_create_class():
    if current_user.role != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    name = data.get("name")
    teacher = get_teacher_by_user_id(current_user.id)
    
    if teacher:
        create_class(name, teacher['id'])
        return jsonify({"message": "Class created successfully!"})
    return jsonify({"error": "Teacher profile not found"}), 404

@app.route('/class/<int:class_id>/attendance', methods=['GET'])
@login_required
def class_attendance(class_id):
    if current_user.role != 'teacher':
        return redirect(url_for('home'))
    
    students = get_students_by_class(class_id)
    return render_template("take_attendance.html", students=students, class_id=class_id)

@app.route('/submit_attendance', methods=['POST'])
@login_required
def submit_attendance():
    if current_user.role != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    class_id = data.get("class_id")
    attendance_data = data.get("attendance") # List of {student_id, status}
    today = str(date.today())
    
    for entry in attendance_data:
        mark_attendance(entry['student_id'], class_id, today, entry['status'])
        
    return jsonify({"message": "Attendance submitted successfully!"})

@app.route('/dashboard_stats')
def dashboard_stats():
    return jsonify(get_dashboard_stats())

@app.route('/students', methods=['GET'])
def get_students():
    students = get_all_students()
    return jsonify(students)

@app.route('/update_student/<int:student_id>', methods=['PUT'])
def update_student_route(student_id):
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    update_student(student_id, name)
    return jsonify({"message": "Student updated successfully!"})

@app.route('/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student_route(student_id):
    delete_student(student_id)
    return jsonify({"message": "Student deleted successfully!"})

@app.route('/students_page')
def students_page():
    return render_template("students.html")

@app.route('/register_student', methods=['POST'])
def register_student():
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"error": "Name is required"}), 400

    student_id = add_student(name)
    mark_attendance(student_id, str(date.today()), "Present")

    return jsonify({"message": f"Attendance recorded for {name}!"})

@app.route('/mark_absent', methods=['POST'])
def mark_absent():
    data = request.get_json()
    student_id = data.get("student_id")

    if not student_id:
        return jsonify({"error": "Student ID is required"}), 400

    mark_attendance(student_id, str(date.today()), "Absent")

    return jsonify({"message": "Student marked as Absent!"})

@app.route('/get_attendance', methods=['GET'])
def fetch_attendance():
    records = get_attendance()
    return render_template("attendance.html", records=records)

@app.route('/analytics')
def analytics_page():
    return render_template("analytics.html")

@app.route('/attendance_stats', methods=['GET'])
def attendance_stats():
    start_date = request.args.get('start_date', '2023-01-01')  # Default start date
    end_date = request.args.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    student_name = request.args.get('student_name', None)  # Optional filter by student

    if student_name:
        stats = get_student_attendance(student_name, start_date, end_date)
    else:
        stats = get_attendance_stats(start_date, end_date)

    return jsonify(stats)