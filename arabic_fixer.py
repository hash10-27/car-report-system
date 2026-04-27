import arabic_reshaper

try:
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False


def normalize_arabic(text):
    try:
        reshaped = arabic_reshaper.reshape(text)
        if BIDI_AVAILABLE:
            return get_display(reshaped)
        return reshaped
    except:
        return text