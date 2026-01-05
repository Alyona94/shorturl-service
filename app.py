import os
import re
import sqlite3
from urllib.parse import urlparse

from flask import Flask, request, jsonify, redirect, abort, send_from_directory

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "urls.db")

URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def ensure_db_dir():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def get_conn():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                short_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_url  TEXT NOT NULL
            )
            """
        )
        conn.commit()


def is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    if not URL_RE.search(url):
        return False
    p = urlparse(url)
    return bool(p.scheme in ("http", "https") and p.netloc)


# ----- UI -----

@app.get("/")
def ui_index():
    return send_from_directory(os.path.dirname(__file__), "index.html")


# ----- API -----

@app.post("/shorten")
def shorten():
    data = request.get_json(silent=True) or {}
    full_url = data.get("url")

    if not is_valid_url(full_url):
        return jsonify({"error": "Invalid or missing 'url'"}), 400

    with get_conn() as conn:
        cur = conn.execute("INSERT INTO links(full_url) VALUES(?)", (full_url,))
        conn.commit()
        short_id = int(cur.lastrowid)

    return jsonify({"short_id": short_id, "full_url": full_url}), 201


@app.get("/<int:short_id>")
def go(short_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT full_url FROM links WHERE short_id = ?",
            (short_id,),
        ).fetchone()

    if not row:
        abort(404)

    return redirect(row["full_url"], code=302)


@app.get("/stats/<int:short_id>")
def stats(short_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT short_id, full_url FROM links WHERE short_id = ?",
            (short_id,),
        ).fetchone()

    if not row:
        abort(404)

    return jsonify({"short_id": int(row["short_id"]), "full_url": row["full_url"]})


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
