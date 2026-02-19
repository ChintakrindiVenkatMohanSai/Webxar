from flask import Flask, render_template, request, redirect, send_from_directory, abort, session
import sqlite3, os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- DATABASE ----------
def init_db():
    with sqlite3.connect("projects.db") as conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            file TEXT,
            type TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS auth(
            id INTEGER PRIMARY KEY,
            pin TEXT
        )
        """)

        # default PIN = 1234
        conn.execute("""
        INSERT OR IGNORE INTO auth(id,pin)
        VALUES(1,'1234')
        """)

        conn.commit()

init_db()


# ---------- LOGIN REQUIRED ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("auth"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


# ---------- DASHBOARD ----------
@app.route("/")
def dashboard():
    with sqlite3.connect("projects.db") as conn:
        projects = conn.execute("SELECT * FROM projects").fetchall()
    return render_template("dashboard.html", projects=projects)


# ---------- LOGIN ----------
@app.route("/login")
def login():
    return render_template("pin_login.html")


@app.route("/verify-pin", methods=["POST"])
def verify_pin():

    pin = request.form["pin"]

    with sqlite3.connect("projects.db") as conn:
        row = conn.execute("SELECT pin FROM auth WHERE id=1").fetchone()

    if row and row[0] == pin:
        session["auth"] = True
        return redirect("/create")

    return "Wrong PIN"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- CREATE PROJECT ----------
@app.route("/create")
@login_required
def create_project():
    return render_template("create_project.html")


@app.route("/save", methods=["POST"])
@login_required
def save():

    name = request.form.get("name")
    ptype = request.form.get("type")
    file = request.files.get("file")

    if not file or file.filename == "":
        return "No file uploaded"

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    with sqlite3.connect("projects.db") as conn:
        conn.execute(
            "INSERT INTO projects(name,file,type) VALUES(?,?,?)",
            (name, filename, ptype)
        )
        conn.commit()

    return redirect("/")


# ---------- DELETE ----------
@app.route("/delete/<int:id>")
@login_required
def delete_project(id):

    with sqlite3.connect("projects.db") as conn:
        project = conn.execute(
            "SELECT file FROM projects WHERE id=?",
            (id,)
        ).fetchone()

        if project:
            filepath = os.path.join(UPLOAD_FOLDER, project[0])
            if os.path.exists(filepath):
                os.remove(filepath)

        conn.execute("DELETE FROM projects WHERE id=?", (id,))
        conn.commit()

    return redirect("/")


# ---------- FILE SERVE ----------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        abort(404)

    return send_from_directory(UPLOAD_FOLDER, filename)


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)