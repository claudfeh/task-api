import os
import time

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "tasks"),
    "user": os.environ.get("DB_USER", "taskuser"),
    "password": os.environ.get("DB_PASSWORD", "taskpass"),
}


def get_conn(retries=10):
    """Connect to Postgres, retrying while the DB is still starting."""
    last_error = None
    for _ in range(retries):
        try:
            return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


@app.get("/health")
def health():
    try:
        conn = get_conn(retries=1)
        conn.close()
        db_status = "up"
    except Exception:
        db_status = "down"
    code = 200 if db_status == "up" else 503
    return jsonify(service="task-api", database=db_status), code


@app.get("/api/tasks")
def list_tasks():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


@app.post("/api/tasks")
def create_task():
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done",
        (title,),
    )
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return jsonify(row), 201


@app.patch("/api/tasks/<int:task_id>")
def toggle_task(task_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET done = NOT done WHERE id = %s "
        "RETURNING id, title, done",
        (task_id,),
    )
    row = cur.fetchone()
    conn.commit()
    conn.close()
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if not deleted:
        return jsonify(error="not found"), 404
    return "", 204
