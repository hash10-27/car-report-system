from extractor import extract_text
from cleaner import fix_arabic
from parser import parse
from writer import fill_template
from arabic_fixer import normalize_arabic

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import sys

# =========================
# الإعدادات
# =========================
TEMPLATE_PATH = "template.docx"


selected_file = None

def ar(text):
    return normalize_arabic(text)
# =========================
# اختيار الملف
# =========================
def choose_file():
    global selected_file
    file_path = filedialog.askopenfilename(
        filetypes=[("PDF Files", "*.pdf")]
    )

    if file_path:
        selected_file = file_path
        file_label.config(text=f"📄 {os.path.basename(file_path)}")

last_pdf = None
# =========================
# التحويل
# =========================
def process_file():
    global selected_file
    global last_pdf

    if not selected_file:
        messagebox.showwarning("تنبيه", "اختر ملف PDF أولاً")
        return

    output_docx = None
    output_pdf = None

    try:
        status_label.config(text=ar("⏳ جاري المعالجة..."))
        root.update()

        text = extract_text(selected_file)
        text = normalize_arabic(text)
        fixed_text = fix_arabic(text)
        data = parse(fixed_text)

        # 🔥 إنشاء أسماء ملفات
        output_docx = get_next_filename("report", ".docx")
        output_pdf = output_docx.replace(".docx", ".pdf")

        # 🔥 استخدم الأسماء الجديدة (مش OUTPUT_PATH)
        fill_template(TEMPLATE_PATH, output_docx, data)
        convert_to_pdf(output_docx, output_pdf)

        # 🔥 حفظ آخر ملف للطباعة
        last_pdf = output_pdf
        status_label.config(text=f"✅ تم الحفظ:\n{os.path.basename(output_pdf)}")

        status_label.config(text=ar("✅ تم إنشاء التقرير"))

    except Exception as e:
        messagebox.showerror("خطأ", str(e))
        status_label.config(text="❌ حدث خطأ")

def convert_to_pdf(docx_path, pdf_path):
    import sys
    import subprocess
    import os

    # 🪟 Windows (باستخدام Word)
    if sys.platform == "win32":
        import comtypes.client

        word = comtypes.client.CreateObject("Word.Application")
        doc = word.Documents.Open(os.path.abspath(docx_path))
        doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)
        doc.Close()
        word.Quit()

    # 🐧 Linux (LibreOffice)
    else:
        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            docx_path,
            "--outdir",
            os.path.dirname(pdf_path)
        ])

import os
def get_next_filename(base_name="report", ext=".docx"):
    i = 1
    while True:
        filename = f"{base_name}_{i:03d}{ext}"
        if not os.path.exists(filename):
            return filename
        i += 1
# =========================
# الطباعة
# =========================
def print_file():
    if not last_pdf or not os.path.exists(last_pdf):
        messagebox.showwarning("تنبيه", "قم بإنشاء التقرير أولاً")
        return

    try:
        # 🔥 الأفضل: فتح الملف بدل طباعة مباشرة
        subprocess.run(["xdg-open", last_pdf])
        status_label.config(text="📄 تم فتح الملف")

    except Exception as e:
        messagebox.showerror("خطأ", str(e))
# =========================
# الواجهة
# =========================
# =========================
# الواجهة (نسخة احترافية)
# =========================
root = tk.Tk()
root.title("نظام تحويل التقارير")

# 🔥 شاشة كاملة للتابلت
root.attributes("-fullscreen", True)
root.configure(bg="#1e1e2f")

FONT_TITLE = ("Arial", 26, "bold")
FONT_BTN = ("Arial", 18)
FONT_STATUS = ("Arial", 14)

# =========================
# عنوان
# =========================
title = tk.Label(
    root,
    text=ar("📊 نظام تحويل التقارير"),
    font=FONT_TITLE,
    fg="white",
    bg="#1e1e2f"
)
title.pack(pady=30)

# =========================
# اسم الملف
# =========================
file_label = tk.Label(
    root,
    text=ar("لم يتم اختيار ملف"),
    font=("Arial", 14),
    fg="#cccccc",
    bg="#1e1e2f"
)
file_label.pack(pady=10)

# =========================
# زر اختيار ملف
# =========================
btn_select = tk.Button(
    root,
    text=ar("📂 اختيار ملف PDF"),
    font=FONT_BTN,
    bg="#4CAF50",
    fg="white",
    width=25,
    height=2,
    command=choose_file
)
btn_select.pack(pady=15)

# =========================
# زر المعالجة
# =========================
btn_process = tk.Button(
    root,
    text=ar("⚙️ إنشاء التقرير"),
    font=FONT_BTN,
    bg="#2196F3",
    fg="white",
    width=25,
    height=2,
    command=process_file
)
btn_process.pack(pady=15)

# =========================
# زر الطباعة (أو فتح PDF)
# =========================
btn_print = tk.Button(
    root,
    text=ar("🖨️ عرض / طباعة"),
    font=FONT_BTN,
    bg="#FF9800",
    fg="white",
    width=25,
    height=2,
    command=print_file
)
btn_print.pack(pady=15)

# =========================
# الحالة
# =========================
status_label = tk.Label(
    root,
    text="",
    font=FONT_STATUS,
    fg="#00ffcc",
    bg="#1e1e2f"
)
status_label.pack(pady=30)

# =========================
# زر خروج (مهم للتابلت)
# =========================
def exit_app():
    root.destroy()

btn_exit = tk.Button(
    root,
    text=ar("❌ خروج"),
    font=("Arial", 14),
    bg="#e53935",
    fg="white",
    command=exit_app
)
btn_exit.pack(side="bottom", pady=20)

root.mainloop()