from datetime import date
from app.database import get_db_connection

def add_student(name):
    """Insert a new student and return their ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name) VALUES (%s)", (name,))
    student_id = cursor.lastrowid  # Get last inserted student ID
    conn.commit()
    cursor.close()
    conn.close()
    return student_id

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def create_user(username, password_hash, email, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s)",
                   (username, password_hash, email, role))
    user_id = cursor.lastrowid
    
    # Create corresponding profile
    if role == 'teacher':
        cursor.execute("INSERT INTO teachers (user_id, name) VALUES (%s, %s)", (user_id, username))
    elif role == 'student':
        cursor.execute("INSERT INTO students (user_id, name) VALUES (%s, %s)", (user_id, username))
        
    conn.commit()
    cursor.close()
    conn.close()

def get_teacher_by_user_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teachers WHERE user_id = %s", (user_id,))
    teacher = cursor.fetchone()
    cursor.close()
    conn.close()
    return teacher

def get_student_by_user_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return student

def create_class(name, teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO classes (class_name, teacher_id) VALUES (%s, %s)", (name, teacher_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_classes_by_teacher(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM classes WHERE teacher_id = %s", (teacher_id,))
    classes = cursor.fetchall()
    cursor.close()
    conn.close()
    return classes

def get_students_by_class(class_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.* FROM students s
        JOIN enrollments e ON s.id = e.student_id
        WHERE e.class_id = %s
    """, (class_id,))
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return students

def get_attendance_for_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, c.class_name FROM attendance a
        JOIN classes c ON a.class_id = c.id
        WHERE a.student_id = %s
        ORDER BY a.date DESC
    """, (student_id,))
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

def mark_attendance(student_id, class_id, date, status="Present"):
    """Mark attendance for a student. Updates if already exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if entry exists
    cursor.execute("SELECT id FROM attendance WHERE student_id = %s AND class_id = %s AND date = %s", 
                   (student_id, class_id, date))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE attendance SET status = %s WHERE id = %s", (status, existing[0]))
    else:
        cursor.execute("INSERT INTO attendance (student_id, class_id, date, status) VALUES (%s, %s, %s, %s)", 
                       (student_id, class_id, date, status))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_attendance():
    """Fetch attendance records."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.id AS student_id, s.name, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC
    """)
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

def get_all_students():
    """Fetch all students."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students ORDER BY name")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return students

def update_student(student_id, name):
    """Update a student's name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET name = %s WHERE id = %s", (name, student_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_student(student_id):
    """Delete a student and their attendance records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()

def get_dashboard_stats():
    """Fetch total students and today's attendance summary."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Total students
    cursor.execute("SELECT COUNT(*) as total FROM students")
    total_students = cursor.fetchone()["total"]

    # Today's attendance
    today = str(date.today())
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM attendance 
        WHERE date = %s 
        GROUP BY status
    """, (today,))
    
    attendance_data = {row["status"]: row["count"] for row in cursor.fetchall()}
    
    cursor.close()
    conn.close()

    return {
        "total_students": total_students,
        "present_today": attendance_data.get("Present", 0),
        "absent_today": attendance_data.get("Absent", 0)
    }

def get_attendance_stats(start_date, end_date):
    """Fetch total Present vs Absent count for a date range."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM attendance
        WHERE date BETWEEN %s AND %s
        GROUP BY status
    """, (start_date, end_date))

    data = {row["status"]: row["count"] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    return {"Present": data.get("Present", 0), "Absent": data.get("Absent", 0)}

def get_student_attendance(name, start_date, end_date):
    """Fetch Present vs Absent count for a particular student."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.status, COUNT(*) as count
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE s.name = %s AND a.date BETWEEN %s AND %s
        GROUP BY a.status
    """, (name, start_date, end_date))

    data = {row["status"]: row["count"] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    return {"Student": name, "Present": data.get("Present", 0), "Absent": data.get("Absent", 0)}
