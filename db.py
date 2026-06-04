"""MySQL helpers — raw SQL only, no ORM."""
import mysql.connector
from mysql.connector import Error

import config

DB_CONFIG = {
    "host": config.DB_HOST,
    "port": config.DB_PORT,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
    "database": config.DB_NAME,
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def query(sql, params=None, fetchone=False, fetchall=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return None
    finally:
        cursor.close()
        conn.close()


def execute(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        if cursor.lastrowid:
            return cursor.lastrowid
        return cursor.rowcount
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
