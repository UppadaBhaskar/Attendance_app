"""Run once: python setup_db.py"""
import mysql.connector

import config

STATEMENTS = [
    "CREATE DATABASE IF NOT EXISTS CDB",
    "USE CDB",
    """
    CREATE TABLE IF NOT EXISTS faculty (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL,
        department VARCHAR(100) DEFAULT 'CSE',
        designation VARCHAR(100) DEFAULT 'Faculty'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        roll_no VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL,
        phone VARCHAR(20) DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS attendance (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        faculty_id INT NOT NULL,
        attendance_date DATE NOT NULL,
        status ENUM('present', 'absent') NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (faculty_id) REFERENCES faculty(id),
        UNIQUE KEY one_mark_per_day (student_id, faculty_id, attendance_date)
    )
    """,
    """
    INSERT INTO faculty (name, email, password, department, designation)
    SELECT 'Dr. Ramesh Kumar', 'ramesh.kumar@sece.edu', 'faculty123', 'CSE', 'Professor'
    FROM DUAL
    WHERE NOT EXISTS (SELECT 1 FROM faculty LIMIT 1)
    """,
]


def main():
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    cursor = conn.cursor()
    try:
        for sql in STATEMENTS:
            cursor.execute(sql)
        conn.commit()
        print("Database CDB is ready.")
        print("Faculty: ramesh.kumar@sece.edu / faculty123")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
