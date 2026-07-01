from pathlib import Path
from datetime import timedelta
import sqlite3
import os

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "database.sql"

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key")
app.permanent_session_lifetime = timedelta(days=7)

ALLOWED_PAGES = {
    "index.html",
    "about.html",
    "contact.html",
    "community.html",
    "courses.html",
    "course-detail.html",
    "pricing.html",
    "profile.html",
    "login.html",
    "register.html",
    "lab.html",
    "admin.html",
}

RESTRICTED_PAGES = {
    "course-detail.html",
    "profile.html",
    "lab.html",
    "admin.html",
}


def get_db():
    if hasattr(g, "_db") and g._db:
        return g._db

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    g._db = conn
    return conn


@app.teardown_appcontext
def close_db(exception=None):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def init_db():
    if DB_PATH.exists():
        return

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError("database.sql schema file not found")

    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(sql)
    conn.commit()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    row = query_db("SELECT id, full_name, email, role FROM users WHERE id = ?", (user_id,), one=True)
    return row_to_dict(row)


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


@app.before_request
def protect_pages():
    if request.endpoint == "render_page":
        page = request.view_args.get("page") if request.view_args else None
        if page in RESTRICTED_PAGES and not session.get("user_id"):
            return redirect(url_for("render_page", page="login.html"))


@app.route("/")
def index():
    return redirect(url_for("render_page", page="index.html"))


@app.route("/<path:page>")
def render_page(page):
    if page not in ALLOWED_PAGES:
        abort(404)

    if page in RESTRICTED_PAGES and not session.get("user_id"):
        return redirect(url_for("render_page", page="login.html"))

    return render_template(page)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("render_page", page="index.html"))


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not full_name or not email or not password:
        return jsonify(error="Full name, email, and password are required."), 400

    existing_user = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
    if existing_user:
        return jsonify(error="This email is already registered."), 400

    password_hash = generate_password_hash(password)
    db = get_db()
    db.execute(
        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
        (full_name, email, password_hash),
    )
    db.commit()

    return jsonify(message="Registration successful. Please log in."), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify(error="Email and password are required."), 400

    user = query_db(
        "SELECT id, full_name, email, password_hash, role FROM users WHERE email = ?",
        (email,),
        one=True,
    )
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Invalid email or password."), 401

    session.permanent = True
    session["user_id"] = user["id"]
    return jsonify(message="Login successful.")


@app.route("/api/profile")
def api_profile():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(error="Authentication required."), 401

    user = query_db(
        "SELECT id, full_name, email, role FROM users WHERE id = ?",
        (user_id,),
        one=True,
    )
    if not user:
        return jsonify(error="User not found."), 404

    courses = query_db(
        "SELECT c.id, c.title, c.summary, c.description, COALESCE(p.percentage, 0) AS percentage "
        "FROM enrollments e "
        "JOIN courses c ON c.id = e.course_id "
        "LEFT JOIN progress p ON p.user_id = e.user_id AND p.course_id = e.course_id "
        "WHERE e.user_id = ? "
        "ORDER BY c.title ASC",
        (user_id,),
    )

    return jsonify(user=row_to_dict(user), courses=[row_to_dict(row) for row in courses])


@app.route("/api/courses")
def api_courses():
    rows = query_db(
        "SELECT id, title, summary, description, price, status FROM courses "
        "WHERE status = 'published' ORDER BY created_at DESC"
    )
    return jsonify(courses=[row_to_dict(row) for row in rows])


@app.route("/api/courses/<int:course_id>/lessons")
def api_course_lessons(course_id):
    if not session.get("user_id"):
        return jsonify(error="Authentication required."), 401

    course = query_db("SELECT id FROM courses WHERE id = ?", (course_id,), one=True)
    if not course:
        return jsonify(error="Course not found."), 404

    lessons = query_db(
        "SELECT id, course_id, title, description, order_index FROM lessons "
        "WHERE course_id = ? ORDER BY order_index ASC",
        (course_id,),
    )
    return jsonify(lessons=[row_to_dict(row) for row in lessons])


@app.route("/api/courses/<int:course_id>/start", methods=["POST"])
def api_course_start(course_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(error="Authentication required."), 401

    course = query_db("SELECT id, title FROM courses WHERE id = ?", (course_id,), one=True)
    if not course:
        return jsonify(error="Course not found."), 404

    db = get_db()
    enrollment = query_db(
        "SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?", (user_id, course_id), one=True
    )
    if not enrollment:
        db.execute(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            (user_id, course_id),
        )

    progress = query_db(
        "SELECT id FROM progress WHERE user_id = ? AND course_id = ?", (user_id, course_id), one=True
    )
    if not progress:
        db.execute(
            "INSERT INTO progress (user_id, course_id, percentage) VALUES (?, ?, 0)",
            (user_id, course_id),
        )

    db.commit()
    return jsonify(message="Course started and added to your profile.")


@app.route("/api/lessons/<int:lesson_id>/exercises")
def api_lesson_exercises(lesson_id):
    if not session.get("user_id"):
        return jsonify(error="Authentication required."), 401

    lesson = query_db("SELECT id, course_id FROM lessons WHERE id = ?", (lesson_id,), one=True)
    if not lesson:
        return jsonify(error="Lesson not found."), 404

    exercises = query_db(
        "SELECT id, lesson_id, title, description, difficulty FROM exercises "
        "WHERE lesson_id = ? ORDER BY id ASC",
        (lesson_id,),
    )
    return jsonify(exercises=[row_to_dict(row) for row in exercises])


@app.route("/api/exercises/<int:exercise_id>")
def api_exercise(exercise_id):
    if not session.get("user_id"):
        return jsonify(error="Authentication required."), 401

    exercise = query_db(
        "SELECT id, lesson_id, title, description, starter_code, test_cases, difficulty FROM exercises WHERE id = ?",
        (exercise_id,),
        one=True,
    )
    if not exercise:
        return jsonify(error="Exercise not found."), 404

    return jsonify(row_to_dict(exercise))


@app.route("/api/execute-code", methods=["POST"])
def api_execute_code():
    if not session.get("user_id"):
        return jsonify(error="Authentication required."), 401

    return jsonify(error="Code execution is not available in this deployment."), 501


@app.route("/api/exercises/<int:exercise_id>/submit", methods=["POST"])
def api_submit_exercise(exercise_id):
    if not session.get("user_id"):
        return jsonify(error="Authentication required."), 401

    return jsonify(error="Exercise submission is not available in this deployment."), 501


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
