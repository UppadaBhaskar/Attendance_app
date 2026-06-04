"""
SECE Attendance System — Flask + MySQL (raw SQL only).
All business data is read/written in MySQL; session stores login id only.
"""
from datetime import date
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

import db

app = Flask(__name__)
app.secret_key = "sece-attendance-dev-secret"

SHORTAGE_THRESHOLD = 75


def get_faculty():
    return db.query("SELECT * FROM faculty ORDER BY id LIMIT 1", fetchone=True)


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Please login with the correct role.", "error")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def attendance_percent(student_id, faculty_id):
    row = db.query(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS present_count
        FROM attendance
        WHERE student_id = %s AND faculty_id = %s
        """,
        (student_id, faculty_id),
        fetchone=True,
    )
    total = row["total"] or 0
    if total == 0:
        return 0, 0, 0
    present = row["present_count"] or 0
    return total, present, round((present / total) * 100)


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session["role"] == "student":
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("faculty_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role", "student")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if role == "student":
            user = db.query(
                "SELECT * FROM students WHERE LOWER(email) = %s AND password = %s",
                (email, password),
                fetchone=True,
            )
            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["role"] = "student"
                session["name"] = user["name"]
                session["email"] = user["email"]
                session["roll_no"] = user["roll_no"]
                return redirect(url_for("student_dashboard"))
        else:
            user = db.query(
                "SELECT * FROM faculty WHERE LOWER(email) = %s AND password = %s",
                (email, password),
                fetchone=True,
            )
            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["role"] = "faculty"
                session["name"] = user["name"]
                session["email"] = user["email"]
                return redirect(url_for("faculty_dashboard"))

        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([name, roll_no, email, password, phone]):
            flash("All fields are required.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        exists = db.query(
            "SELECT id FROM students WHERE email = %s OR roll_no = %s",
            (email, roll_no),
            fetchone=True,
        )
        if exists:
            flash("Email or roll number already registered.", "error")
            return render_template("register.html")

        db.execute(
            "INSERT INTO students (name, roll_no, email, password, phone) VALUES (%s, %s, %s, %s, %s)",
            (name, roll_no, email, password, phone),
        )
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/student/dashboard")
@login_required("student")
def student_dashboard():
    faculty = get_faculty()
    if not faculty:
        flash("Faculty not configured.", "error")
        return render_template("student/dashboard.html", summary=None)

    total, present, percent = attendance_percent(session["user_id"], faculty["id"])
    summary = {
        "faculty_name": faculty["name"],
        "total": total,
        "present": present,
        "absent": total - present,
        "percent": percent,
    }
    return render_template("student/dashboard.html", summary=summary)


@app.route("/student/detail")
@login_required("student")
def student_detail():
    faculty = get_faculty()
    if not faculty:
        return redirect(url_for("student_dashboard"))

    records = db.query(
        """
        SELECT attendance_date, status
        FROM attendance
        WHERE student_id = %s AND faculty_id = %s
        ORDER BY attendance_date DESC
        """,
        (session["user_id"], faculty["id"]),
        fetchall=True,
    )
    total, present, percent = attendance_percent(session["user_id"], faculty["id"])
    return render_template(
        "student/detail.html",
        faculty=faculty,
        records=records,
        percent=percent,
        total=total,
        present=present,
    )


def render_faculty_page(mark_date=None):
    """Build single faculty page — all data from MySQL."""
    faculty = get_faculty()
    mark_date = mark_date or str(date.today())
    students = db.query("SELECT * FROM students ORDER BY roll_no", fetchall=True)

    marks = {}
    rows = db.query(
        "SELECT student_id, status FROM attendance WHERE faculty_id = %s AND attendance_date = %s",
        (faculty["id"], mark_date),
        fetchall=True,
    )
    for row in rows:
        marks[row["student_id"]] = row["status"]

    report = []
    for student in students:
        total, present, percent = attendance_percent(student["id"], faculty["id"])
        report.append({
            "student": student,
            "total": total,
            "present": present,
            "absent": total - present,
            "percent": percent,
        })

    student_count = db.query("SELECT COUNT(*) AS c FROM students", fetchone=True)["c"]
    session_count = db.query(
        "SELECT COUNT(DISTINCT attendance_date) AS c FROM attendance WHERE faculty_id = %s",
        (faculty["id"],),
        fetchone=True,
    )["c"]
    shortage_row = db.query(
        """
        SELECT COUNT(*) AS c FROM (
            SELECT s.id,
                   ROUND(100.0 * SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)
                         / NULLIF(COUNT(a.id), 0)) AS pct
            FROM students s
            LEFT JOIN attendance a ON a.student_id = s.id AND a.faculty_id = %s
            GROUP BY s.id
            HAVING COUNT(a.id) > 0 AND pct < %s
        ) AS below_threshold
        """,
        (faculty["id"], SHORTAGE_THRESHOLD),
        fetchone=True,
    )
    shortage = shortage_row["c"] if shortage_row else 0

    return render_template(
        "faculty/dashboard.html",
        faculty=faculty,
        students=students,
        marks=marks,
        mark_date=mark_date,
        today=str(date.today()),
        report=report,
        student_count=student_count,
        session_count=session_count,
        shortage=shortage,
    )


@app.route("/faculty/dashboard", methods=["GET", "POST"])
@login_required("faculty")
def faculty_dashboard():
    faculty = get_faculty()
    mark_date = request.form.get("mark_date") or request.args.get("date") or str(date.today())

    if request.method == "POST":
        mark_date = request.form.get("mark_date", str(date.today()))
        students = db.query("SELECT * FROM students ORDER BY roll_no", fetchall=True)
        for student in students:
            status = request.form.get(f"status_{student['id']}", "absent")
            if status not in ("present", "absent"):
                status = "absent"
            existing = db.query(
                """
                SELECT id FROM attendance
                WHERE student_id = %s AND faculty_id = %s AND attendance_date = %s
                """,
                (student["id"], faculty["id"], mark_date),
                fetchone=True,
            )
            if existing:
                db.execute("UPDATE attendance SET status = %s WHERE id = %s", (status, existing["id"]))
            else:
                db.execute(
                    """
                    INSERT INTO attendance (student_id, faculty_id, attendance_date, status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (student["id"], faculty["id"], mark_date, status),
                )
        flash(f"Attendance saved for {mark_date}.", "success")
        return redirect(url_for("faculty_dashboard", date=mark_date))

    return render_faculty_page(mark_date)


@app.route("/faculty/mark-attendance", methods=["GET", "POST"])
@login_required("faculty")
def faculty_mark_attendance():
    date_arg = request.args.get("date") or request.form.get("mark_date")
    if date_arg:
        return redirect(url_for("faculty_dashboard", date=date_arg))
    return redirect(url_for("faculty_dashboard"))


@app.route("/faculty/students/delete/<int:student_id>", methods=["POST"])
@login_required("faculty")
def faculty_delete_student(student_id):
    student = db.query("SELECT id FROM students WHERE id = %s", (student_id,), fetchone=True)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("faculty_dashboard"))
    db.execute("DELETE FROM students WHERE id = %s", (student_id,))
    flash("Student deleted.", "success")
    mark_date = request.form.get("mark_date") or request.args.get("date")
    if mark_date:
        return redirect(url_for("faculty_dashboard", date=mark_date))
    return redirect(url_for("faculty_dashboard"))


@app.route("/faculty/reports")
@login_required("faculty")
def faculty_reports():
    return redirect(url_for("faculty_dashboard") + "#reports")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
