import re


# ================================
# 🔹 أدوات مساعدة
# ================================

def clean_name(text):
    import re
    text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
    words = text.split()
    return " ".join(words[::-1])

def fix_arabic_order(text):
    words = text.split()

    return " ".join(words)

def fix_engine_format(text):
    parts = text.split()
    parts.sort(key=lambda x: any(c.isdigit() for c in x), reverse=True)
    return " ".join(parts)

def extract_arabic_name(line):
    import re

    words = re.findall(r'[\u0600-\u06FF]+', line)

    # حذف الكلمات العامة
    ignore = {"اسم", "العميل", "الفني"}
    words = [w for w in words if w not in ignore]

    return " ".join(words)

def extract_from_line(line, keywords):
    import re

    # استخراج ما بعد :
    if ":" in line:
        value = line.split(":", 1)[1].strip()
    else:
        value = line

    # 🔥 إزالة الكلمات العربية
    value = re.sub(r'[\u0600-\u06FF]+', '', value)

    # إزالة رموز غير مفيدة
    value = re.sub(r'[:\-]', '', value)

    return value.strip()

import unicodedata

def normalize_line(line):
    # 🔥 تحويل Unicode إلى الشكل الطبيعي
    line = unicodedata.normalize('NFKC', line)

    # إزالة الرموز الغريبة
    line = re.sub(r'[^\w\u0600-\u06FF\s:.+-]', '', line)

    # توحيد المسافات
    line = re.sub(r'\s+', ' ', line)

    return line.strip()
def extract_pattern(text, pattern):
    import re
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

# ================================
# 🔹 أدوات مساعدة
# ================================

def fix_reverse(text):
    if not text:
        return text
    return text[::-1]

def fix_vin_numbers(v):
    if not v:
        return v

    v = v.strip().replace(" ", "")

    # استخراج الأرقام فقط
    digits = [c for c in v if c.isdigit()]
    digits.reverse()

    result = []
    digit_index = 0

    for c in v:
        if c.isdigit():
            result.append(digits[digit_index])
            digit_index += 1
        else:
            result.append(c)

    return "".join(result)
def fix_engine(e):
    if not e:
        return e
    
    # اقسم على +
    parts = e.split("+")
    
    # اعكس كل جزء
    parts = [p[::-1] for p in parts]
    
    # ارجع ترتيبها الصحيح
    return "+".join(parts[::-1])

def fix_mileage(m):
    if not m:
        return m

    m = m[::-1]  # عكس

    # إزالة الأصفار الزائدة من البداية
    m = m.lstrip("0")

    # إذا كان كله أرقام
    if m.isdigit():
        return m

    return m

