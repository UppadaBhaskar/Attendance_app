# SECE Attendance System

Beginner-friendly Flask app with MySQL. All student and attendance data is stored **only in the database** (`CDB`).

## Setup

1. Start MySQL on port 3306.
2. Install Python packages:

```bash
cd sece_attendance
pip install -r requirements.txt
```

3. Create tables (run once):

```bash
python setup_db.py
```

4. Start the app:

```bash
python app.py
```

5. Open **http://127.0.0.1:5000**

## Default faculty login

| Email | Password |
|-------|----------|
| ramesh.kumar@sece.edu | faculty123 |

Students must use **Register** before logging in.

## Database settings

Edit [`config.py`](config.py) if your MySQL user or password differs.

## Project layout

| File | Purpose |
|------|---------|
| `app.py` | All web routes |
| `db.py` | SQL query helpers |
| `config.py` | DB connection settings |
| `schema.sql` | Table definitions |
| `setup_db.py` | Create database and tables |
| `templates/` | HTML pages |
| `static/` | CSS and JavaScript |
