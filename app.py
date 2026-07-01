import os
import sqlite3
import subprocess
import json
from datetime import datetime
from flask import Flask, g, session, redirect, url_for, request, jsonify, render_template, abort
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('AIT_SECRET_KEY', 'ait-secret-key-change')
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'ait.db')

# Email Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 1025))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', False)
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', False)
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@africainnovation.tech')

mail = Mail(app)

def send_welcome_email(full_name, email):
    """Send a professional welcome email to new users."""
    try:
        subject = f'Welcome to Africa Technology Innovation, {full_name}!'
        msg = Message(
            subject=subject,
            recipients=[email],
            html=render_template('email/welcome.html', full_name=full_name)
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f'Error sending welcome email to {email}: {e}')
        return False


PAGE_TEMPLATES = {
    'index.html',
    'courses.html',
    'community.html',
    'pricing.html',
    'about.html',
    'contact.html',
    'login.html',
    'register.html',
    'profile.html',
    'admin.html',
    'lab.html',
    'course-detail.html',
}


def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        g.db = db
    return db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        if not os.path.exists(DATABASE_PATH):
            db = get_db()
            with open(os.path.join(os.path.dirname(__file__), 'database.sql'), 'r', encoding='utf-8') as f:
                db.executescript(f.read())
            db.commit()
        db = get_db()
        create_default_accounts(db)


def create_default_accounts(db):
    admin_email = 'admin@africainnovation.tech'
    normal_email = 'jane@example.com'

    admin_user = db.execute('SELECT id, password_hash FROM users WHERE email = ?', (admin_email,)).fetchone()
    if not admin_user:
        db.execute(
            'INSERT INTO users (full_name, email, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (
                'Admin Manager',
                admin_email,
                generate_password_hash('Admin123!'),
                'admin',
                datetime.utcnow(),
                datetime.utcnow(),
            ),
        )
    elif admin_user['password_hash'] == '<hashed-password>':
        db.execute(
            'UPDATE users SET password_hash = ?, full_name = ?, role = ?, updated_at = ? WHERE id = ?',
            (
                generate_password_hash('Admin123!'),
                'Admin Manager',
                'admin',
                datetime.utcnow(),
                admin_user['id'],
            ),
        )

    normal_user = db.execute('SELECT id, password_hash FROM users WHERE email = ?', (normal_email,)).fetchone()
    if not normal_user:
        db.execute(
            'INSERT INTO users (full_name, email, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (
                'Jane Doe',
                normal_email,
                generate_password_hash('User1234!'),
                'user',
                datetime.utcnow(),
                datetime.utcnow(),
            ),
        )
    elif normal_user['password_hash'] == '<hashed-password>':
        db.execute(
            'UPDATE users SET password_hash = ?, full_name = ?, role = ?, updated_at = ? WHERE id = ?',
            (
                generate_password_hash('User1234!'),
                'Jane Doe',
                'user',
                datetime.utcnow(),
                normal_user['id'],
            ),
        )

    db.commit()


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = None
    if user_id is not None:
        g.user = get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


@app.context_processor
def inject_user():
    return {'current_user': g.user}


def login_required():
    if g.user is None:
        abort(401)


