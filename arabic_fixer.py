import arabic_reshaper

def normalize_arabic(text):
    try:
        return arabic_reshaper.reshape(text)
    except:
        return text