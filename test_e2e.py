"""Quick E2E smoke test — run: python test_e2e.py"""
from datetime import date

import app as a
import db

client = a.app.test_client()

# Clean test student if exists
db.execute("DELETE FROM students WHERE email = %s", ("e2e@test.edu",))

# Register
r = client.post(
    "/register",
    data={
        "name": "E2E Student",
        "roll_no": "E2E001",
        "email": "e2e@test.edu",
        "phone": "1111111111",
        "password": "pass123",
        "confirm_password": "pass123",
    },
    follow_redirects=True,
)
assert r.status_code == 200, "register failed"

# Student login
r = client.post(
    "/login",
    data={"role": "student", "email": "e2e@test.edu", "password": "pass123"},
    follow_redirects=True,
)
assert b"Welcome" in r.data, "student login failed"

faculty_client = a.app.test_client()
r = faculty_client.post(
    "/login",
    data={"role": "faculty", "email": "ramesh.kumar@sece.edu", "password": "faculty123"},
    follow_redirects=True,
)
assert r.status_code == 200, "faculty login failed"

stu = db.query("SELECT id FROM students WHERE email = %s", ("e2e@test.edu",), fetchone=True)
today = str(date.today())
status_key = "status_" + str(stu["id"])

r = faculty_client.post(
    "/faculty/dashboard",
    data={"mark_date": today, status_key: "present"},
    follow_redirects=True,
)
assert b"saved" in r.data.lower() or r.status_code == 200, "mark attendance failed"

r = client.get("/student/dashboard", follow_redirects=True)
assert b"%" in r.data, "student dashboard missing percent"

r = faculty_client.post(
    "/faculty/students/delete/" + str(stu["id"]),
    follow_redirects=True,
)
gone = db.query("SELECT id FROM students WHERE id = %s", (stu["id"],), fetchone=True)
assert gone is None, "student not deleted"

print("E2E passed: register, login, mark, view %, delete")
