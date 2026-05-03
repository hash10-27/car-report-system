from flask import Flask, render_template, request, send_file
import os

from extractor import extract_text
#from cleaner import fix_arabic
from parser import parse
from writer import fill_template
#from arabic_fixer import normalize_arabic

def fix_full_text(text):
    lines = text.split("\n")
    fixed_lines = []

   
    return "\n".join(fixed_lines)

app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

TEMPLATE_PATH = "template.docx"


def get_next_filename(base_name="report", ext=".docx"):
    i = 1
    while True:
        filename = f"{base_name}_{i:03d}{ext}"
        path = os.path.join(OUTPUT_FOLDER, filename)
        if not os.path.exists(path):
            return path
        i += 1

@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            return "❌ لم يتم اختيار ملف"

        from werkzeug.utils import secure_filename

        filename = secure_filename(file.filename)

        # إذا الاسم غريب من التابلت
        if not filename.lower().endswith(".pdf"):
            filename = "upload.pdf"

        pdf_path = os.path.join(UPLOAD_FOLDER, filename)

        # ✅ حفظ مرة واحدة فقط
        file.save(pdf_path)

        # ✅ تحقق من الحجم
        size = os.path.getsize(pdf_path)
        print("FILE SIZE:", size)

        if size == 0:
            return "❌ الملف فارغ (فشل الرفع من التابلت)"

        try:
            # 🔥 استخراج النص
            text = extract_text(pdf_path)

            # 🔥 تحليل
            data = parse(text)

            # 🔥 إنشاء التقرير
            output_docx = get_next_filename()
            fill_template(TEMPLATE_PATH, output_docx, data)

            filename = os.path.basename(output_docx)
            return render_template("index.html", file_ready=filename)

        except Exception as e:
            print("ERROR:", e)
            return "❌ فشل المعالجة (راجع اللوق)"

    return render_template("index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)