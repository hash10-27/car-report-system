# arabic_fixer.py

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def normalize_arabic(text):
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)

except ImportError:
    # 🔥 fallback إذا المكتبات غير موجودة (مثل Render)
    def normalize_arabic(text):
        return text