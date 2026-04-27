# arabic_fixer.py

import arabic_reshaper
from bidi.algorithm import get_display


def normalize_arabic(text):
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text