from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a secure random key

def get_db_connection():
    try:
        # Set a timeout of 10 seconds for acquiring the database lock
        conn = sqlite3.connect('database.db', timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None





@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
            conn.close()
            
            if user:
                if user['status'] == 'accepted':
                    session['username'] = username
                    session['role'] = user['role']
                    session['user_id'] = user['id']
                    return redirect(url_for('dashboard'))
                else:
                    return 'Account not accepted yet!'
            else:
                return 'Invalid credentials or account not found!'
        else:
            return 'Database connection error!'
    
    return render_template('login.html')

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db_connection()
        if conn:
            existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if existing_user:
                conn.close()
                return 'Username already exists. Please choose a different username.'
            
            conn.execute('INSERT INTO users (username, password, role, status) VALUES (?, ?, ?, ?)', 
                         (username, password, role, 'pending'))
            conn.commit()
            conn.close()
            
            return 'Application submitted!'
        else:
            return 'Database connection error!'
    
    return render_template('apply.html')

@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'admin'
        
        conn = get_db_connection()
        if conn:
            existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if existing_user:
                conn.close()
                return 'Username already exists. Please choose a different username.'
            
            conn.execute('INSERT INTO users (username, password, role, status) VALUES (?, ?, ?, ?)', 
                         (username, password, role, 'accepted'))
            conn.commit()
            conn.close()
            
            return redirect(url_for('login'))
        else:
            return 'Database connection error!'
    
    return render_template('admin_signup.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        if session['role'] == 'admin':
            pending_users = conn.execute('SELECT * FROM users WHERE status = ?', ('pending',)).fetchall()
        else:
            pending_users = []

        conn.close()
        return render_template('dashboard.html', role=session['role'], pending_users=pending_users)
    else:
        return 'Database connection error!'

@app.route('/upload_timetable', methods=['GET', 'POST'])
def upload_timetable():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file.save(f'static/{file.filename}')
            conn = get_db_connection()
            if conn:
                conn.execute('INSERT INTO timetables (file_path, uploaded_by) VALUES (?, ?)', (file.filename, session['username']))
                conn.commit()
                conn.close()
                return 'Timetable uploaded!'
            else:
                return 'Database connection error!'
    
    return render_template('upload_timetable.html')

@app.route('/view_timetable')
def view_timetable():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        timetables = conn.execute('SELECT * FROM timetables').fetchall()
        conn.close()
        return render_template('view_timetable.html', timetables=timetables)
    else:
        return 'Database connection error!'
    




@app.route('/show_attendance', methods=['GET'])
def show_attendance():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    class_id = request.args.get('class_id')
    date = request.args.get('date')

    conn = get_db_connection()
    if conn:
        attendance_records = conn.execute('''
            SELECT u.username, a.status
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            WHERE a.class_id = ? AND a.date = ?
        ''', (class_id, date)).fetchall()
        conn.close()
        return render_template('show_attendance.html', attendance=attendance_records)
    else:
        return 'Database connection error!'




@app.route('/view_my_attendance')
def view_my_attendance():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        student_id = conn.execute('SELECT id FROM users WHERE username = ?', (session['username'],)).fetchone()['id']
        attendance = conn.execute('''\
            SELECT a.*, c.subject, c.year, c.batch
            FROM attendance a
            JOIN classes c ON a.class_id = c.id
            WHERE a.student_id = ?
        ''', (student_id,)).fetchall()
        
        conn.close()
        return render_template('view_my_attendance.html', attendance=attendance)
    else:
        return 'Database connection error!'

@app.route('/approve_application/<int:user_id>')
def approve_application(user_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        conn.execute('UPDATE users SET status = ? WHERE id = ?', ('accepted', user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    else:
        return 'Database connection error!'

@app.route('/reject_application/<int:user_id>')
def reject_application(user_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        conn.execute('UPDATE users SET status = ? WHERE id = ?', ('rejected', user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    else:
        return 'Database connection error!'

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('home'))

@app.route('/delete_timetable/<int:timetable_id>', methods=['POST'])
def delete_timetable(timetable_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn:
        timetable = conn.execute('SELECT * FROM timetables WHERE id = ?', (timetable_id,)).fetchone()
        if timetable:
            file_path = timetable['file_path']
            file_full_path = f'static/{file_path}'
            try:
                os.remove(file_full_path)
            except FileNotFoundError:
                pass

            conn.execute('DELETE FROM timetables WHERE id = ?', (timetable_id,))
            conn.commit()
        conn.close()
        return redirect(url_for('view_timetable'))
    else:
        return 'Database connection error!'

@app.route('/manage_students_teachers', methods=['GET', 'POST'])
def manage_students_teachers():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    if request.method == 'POST':
        subject = request.form['subject']
        year = request.form['year']
        batch = request.form['batch']
        teacher_id = request.form['teacher_id']
        student_ids = request.form.getlist('student_ids')
        
        conn.execute('INSERT INTO classes (subject, year, batch, teacher_id) VALUES (?, ?, ?, ?)', 
                     (subject, year, batch, teacher_id))
        class_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        for student_id in student_ids:
            conn.execute('INSERT INTO class_students (class_id, student_id) VALUES (?, ?)', 
                         (class_id, student_id))
        conn.commit()
        conn.close()
        return 'Class and students assigned successfully!'

    teachers = conn.execute('SELECT id, username FROM users WHERE role = ?', ('teacher',)).fetchall()
    students = conn.execute('SELECT id, username FROM users WHERE role = ?', ('student',)).fetchall()
    conn.close()
    return render_template('manage_students_teachers.html', teachers=teachers, students=students)

@app.route('/get_students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    if conn:
        students = conn.execute('SELECT id, username FROM users WHERE role = ?', ('student',)).fetchall()
        conn.close()
        return render_template('students_list.html', students=students)
    else:
        return 'Database connection error!'

@app.route('/take_attendance', methods=['GET', 'POST'])
def take_attendance():
    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    teacher_id = conn.execute('SELECT id FROM users WHERE username = ?', (session['username'],)).fetchone()['id']
    
    if request.method == 'POST':
        class_id = request.form['class_id']
        date = request.form['date']
        attendance_data = request.form.to_dict()
        student_statuses = {key.split('_')[1]: value for key, value in attendance_data.items() if key.startswith('attendance_')}
        try:
            for student_id, status in student_statuses.items():
                conn.execute('''
                    INSERT INTO attendance (class_id, student_id, date, status)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(student_id, class_id, date) DO UPDATE SET status=excluded.status''',
                             (class_id, student_id, date, status))
            conn.commit()
            flash('Attendance marked successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred while marking attendance: {e}', 'error')
        
        return redirect(url_for('take_attendance', class_id=class_id, date=date))

    classes = conn.execute('''SELECT id, subject, year, batch FROM classes WHERE teacher_id = ?''', (teacher_id,)).fetchall()
    selected_class_id = request.args.get('class_id')
    students = []
    
    if selected_class_id:
        students = conn.execute('''
            SELECT u.id, u.username 
            FROM users u 
            JOIN class_students cs ON u.id = cs.student_id 
            WHERE cs.class_id = ?''', (selected_class_id,)).fetchall()
    
    conn.close()
    return render_template('take_attendance.html', classes=classes, students=students, selected_class_id=selected_class_id)


@app.route('/view_students', methods=['GET', 'POST'])
def view_students():
    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    class_id = request.args.get('class_id')
    date = request.args.get('date')

    conn = get_db_connection()
    students = []
    
    if class_id:
        students = conn.execute('''
            SELECT u.id, u.username
            FROM users u
            JOIN class_students cs ON u.id = cs.student_id
            WHERE cs.class_id = ?
        ''', (class_id,)).fetchall()
    
    conn.close()
    return render_template('view_students.html', students=students, class_id=class_id, date=date)



@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    class_id = request.form['class_id']
    date = request.form['date']

    # Validate and format the date
    try:
        date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        flash('Please enter a valid date.', 'error')
        return redirect(url_for('take_attendance'))

    student_statuses = {}
    for key in request.form.keys():
        if key.startswith('attendance_'):
            student_id = key.split('_')[1]
            status = request.form[key]
            student_statuses[student_id] = status

    # Insert into the database
    for student_id, status in student_statuses.items():
        save_attendance(student_id, class_id, date, status)

    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('take_attendance'))


def save_attendance(student_id, class_id, date, status):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO attendance (student_id, class_id, date, status)
            VALUES (?, ?, ?, ?)''', (student_id, class_id, date, status))
        connection.commit()
        print(f"Attendance for Student ID {student_id} marked as {status}.")  # Debug log
    except Exception as e:
        print(f"Error saving attendance for Student ID {student_id}: {e}")  # More detailed logging
        flash('An error occurred while marking attendance.', 'error')
    finally:
        cursor.close()
        connection.close()



@app.route('/view_attendance', methods=['GET'])
def view_attendance():
    if 'username' not in session:
        return redirect(url_for('login'))

    class_id = request.args.get('class_id')
    date = request.args.get('date')

    conn = get_db_connection()
    if conn:
        # Fetch the classes associated with the logged-in teacher
        teacher_id = conn.execute('SELECT id FROM users WHERE username = ?', (session['username'],)).fetchone()['id']
        classes = conn.execute('SELECT id, subject, year, batch FROM classes WHERE teacher_id = ?', (teacher_id,)).fetchall()

        attendance = []
        if class_id and date:
            attendance = conn.execute('''
                SELECT u.username, a.status
                FROM attendance a
                JOIN users u ON a.student_id = u.id
                WHERE a.class_id = ? AND a.date = ?
            ''', (class_id, date)).fetchall()

        conn.close()
        return render_template('view_attendance.html', classes=classes, attendance=attendance, 
                               selected_class_id=class_id, selected_date=date)
    else:
        return 'Database connection error!'










if __name__ == '__main__':
    app.run(debug=True)
