from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
from werkzeug.security import check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename

from extractor import extract_text
from parser import parse
from writer import fill_template
from datetime import timedelta
from flask import Flask, request, jsonify

# 🔐 إعداد التطبيق
app = Flask(__name__, static_folder='static')
app.permanent_session_lifetime = timedelta(hours=1)
app.secret_key = os.environ.get("SECRET_KEY", "change-this")

# 🔐 بيانات الدخول من Render
USERNAME = os.environ.get("APP_USERNAME")
PASSWORD_HASH = os.environ.get("APP_PASSWORD_HASH")

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
TEMPLATE_PATH = "template.docx"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🔐 التحقق
def check_auth(u, p):
    return u == USERNAME and check_password_hash(PASSWORD_HASH, p)

# 🔒 حماية الصفحات
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# 🔐 تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if check_auth(u, p):
            session.permanent = True
            session["logged_in"] = True
            return redirect("/")
        else:
            error = "بيانات غير صحيحة"

    return render_template("login.html", error=error)

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()

    username = data.get("email")   # نفس اسم الحقل في التطبيق
    password = data.get("password")

    if check_auth(username, password):
        return jsonify({"token": "valid-user"})
    else:
        return jsonify({"error": "invalid credentials"}), 401

# 🚪 تسجيل الخروج
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/api/upload", methods=["POST"])
def api_upload():

    auth = request.headers.get("Authorization")

    if not auth or "valid-user" not in auth:
        return {"error": "unauthorized"}, 401

    file = request.files.get("file")

    if not file:
        return {"error": "no file"}, 400

    filename = secure_filename(file.filename)
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(pdf_path)

    if os.path.getsize(pdf_path) == 0:
        return {"error": "empty file"}, 400

    try:
        # 🔥 نفس المعالجة
        text = extract_text(pdf_path)
        data = parse(text)

        output_docx = get_next_filename()
        fill_template(TEMPLATE_PATH, output_docx, data)

        # 👇 اسم الملف الناتج
        out_name = os.path.basename(output_docx)

        # 👇 رابط التحميل
        file_url = f"https://car-report-sanaa.onrender.com/download/{out_name}"

        return {
            "status": "done",
            "file": file_url
        }

    except Exception as e:
        print("ERROR:", e)
        return {"error": "processing failed"}, 500
# 📁 إعداد الملفات

# 🔢 إنشاء اسم ملف
def get_next_filename(base_name="report", ext=".docx"):
    i = 1
    while True:
        filename = f"{base_name}_{i:03d}{ext}"
        path = os.path.join(OUTPUT_FOLDER, filename)
        if not os.path.exists(path):
            return path
        i += 1

# 📥 الصفحة الرئيسية (محمي)
@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            return "❌ لم يتم اختيار ملف"

        filename = secure_filename(file.filename)

        if not filename.lower().endswith(".pdf"):
            filename = "upload.pdf"

        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)

        if os.path.getsize(pdf_path) == 0:
            return "❌ الملف فارغ"

        try:
            text = extract_text(pdf_path)
            data = parse(text)

            output_docx = get_next_filename()
            fill_template(TEMPLATE_PATH, output_docx, data)

            filename = os.path.basename(output_docx)
            return render_template("index.html", file_ready=filename)

        except Exception as e:
            print("ERROR:", e)
            return "❌ فشل المعالجة"

    return render_template("index.html")

# 📤 تحميل الملف (محمي)
@app.route("/download/<filename>")
@login_required
def download_file(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)

# 🚀 تشغيل
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)