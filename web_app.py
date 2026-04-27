from flask import Flask, render_template, request, send_file
import os

from extractor import extract_text
from cleaner import fix_arabic
from parser import parse
from writer import fill_template
from arabic_fixer import normalize_arabic

app = Flask(__name__)

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
        file = request.files["file"]

        if file:
            pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(pdf_path)

            # 🔥 نفس منطقك بدون تغيير
            text = extract_text(pdf_path)
            text = normalize_arabic(text)
            fixed_text = fix_arabic(text)
            data = parse(fixed_text)

            output_docx = get_next_filename()
            fill_template(TEMPLATE_PATH, output_docx, data)

            filename = os.path.basename(output_docx)
            return render_template("index.html", file_ready=filename)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)