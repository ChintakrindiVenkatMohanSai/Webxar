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

    # ⭐ IMPORTANT FIX
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    with sqlite3.connect("projects.db") as conn:
        conn.execute(
            "INSERT INTO projects(name,file,type) VALUES(?,?,?)",
            (name, filename, ptype)
        )

    return redirect("/")



@app.route("/uploads/")
def uploads_root():
    return "Upload folder ready. Specify a filename."

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
    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=False
    )

# ---------- RUN SERVER ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)