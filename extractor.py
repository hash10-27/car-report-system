import pdfplumber
from pdf2image import convert_from_path
import pytesseract


def extract_text(pdf_path):
    text = ""

    # ✅ محاولة قراءة النص مباشرة (أفضل شيء)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print("PDF read error:", e)

    # 🔥 إذا النص ضعيف → استخدم OCR
    if len(text.strip()) < 100:
        print("⚠️ استخدام OCR...")
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img, lang="eng+ara")

    return text