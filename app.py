from flask import Flask, render_template, request, redirect, send_from_directory, abort
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)

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
init_db()


# ---------- DASHBOARD ----------
@app.route("/")
def dashboard():
    with sqlite3.connect("projects.db") as conn:
        projects = conn.execute("SELECT * FROM projects").fetchall()
    return render_template("dashboard.html", projects=projects)


# ---------- CREATE PROJECT ----------
@app.route("/create")
def create_project():
    return render_template("create_project.html")


@app.route("/save", methods=["POST"])
def save():
    name = request.form.get("name")
    ptype = request.form.get("type")
    file = request.files.get("file")

    if not file or file.filename == "":
        return "No file uploaded"

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    with sqlite3.connect("projects.db") as conn:
        conn.execute(
            "INSERT INTO projects(name,file,type) VALUES(?,?,?)",
            (name, filename, ptype)
        )
        conn.commit()

    return redirect("/")


# ---------- AR ROUTES ----------
@app.route("/image-ar/<path:file>")
def image_ar(file):
    return render_template("image_ar.html", file=file)


@app.route("/model-ar/<path:file>")
def model_ar(file):
    return render_template("model_ar.html", file=file)


@app.route("/wall-ar")
def wall_ar():
    return render_template("wall_ar.html")


# ---------- SERVE UPLOADED FILES ----------
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        abort(404)

    return send_from_directory(UPLOAD_FOLDER, filename)


# ---------- DELETE PROJECT + FILE ----------
@app.route("/delete/<int:id>")
def delete_project(id):

    with sqlite3.connect("projects.db") as conn:
        project = conn.execute(
            "SELECT file FROM projects WHERE id=?",
            (id,)
        ).fetchone()

        # Delete file from uploads folder
        if project:
            filepath = os.path.join(UPLOAD_FOLDER, project[0])
            if os.path.exists(filepath):
                os.remove(filepath)

        # Delete DB record
        conn.execute("DELETE FROM projects WHERE id=?", (id,))
        conn.commit()

    return redirect("/")


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)