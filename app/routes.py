from flask import request, jsonify, render_template
from app import app
from datetime import date, datetime
from app.models import add_student, mark_attendance, get_attendance, get_attendance_stats, get_student_attendance, get_all_students, update_student, delete_student, get_dashboard_stats

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def home():
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)

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