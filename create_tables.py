import sqlite3

def create_tables():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected'))
        )
    ''')
    
    # Create classes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            year TEXT NOT NULL,
            batch TEXT NOT NULL,
            teacher_id INTEGER NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    ''')
    
    # Create students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # Create class_students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS class_students (
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            PRIMARY KEY (class_id, student_id)
        )
    ''')
    
    # Create attendance table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
            date TEXT NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