# ================================
# 🔥 الدالة الرئيسية
# ================================
def parse(text):
    
    lines = []
    for line in text.split("\n"):
        line = normalize_line(line)

        # قلب مرة واحدة فقط
        if any('\u0600' <= c <= '\u06FF' for c in line):
            line = line[::-1]

        lines.append(line)

    # 🔥 إصلاح النص المقلوب (مهم جداً)

    import re

    data = {
        "car_info": {
            "year": "",
            "make": "",
            "model": "",
            "vin": "",
            "engine": "",
            "mileage": ""
        },
        "customer_info": {
            "customer": "",
            "technician": "",
            "phone": ""
        },
        "meta": {
            "car_version": "",
            "app_version": "",
            "test_time": "",
            "sn": ""
        },
        "systems": {},
        "systems_ok": []
    }

    # ====================================
    # 🔥 استخراج مباشر من النص (مهم)
    # ====================================

    import re

    # 🔥 تنظيف النص بالكامل من رموز OCR المخفية
    text_clean = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)

    # توحيد المسافات
    text_clean = re.sub(r'\s+', ' ', text_clean)

    car_ver = re.search(r'V\d+\.\d+', text_clean)
    app_ver = re.findall(r'V\d+\.\d+\.\d+', text_clean)

    if car_ver:
        data["meta"]["car_version"] = car_ver.group()

    if len(app_ver) > 0:
        data["meta"]["app_version"] = app_ver[-1]

    # 🔥 استخراج التاريخ والوقت بشكل منفصل
    date_match = re.search(r'\d{2}-\d{2}-\d{4}', text_clean)
    time_match = re.search(r'\d{2}:\d{2}:\d{2}', text_clean)

    if date_match and time_match:
        data["meta"]["test_time"] = date_match.group() + " " + time_match.group()

    # ====================================
    # 🔍 تحليل سطر بسطر
    # ====================================
    in_ok_section = False
    current_system = None
    in_dtc_section = False

    for i, line in enumerate(lines):
        line = normalize_line(line)
        # 🔥 قلب السطر إذا عربي
        lines = text.split("\n")

        # 🔥 إصلاح الأرقام (ترجع 4102 → 2014)
        import re
        numbers = re.findall(r'\d+', line)
        for num in numbers:
            line = line.replace(num, num[::-1])

        if not line:
            continue

        # 🔥 استخراج الأنظمة من الأقواس
        systems = re.findall(r'\((.*?)\)', line)

        for s in systems:
            if len(s) <= 5:
                if s not in data["systems_ok"]:
                    data["systems_ok"].append(s)

        # 🔥 بداية قسم الأعطال
        if "رمز" in line and "خطأ" in line:
            in_dtc_section = True
            continue

        if "على ما يرام" in line:
            in_ok_section = True
             # 🔥 أضف هذا مباشرة هنا
            if i + 1 < len(lines):
                next_line = normalize_line(lines[i + 1])
                if next_line:
                    clean_next = re.sub(r'^\d+\.', '', next_line).strip()
                    data["systems_ok"].append(clean_next)

            if i + 2 < len(lines):
                next_line2 = normalize_line(lines[i + 2])
                if next_line2:
                    clean_next2 = re.sub(r'^\d+\.', '', next_line2).strip()
                    data["systems_ok"].append(clean_next2)

            continue

        clean = fix_arabic_order(line)
        clean = clean.replace(" ", "")
         
        # 🚗 السيارة
        if "السنة" in clean:
            year = re.search(r'\d{4}', line)
            if year:
                data["car_info"]["year"] = year.group()

        elif "الصانع" in clean:
            make = re.search(r'[A-Z]+', line)
            if make:
                data["car_info"]["make"] = fix_reverse(make.group())

        elif "الطراز" in clean:
            words = re.findall(r'[A-Za-z]+', line)
            if words:
                model = " ".join(words)
                data["car_info"]["model"] = fix_reverse(model)

        elif "تعريف" in clean:
            vin = re.search(r'[A-Z0-9]{17}', line)
            if vin:
                data["car_info"]["vin"] = fix_vin_numbers(vin.group())

        elif "حجمالمحرك" in clean:

            clean_engine = re.sub(r'[^\w\.\+\-\s]', '', line)

            parts = re.findall(r'[A-Z0-9\.\+\-]+', clean_engine)

            fixed_parts = []

            for p in parts:
                # إذا فيه حروف → غالباً معكوس → نقلبه
                if re.search(r'[A-Z]', p):
                    fixed_parts.append(p[::-1])
                else:
                    fixed_parts.append(p)

            if fixed_parts:
                data["car_info"]["engine"] = " ".join(sorted(fixed_parts, key=lambda x: (not 'L' in x, len(x))))

        elif "عداد" in clean:

            numbers = re.findall(r'\d+', line)

            if numbers:
                # نأخذ أطول رقم (غالباً هو الصحيح)
                value = max(numbers, key=len)

                data["car_info"]["mileage"] = value
        # 👤 العميل
        elif "اسمالعميل" in clean:
            data["customer_info"]["customer"] = extract_arabic_name(line)

        elif "اسمالفني" in clean:
            data["customer_info"]["technician"] = extract_arabic_name(line)

        elif "الهاتف" in clean:
            phone = re.search(r'\d{6,}', line)
            if phone:
                data["customer_info"]["phone"] = phone.group()

        # ================================
        # ⚙️ بيانات إضافية
        # ================================
        elif "إصدار برنامج السيارة" in clean:
            data["meta"]["car_version"] = extract_from_line(line, ["إصدار برنامج السيارة"])

        elif "إصدار تطبيق التشخيص" in clean:
            data["meta"]["app_version"] = extract_from_line(line, ["إصدار تطبيق التشخيص"])

        elif "وقت الاختبار" in clean:
            data["meta"]["test_time"] = extract_from_line(line, ["وقت الاختبار"])

        elif "SN" in clean:
            data["meta"]["sn"] = extract_from_line(line, ["SN"])

        # 🔥 اكتشاف اسم النظام من السطر
        system_line = re.search(r'(HC|ABS|VSC|TRAC|SRS|CM)', line)

        clean_line = line.replace(" ", "")

        # 🔥 اكتشاف النظام بشكل قوي
        if "HC" in clean_line:
            current_system = "HC"

        elif "ABS" in clean_line:
            current_system = "ABS / VSC / TRAC"

        elif "VSC" in clean_line:
            current_system = "VSC"

        elif "TRAC" in clean_line:
            current_system = "TRAC"

        elif "SRS" in clean_line:
            current_system = "SRS"

        elif "CM" in clean_line:
            current_system = "CM"

        # ================================
        # 🔥 الأعطال (بدون section)
        # ================================
        dtc_match = re.search(r'([PBCU][0-9A-Z]{4}(?:\.\d+)?)', line)

        if dtc_match:
            code = dtc_match.group(1)
            desc = line.split(code, 1)[-1].strip()
            if not re.search(r'(الحالي|التاريخ|DTC)', line):
                continue

                # 🔥 الفلتر هنا (داخل الشرط)
            if "المحرك" in desc or "حجم" in desc or len(desc) < 3:
                continue

            # ❌ تجاهل إذا لم يتم تحديد النظام
            # إذا ما تم تحديد النظام → نحدد من الكود
            if not current_system:
                if code.startswith("P"):
                    current_system = "HC"
                elif code.startswith("C"):
                    current_system = "ABS / VSC / TRAC"
                elif code.startswith("B"):
                    current_system = "SRS"
                elif code.startswith("U"):
                    current_system = "NETWORK"
                else:
                    current_system = "OTHER"

            # دمج السطر التالي للوصف
            if i + 1 < len(lines):
                next_line = normalize_line(lines[i + 1])

                # 🔥 شروط صارمة
                if next_line and not re.search(r'[PBCU]\d{4}', next_line):

                    # ❌ لا تدمج إذا بداية قسم جديد
                    if any(x in next_line for x in [
                        "الأنظمة التالية",
                        "على ما يرام",
                        "النظام التالي",
                        "DTC",
                        "قبل الإصلاح"
                    ]):
                        pass
                    else:
                        desc += " " + next_line

            # 🔥 تحديد النظام (مرة واحدة فقط)
            # 🔥 الأولوية للنظام المكتشف من النص
            # 🔥 استخدم النظام الحالي أولاً
            system = current_system

            # إذا غير موجود → fallback
            if not system:
                if code.startswith("P") or code.startswith("U"):
                    system = "HC"
                elif code.startswith("C"):
                    system = "ABS"
                elif code.startswith("B"):
                    system = "CM" if code.startswith("B150") else "SRS"
                else:
                    system = "OTHER"

            # إنشاء القسم إذا غير موجود
            if system not in data["systems"]:
                data["systems"][system] = []

            # اختصار الوصف
            short_desc = desc
            
            # إضافة العطل
            data["systems"][system].append({
                "system": system,
                "code": code,
                "desc": short_desc
            })


        # ================================
        # ✅ الأنظمة السليمة
        # ================================
        if in_ok_section:
            print("OK SECTION >>>", line)

            # 🔥 إذا هذا أول سطر بعد العنوان لا تتجاهله
            if "على ما يرام" in lines[i-1]:
                pass

            print("RAW LINE >>>", repr(line))  # 👈 هنا

            # وقف عند نهاية التقرير
            if "إخلاء المسؤولية" in line:
                break

            # تنظيف
            clean_line = re.sub(r'^\d+\.', '', line).strip()

            print("CLEAN LINE >>>", repr(clean_line))  # 👈 

            # ❌ تجاهل السطور الفارغة
            if not clean_line:
                continue

            # ✅ اسم نظام حتى لو قصير (مثل EOBD)
            if re.match(r'^[A-Z0-9\s\.]+$', clean_line):
                data["systems_ok"].append(clean_line)
                continue

            # ❌ تجاهل الجمل الطويلة (ليست أنظمة)
            # ❌ تجاهل فقط الجمل الطويلة جداً (رفع الحد)
            if len(clean_line) > 100:
                continue

            # ❌ تجاهل النصوص التوضيحية
            if any(x in clean_line for x in [
                "هذا التقرير",
                "بيانات",
                "LAUNCH"
            ]):
                continue

            # 🔥 أضف مباشرة بدون شروط قاسية
            data["systems_ok"].append(clean_line)

        print("FINAL DATA >>>", data)

    return data