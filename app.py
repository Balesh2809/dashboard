import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = 'students.db'

# 1. Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gpa REAL,
            attendance REAL,
            assignments_submitted INTEGER,
            total_assignments INTEGER
        )
    ''')
    
    # Seed sample data if table is empty
    cursor.execute('SELECT COUNT(*) FROM students')
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('Alex Johnson', 3.8, 95.0, 10, 10),
            ('Sam Rivera', 1.9, 62.0, 4, 10),
            ('Taylor Smith', 2.4, 78.0, 7, 10),
            ('Jordan Lee', 1.2, 45.0, 2, 10),
            ('Morgan Davis', 3.2, 88.0, 9, 10)
        ]
        cursor.executemany('''
            INSERT INTO students (name, gpa, attendance, assignments_submitted, total_assignments)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_data)
        conn.commit()
    conn.close()

# 2. Risk Calculation Algorithm
def calculate_risk(gpa, attendance, submitted, total):
    # Calculate component scores
    gpa_score = max(0, (4.0 - gpa) / 4.0) * 40          # 40% Weight on GPA
    att_score = max(0, (100 - attendance) / 100) * 40    # 40% Weight on Attendance
    
    completion_rate = (submitted / total) if total > 0 else 1.0
    hw_score = (1.0 - completion_rate) * 20             # 20% Weight on Assignments
    
    risk_score = round(gpa_score + att_score + hw_score, 1)
    
    if risk_score >= 50:
        status = 'High Risk'
        color = 'red'
    elif risk_score >= 25:
        status = 'Moderate Risk'
        color = 'amber'
    else:
        status = 'Low Risk'
        color = 'green'
        
    return risk_score, status, color

# 3. Web Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    rows = cursor.fetchall()
    conn.close()

    students = []
    for r in rows:
        risk_score, status, color = calculate_risk(r[2], r[3], r[4], r[5])
        students.append({
            'id': r[0],
            'name': r[1],
            'gpa': r[2],
            'attendance': r[3],
            'assignments': f"{r[4]}/{r[5]}",
            'risk_score': risk_score,
            'status': status,
            'color': color
        })
    return jsonify(students)

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO students (name, gpa, attendance, assignments_submitted, total_assignments)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['name'], float(data['gpa']), float(data['attendance']), int(data['submitted']), int(data['total'])))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
