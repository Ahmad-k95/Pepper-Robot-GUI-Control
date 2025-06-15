#!/usr/bin/python2.7
# coding=utf-8
import Tkinter as tk  # type: ignore
import os
import sqlite3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "data/robot_data.db")


# --------------------------------------------------------------- Postures ---------------------------------------------------------------#

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_posture_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS postures (
        name TEXT PRIMARY KEY,
        R1 REAL, R2 REAL, R3 REAL, R4 REAL, R5 REAL, R6 REAL,
        L1 REAL, L2 REAL, L3 REAL, L4 REAL, L5 REAL, L6 REAL,
        T1 REAL, T2 REAL, T3 REAL,
        H1 REAL, H2 REAL)""")

    conn.commit()
    conn.close()


def insert_posture(data):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO postures VALUES (
                ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?
            )
        """, data)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_posture(name, angles):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE postures SET
            R1=?, R2=?, R3=?, R4=?, R5=?, R6=?,
            L1=?, L2=?, L3=?, L4=?, L5=?, L6=?,
            T1=?, T2=?, T3=?,
            H1=?, H2=?
        WHERE name=?
    """, angles + [name])
    conn.commit()
    conn.close()


def delete_posture_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM postures WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def get_posture_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM postures WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result  # tuple: (name, R1, R2, ..., H2) ou None


# --------------------------------------------------------------- Motions ---------------------------------------------------------------#

def create_motion_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motion_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motion_id INTEGER,
            posture_name TEXT,
            duration REAL,
            FOREIGN KEY (motion_id) REFERENCES motions(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def insert_motion_to_db(name, steps):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO motions (name) VALUES (?)", (name,))
    motion_id = cursor.lastrowid
    for posture_name, duration in steps:
        cursor.execute("""
            INSERT INTO motion_steps (motion_id, posture_name, duration)
            VALUES (?, ?, ?)
        """, (motion_id, posture_name, float(duration)))

    conn.commit()
    conn.close()


def motion_exists(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM motions WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def delete_motion_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM motions WHERE name = ?", (name,))
    result = cursor.fetchone()
    if result:
        motion_id = result[0]
        cursor.execute("DELETE FROM motion_steps WHERE motion_id = ?", (motion_id,))
        cursor.execute("DELETE FROM motions WHERE id = ?", (motion_id,))
    conn.commit()
    conn.close()


def get_motion(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM motions WHERE name = ?", (name,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return []
    motion_id = result[0]
    cursor.execute("""
        SELECT posture_name, duration
        FROM motion_steps
        WHERE motion_id = ?
        ORDER BY id ASC
    """, (motion_id,))
    steps = cursor.fetchall()
    conn.close()
    return steps  # Ex: [('p11', 1.0), ('p12', 1.0), ...]


def load_selected_motion_from_db(app_state, frame2):
    conn = get_connection()
    cursor = conn.cursor()
    motion_name = app_state.selected_motion
    cursor.execute("SELECT id FROM motions WHERE name = ?", (motion_name,))
    row = cursor.fetchone()
    if row:
        motion_id = row[0]
        cursor.execute("""
            SELECT posture_name
            FROM motion_steps
            WHERE motion_id = ?
            ORDER BY id ASC
        """, (motion_id,))
        steps = cursor.fetchall()

        for step in steps:
            posture_name = step[0]
            frame2.post_motion_listbox.insert(tk.END, posture_name)
    conn.close()


# --------------------------------------------------------------- Codes ---------------------------------------------------------------#

def create_experiment_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            step_index INTEGER NOT NULL,
            command_type TEXT NOT NULL,
            command_value TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def delete_experiment_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM experiments WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def insert_experiment(name, code_text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO experiments (name) VALUES (?)", (name,))
    experiment_id = cursor.lastrowid
    lines = code_text.strip().splitlines()
    for index, line in enumerate(lines):
        line = line.strip()
        if "=" in line:
            command_type, command_value = line.split("=", 1)
            command_type = command_type.strip()
            command_value = command_value.strip()
        else:
            command_type = line.strip()
            command_value = None
        cursor.execute("""
            INSERT INTO experiment_steps (experiment_id, step_index, command_type, command_value)
            VALUES (?, ?, ?, ?)
        """, (experiment_id, index, command_type, command_value))

    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------------------------------------------------------------------------#