def admin_required():
    if g.user is None or g.user['role'] != 'admin':
        abort(403)


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/<path:page>')
def render_page(page):
    if page not in PAGE_TEMPLATES:
        abort(404)

    if page == 'admin.html':
        if g.user is None or g.user['role'] != 'admin':
            return redirect(url_for('render_page', page='login.html'))

    if page == 'profile.html' and g.user is None:
        return redirect(url_for('render_page', page='login.html'))

    if page == 'lab.html' and g.user is None:
        return redirect(url_for('render_page', page='login.html'))

    return render_template(page)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('render_page', page='login.html'))


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not full_name or not email or not password:
        return jsonify({'error': 'Missing registration fields'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        return jsonify({'error': 'Email already registered'}), 400

    password_hash = generate_password_hash(password)
    db.execute(
        'INSERT INTO users (full_name, email, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
        (full_name, email, password_hash, 'user', datetime.utcnow(), datetime.utcnow()),
    )
    db.commit()

    # Send welcome email
    send_welcome_email(full_name, email)

    return jsonify({'success': True, 'message': 'Registration complete'})


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = get_db().execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if user is None or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 401

    session.clear()
    session['user_id'] = user['id']
    return jsonify({'success': True, 'role': user['role']})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/session')
def api_session():
    if g.user is None:
        return jsonify({'logged_in': False})
    return jsonify({'logged_in': True, 'user': {'full_name': g.user['full_name'], 'email': g.user['email'], 'role': g.user['role']}})


@app.route('/api/profile')
def api_profile():
    if g.user is None:
        return jsonify({'error': 'Authentication required'}), 401

    db = get_db()
    enrolled = db.execute(
        '''
        SELECT c.id, c.title, c.summary, c.description, c.price, e.enrolled_at
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.user_id = ?
        ORDER BY e.enrolled_at DESC
        ''',
        (g.user['id'],),
    ).fetchall()

    courses_with_progress = []
    for course in enrolled:
        # Count total exercises in course
        total_ex = db.execute('''
            SELECT COUNT(*) FROM exercises ex
            JOIN lessons l ON ex.lesson_id = l.id
            WHERE l.course_id = ?
        ''', (course['id'],)).fetchone()[0]
        # Count passed submissions by user in course
        passed_ex = db.execute('''
            SELECT COUNT(DISTINCT ex.id) FROM exercises ex
            JOIN lessons l ON ex.lesson_id = l.id
            LEFT JOIN submissions s ON s.exercise_id = ex.id AND s.user_id = ? AND s.passed = 1
            WHERE l.course_id = ? AND s.passed = 1
        ''', (g.user['id'], course['id'])).fetchone()[0]
        percentage = int((passed_ex / total_ex) * 100) if total_ex > 0 else 0
        cdict = dict(course)
        cdict['percentage'] = percentage
        cdict['completed'] = (percentage == 100)
        courses_with_progress.append(cdict)

    return jsonify({
        'user': {
            'full_name': g.user['full_name'],
            'email': g.user['email'],
            'role': g.user['role'],
            'created_at': g.user['created_at'],
        },
        'courses': courses_with_progress,
    })


@app.route('/api/courses')
def api_courses():
    db = get_db()
    courses = db.execute(
        'SELECT id, title, summary, description, price, status FROM courses WHERE status = ? ORDER BY created_at DESC',
        ('published',),
    ).fetchall()
    enrolled_ids = []
    if g.user:
        rows = db.execute('SELECT course_id FROM enrollments WHERE user_id = ?', (g.user['id'],)).fetchall()
        enrolled_ids = [row['course_id'] for row in rows]

    return jsonify({'courses': [dict(row) | {'enrolled': row['id'] in enrolled_ids} for row in courses]})


@app.route('/api/enroll', methods=['POST'])
def api_enroll():
    if g.user is None:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    course_id = data.get('course_id')
    if not course_id:
        return jsonify({'error': 'Missing course ID'}), 400

    db = get_db()
    course = db.execute('SELECT id FROM courses WHERE id = ? AND status = ?', (course_id, 'published')).fetchone()
    if course is None:
        return jsonify({'error': 'Course not found'}), 404

    existing = db.execute('SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?', (g.user['id'], course_id)).fetchone()
    if existing:
        return jsonify({'success': True, 'message': 'Already enrolled'})

    now = datetime.utcnow()
    db.execute('INSERT INTO enrollments (user_id, course_id, enrolled_at) VALUES (?, ?, ?)', (g.user['id'], course_id, now))
    db.execute('INSERT OR IGNORE INTO progress (user_id, course_id, percentage) VALUES (?, ?, ?)', (g.user['id'], course_id, 0))
    db.commit()
    return jsonify({'success': True})


@app.route('/api/my-courses')
def api_my_courses():
    if g.user is None:
        return jsonify({'error': 'Authentication required'}), 401
    return api_profile()


@app.route('/api/admin/courses', methods=['GET', 'POST'])
def api_admin_courses():
    admin_required()
    db = get_db()
    if request.method == 'GET':
        rows = db.execute('SELECT id, title, summary, description, price, status FROM courses ORDER BY created_at DESC').fetchall()
        return jsonify({'courses': [dict(row) for row in rows]})

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    summary = data.get('summary', '').strip()
    description = data.get('description', '').strip()
    price = data.get('price', 'Free').strip() or 'Free'

    if not title or not summary:
        return jsonify({'error': 'Title and summary are required'}), 400

    now = datetime.utcnow()
    db.execute(
        'INSERT INTO courses (title, summary, description, price, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (title, summary, description, price, 'published', g.user['id'], now, now),
    )
    db.commit()
    return jsonify({'success': True})


@app.route('/api/admin/events', methods=['GET', 'POST'])
def api_admin_events():
    admin_required()
    db = get_db()
    if request.method == 'GET':
        rows = db.execute('SELECT id, title, description, event_date, location, status FROM events ORDER BY event_date DESC').fetchall()
        return jsonify({'events': [dict(row) for row in rows]})

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    event_date = data.get('event_date', '').strip()
    location = data.get('location', '').strip()
    description = data.get('description', '').strip()

    if not title or not event_date:
        return jsonify({'error': 'Event title and date are required'}), 400

    now = datetime.utcnow()
    db.execute(
        'INSERT INTO events (title, description, event_date, location, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (title, description, event_date, location, 'published', g.user['id'], now, now),
    )
    db.commit()
    return jsonify({'success': True})


@app.route('/api/events')
def api_events():
    db = get_db()
    rows = db.execute('SELECT id, title, description, event_date, location FROM events WHERE status = ? ORDER BY event_date DESC', ('published',)).fetchall()
    return jsonify({'events': [dict(row) for row in rows]})


@app.route('/api/execute-code', methods=['POST'])
def api_execute_code():
    """Execute Python code and return output."""
    if g.user is None:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    code = data.get('code', '').strip()

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    try:
        result = subprocess.run(
            ['python', '-c', code],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return jsonify({
            'success': True,
            'output': result.stdout,
            'error': result.stderr,
            'return_code': result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Code execution timed out (>5s)'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/<int:course_id>/lessons')
def api_get_lessons(course_id):
    """Get all lessons for a course."""
    db = get_db()
    course = db.execute('SELECT id FROM courses WHERE id = ? AND status = ?', (course_id, 'published')).fetchone()
    if course is None:
        return jsonify({'error': 'Course not found'}), 404

    rows = db.execute(
        'SELECT id, title, description, content, order_index FROM lessons WHERE course_id = ? ORDER BY order_index ASC',
        (course_id,),
    ).fetchall()
    return jsonify({'lessons': [dict(row) for row in rows]})


@app.route('/api/lessons/<int:lesson_id>/exercises')
def api_get_exercises(lesson_id):
    """Get all exercises for a lesson."""
    db = get_db()
    lesson = db.execute('SELECT id FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    if lesson is None:
        return jsonify({'error': 'Lesson not found'}), 404

    rows = db.execute(
        'SELECT id, title, description, starter_code, difficulty, points FROM exercises WHERE lesson_id = ? ORDER BY id ASC',
        (lesson_id,),
    ).fetchall()
    return jsonify({'exercises': [dict(row) for row in rows]})


@app.route('/api/exercises/<int:exercise_id>')
def api_get_exercise(exercise_id):
    """Get a single exercise with starter code."""
    db = get_db()
    row = db.execute(
        'SELECT id, title, description, starter_code, test_cases, difficulty, points FROM exercises WHERE id = ?',
        (exercise_id,),
    ).fetchone()
    if row is None:
        return jsonify({'error': 'Exercise not found'}), 404

    exercise = dict(row)
    if exercise.get('test_cases'):
        exercise['test_cases'] = json.loads(exercise['test_cases'])
    return jsonify(exercise)


@app.route('/api/exercises/<int:exercise_id>/submit', methods=['POST'])
def api_submit_exercise(exercise_id):
    """Submit exercise code and check if it passes."""
    if g.user is None:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    code = data.get('code', '').strip()

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    db = get_db()
    exercise = db.execute(
        'SELECT id, test_cases, solution_code FROM exercises WHERE id = ?',
        (exercise_id,),
    ).fetchone()
    if exercise is None:
        return jsonify({'error': 'Exercise not found'}), 404

    # Load test cases
    test_cases = []
    if exercise['test_cases']:
        try:
            test_cases = json.loads(exercise['test_cases'])
        except Exception:
            test_cases = []

    test_results = []
    all_passed = True
    for tc in test_cases:
        # For each test case, append code to print output for comparison
        test_code = code + f"\n# Test case\n"
        # If the test case is a string, treat as expected output
        expected = tc
        try:
            result = subprocess.run(
                ['python', '-c', test_code],
                capture_output=True,
                text=True,
                timeout=5,
            )
            actual = result.stdout.strip()
            passed = (actual == expected)
            if not passed:
                all_passed = False
            test_results.append({
                'expected': expected,
                'actual': actual,
                'passed': passed
            })
        except subprocess.TimeoutExpired:
            test_results.append({'expected': expected, 'actual': 'Timeout', 'passed': False})
            all_passed = False
        except Exception as e:
            test_results.append({'expected': expected, 'actual': str(e), 'passed': False})
            all_passed = False

    # Store submission
    now = datetime.utcnow()
    db.execute(
        'INSERT INTO submissions (user_id, exercise_id, code, passed, submitted_at) VALUES (?, ?, ?, ?, ?)',
        (g.user['id'], exercise_id, code, 1 if all_passed else 0, now),
    )
    db.commit()

    if test_cases:
        return jsonify({
            'success': all_passed,
            'passed': all_passed,
            'test_results': test_results
        })

    # Fallback: no test cases, just run code
    try:
        result = subprocess.run(
            ['python', '-c', code],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return jsonify({'passed': False, 'error': 'Code execution timed out'}), 408
    except Exception as e:
        return jsonify({'passed': False, 'error': str(e)}), 500

    if result.returncode != 0:
        return jsonify({'passed': False, 'error': result.stderr})

    return jsonify({
        'success': True,
        'passed': True,
        'message': 'Exercise passed!',
        'output': result.stdout,
    })


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
