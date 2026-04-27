import re

def is_arabic(char):
    return '\u0600' <= char <= '\u06FF'


def fix_word(word):
    # 🔹 نفصل الحروف عن الرموز
    parts = re.findall(r'[\u0600-\u06FF]+|[A-Za-z0-9.]+|[^A-Za-z0-9\u0600-\u06FF]+', word)

    fixed_parts = []

    for part in parts:
        if all(is_arabic(c) for c in part):
            fixed_parts.append(part[::-1])  # نعكس العربي فقط
        else:
            fixed_parts.append(part)  # نخلي الباقي كما هو

    return "".join(fixed_parts)


def fix_arabic(text):
    fixed_lines = []

    for line in text.split("\n"):
        words = line.split()
        fixed_words = [fix_word(word) for word in words]
        fixed_lines.append(" ".join(fixed_words))

    return "\n".join(fixed_lines)