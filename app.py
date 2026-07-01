import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime
from flask import Flask, g, render_template, request, jsonify, session, redirect, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ait.db")
SQL_SCHEMA_PATH = os.path.join(BASE_DIR, "database.sql")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_PERMANENT"] = False

ALLOWED_TEMPLATES = {
    name for name in os.listdir(app.template_folder)
    if name.endswith('.html')
}


def get_db():
    if hasattr(g, "db") and g.db:
        return g.db

    if not os.path.exists(DB_PATH):
        init_db()

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    g.db = conn
    return conn


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "db") and g.db:
        g.db.close()


def init_db():
    if not os.path.exists(SQL_SCHEMA_PATH):
        raise FileNotFoundError(f"Database schema not found: {SQL_SCHEMA_PATH}")

    with open(SQL_SCHEMA_PATH, encoding="utf-8") as schema_file:
        schema = schema_file.read()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def get_user_by_id(user_id):
    return query_db("SELECT id, full_name, email, role FROM users WHERE id = ?", (user_id,), one=True)


def get_user_with_password(email):
    return query_db("SELECT id, full_name, email, password_hash, role FROM users WHERE email = ?", (email,), one=True)


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


@app.route("/")
def index():
    return redirect(url_for("render_page", page="index.html"))


@app.route("/<path:page>")
def render_page(page):
    if ".." in page or page.startswith("/"):
        abort(404)
    if page not in ALLOWED_TEMPLATES:
        abort(404)
    return render_template(page)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("render_page", page="index.html"))


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify(error="Email and password are required."), 400

    user = get_user_with_password(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Invalid email or password."), 401

    session["user_id"] = user["id"]
    return jsonify(message="Logged in successfully.")


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not full_name or not email or not password:
        return jsonify(error="Name, email, and password are required."), 400

    if get_user_with_password(email):
        return jsonify(error="A user with that email already exists."), 409

    password_hash = generate_password_hash(password)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (full_name, email, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (full_name, email, password_hash, "user", datetime.utcnow(), datetime.utcnow()),
    )
    conn.commit()
    user_id = cur.lastrowid
    session["user_id"] = user_id

    return jsonify(message="Registration successful.")


@app.route("/api/profile")
def api_profile():
    user = get_current_user()
    if not user:
        return jsonify(error="You must be logged in to view profile."), 401

    enrolled_courses = query_db(
        """
        SELECT c.id, c.title, c.summary, IFNULL(p.percentage, 0) AS percentage
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN progress p ON p.course_id = c.id AND p.user_id = e.user_id
        WHERE e.user_id = ?
        """,
        (user["id"],),
    )

    return jsonify(
        user={
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        },
        courses=[dict(row) for row in enrolled_courses],
    )


@app.route("/api/courses")
def api_courses():
    rows = query_db("SELECT id, title, summary, description, price FROM courses WHERE status = 'published' ORDER BY id")
    return jsonify(courses=[dict(row) for row in rows])


@app.route("/api/courses/<int:course_id>/lessons")
def api_course_lessons(course_id):
    course = query_db("SELECT id FROM courses WHERE id = ? AND status = 'published'", (course_id,), one=True)
    if not course:
        return jsonify(error="Course not found."), 404

    rows = query_db(
        "SELECT id, title, description, order_index FROM lessons WHERE course_id = ? ORDER BY order_index",
        (course_id,),
    )
    return jsonify(lessons=[dict(row) for row in rows])


@app.route("/api/lessons/<int:lesson_id>/exercises")
def api_lesson_exercises(lesson_id):
    lesson = query_db("SELECT id FROM lessons WHERE id = ?", (lesson_id,), one=True)
    if not lesson:
        return jsonify(error="Lesson not found."), 404

    rows = query_db(
        "SELECT id, title, description, starter_code, difficulty FROM exercises WHERE lesson_id = ? ORDER BY id",
        (lesson_id,),
    )
    return jsonify(exercises=[dict(row) for row in rows])


@app.route("/api/exercises/<int:exercise_id>")
def api_exercise(exercise_id):
    row = query_db(
        "SELECT id, lesson_id, title, description, starter_code, test_cases, difficulty FROM exercises WHERE id = ?",
        (exercise_id,),
        one=True,
    )
    if not row:
        return jsonify(error="Exercise not found."), 404

    exercise = dict(row)
    try:
        exercise["test_cases"] = json.loads(exercise["test_cases"] or "[]")
    except json.JSONDecodeError:
        exercise["test_cases"] = []

    return jsonify(exercise)


def execute_python(code):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        completed = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = completed.stdout.strip()
        error = completed.stderr.strip()
        if completed.returncode != 0:
            return None, error or f"Process exited with return code {completed.returncode}."
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Execution timed out after 5 seconds."
    except Exception as exc:
        return None, str(exc)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@app.route("/api/execute-code", methods=["POST"])
def api_execute_code():
    data = request.get_json(silent=True) or {}
    code = data.get("code") or ""
    if not code:
        return jsonify(error="No code provided."), 400

    output, error = execute_python(code)
    if error:
        return jsonify(error=error), 400
    return jsonify(output=output)


@app.route("/api/exercises/<int:exercise_id>/submit", methods=["POST"])
def api_submit_exercise(exercise_id):
    data = request.get_json(silent=True) or {}
    code = data.get("code") or ""
    if not code:
        return jsonify(error="No code provided."), 400

    row = query_db(
        "SELECT id, test_cases FROM exercises WHERE id = ?",
        (exercise_id,),
        one=True,
    )
    if not row:
        return jsonify(error="Exercise not found."), 404

    try:
        test_cases = json.loads(row["test_cases"] or "[]")
    except json.JSONDecodeError:
        test_cases = []

    output, error = execute_python(code)
    if error:
        return jsonify(error=error), 400

    actual_lines = [line.strip() for line in (output or "").splitlines() if line.strip()]
    results = []
    passed = True

    for index, expected in enumerate(test_cases):
        actual = actual_lines[index] if index < len(actual_lines) else ""
        result_passed = str(actual) == str(expected)
        results.append({
            "expected": expected,
            "actual": actual,
            "passed": result_passed,
        })
        if not result_passed:
            passed = False

    return jsonify(passed=passed, test_results=results)


def require_admin():
    user = get_current_user()
    if not user or user["role"] != "admin":
        abort(jsonify(error="Admin access required."), 403)
    return user


@app.route("/api/admin/courses", methods=["GET", "POST"])
def api_admin_courses():
    require_admin()

    if request.method == "GET":
        rows = query_db(
            "SELECT id, title, summary, description, price, status FROM courses ORDER BY id DESC"
        )
        return jsonify(courses=[dict(row) for row in rows])

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    summary = (data.get("summary") or "").strip()
    description = (data.get("description") or "").strip()
    price = (data.get("price") or "Free").strip()

    if not title or not summary:
        return jsonify(error="Title and summary are required."), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO courses (title, summary, description, price, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, summary, description, price, "published", session["user_id"], datetime.utcnow(), datetime.utcnow()),
    )
    conn.commit()
    return jsonify(message="Course saved successfully.")


@app.route("/api/admin/events", methods=["GET", "POST"])
def api_admin_events():
    require_admin()

    if request.method == "GET":
        rows = query_db(
            "SELECT id, title, description, event_date, location, status FROM events ORDER BY id DESC"
        )
        return jsonify(events=[dict(row) for row in rows])

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    event_date = (data.get("event_date") or "").strip()
    location = (data.get("location") or "").strip()
    description = (data.get("description") or "").strip()

    if not title or not event_date:
        return jsonify(error="Title and date are required."), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO events (title, description, event_date, location, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, description, event_date, location, "published", session["user_id"], datetime.utcnow(), datetime.utcnow()),
    )
    conn.commit()
    return jsonify(message="Event saved successfully.")


@app.errorhandler(404)
def handle_404(error):
    return jsonify(error="Resource not found."), 404


@app.errorhandler(400)
def handle_400(error):
    if isinstance(error, HTTPException) and error.description:
        return jsonify(error=error.description), 400
    return jsonify(error="Bad request."), 400


@app.errorhandler(500)
def handle_500(error):
    return jsonify(error="Internal server error."), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
