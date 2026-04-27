try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def normalize_arabic(text):
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)

except:
    def normalize_arabic(text):
        return text