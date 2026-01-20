import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

APP_SECRET = os.environ.get("APP_SECRET", "change-me")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me-too")
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "hh_detailing.db"))

app = Flask(__name__)
app.secret_key = APP_SECRET


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            city TEXT,
            postal_code TEXT,
            notes TEXT,
            service_type TEXT NOT NULL,
            package_code TEXT NOT NULL,
            extras_json TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_slot
        ON bookings(date, time);
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocked_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            date TEXT NOT NULL UNIQUE,
            reason TEXT
        );
    """)
    conn.commit()
    conn.close()


def is_blocked(date_str: str) -> bool:
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM blocked_dates WHERE date = ? LIMIT 1", (date_str,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def slot_taken(date_str: str, time_str: str) -> bool:
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM bookings WHERE date = ? AND time = ? LIMIT 1", (date_str, time_str))
    row = cur.fetchone()
    conn.close()
    return row is not None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/boeken")
def book():
    return render_template("book.html")


@app.route("/api/availability")
def availability():
    date_str = request.args.get("date", "").strip()
    if not date_str:
        return jsonify({"ok": False, "error": "missing date"}), 400

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT time FROM bookings WHERE date = ?", (date_str,))
    taken = [r["time"] for r in cur.fetchall()]
    conn.close()

    return jsonify({
        "ok": True,
        "date": date_str,
        "blocked": is_blocked(date_str),
        "taken": taken
    })


@app.route("/reserve", methods=["POST"])
def reserve():
    customer_name = request.form.get("customer_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    postal_code = request.form.get("postal_code", "").strip()
    notes = request.form.get("notes", "").strip()

    service_type = request.form.get("service_type", "detailing").strip()
    package_code = request.form.get("package_code", "").strip()
    date_str = request.form.get("date", "").strip()
    time_str = request.form.get("time", "").strip()
    extras = request.form.getlist("extras")

    if not customer_name or not phone or not package_code or not date_str or not time_str:
        flash("Vul je naam, telefoon, pakket, datum en tijd in.", "error")
        return redirect(url_for("book"))

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        if d < datetime.now().date():
            flash("Kies een datum in de toekomst.", "error")
            return redirect(url_for("book"))
    except Exception:
        flash("Ongeldige datum.", "error")
        return redirect(url_for("book"))

    if is_blocked(date_str):
        flash("Die datum is niet beschikbaar. Kies een andere dag.", "error")
        return redirect(url_for("book"))

    if slot_taken(date_str, time_str):
        flash("Dit tijdstip is net gereserveerd. Kies een andere tijd.", "error")
        return redirect(url_for("book"))

    import json
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bookings (
            created_at, customer_name, phone, email, address, city, postal_code, notes,
            service_type, package_code, extras_json, date, time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(timespec="seconds") + "Z",
        customer_name, phone, email, address, city, postal_code, notes,
        service_type, package_code, json.dumps(extras, ensure_ascii=False),
        date_str, time_str
    ))
    conn.commit()
    conn.close()

    return render_template(
        "success.html",
        customer_name=customer_name, date=date_str, time=time_str,
        package_code=package_code, service_type=service_type
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin"))
        flash("Wachtwoord klopt niet.", "error")
        return redirect(url_for("admin"))

    if not session.get("is_admin"):
        return render_template("admin_login.html")

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY date ASC, time ASC")
    bookings = cur.fetchall()
    cur.execute("SELECT * FROM blocked_dates ORDER BY date ASC")
    blocked = cur.fetchall()
    conn.close()
    return render_template("admin.html", bookings=bookings, blocked=blocked)


@app.post("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin"))


@app.post("/admin/block")
def admin_block():
    if not session.get("is_admin"):
        return redirect(url_for("admin"))
    date_str = request.form.get("date", "").strip()
    reason = request.form.get("reason", "").strip()

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        flash("Ongeldige datum.", "error")
        return redirect(url_for("admin"))

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO blocked_dates (created_at, date, reason) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(timespec="seconds") + "Z", date_str, reason)
    )
    conn.commit()
    conn.close()

    flash("Datum geblokkeerd.", "ok")
    return redirect(url_for("admin"))


@app.post("/admin/unblock")
def admin_unblock():
    if not session.get("is_admin"):
        return redirect(url_for("admin"))
    date_str = request.form.get("date", "").strip()
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM blocked_dates WHERE date = ?", (date_str,))
    conn.commit()
    conn.close()

    flash("Datum vrijgegeven.", "ok")
    return redirect(url_for("admin"))


@app.post("/admin/delete_booking")
def admin_delete_booking():
    if not session.get("is_admin"):
        return redirect(url_for("admin"))
    booking_id = request.form.get("id", "").strip()
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

    flash("Reservering verwijderd.", "ok")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
