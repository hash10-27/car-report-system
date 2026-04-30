import re

def clean_name(text):
    import re
    text = re.sub(r'[^؀-ۿ\s]', '', text)
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
    words = re.findall(r'[؀-ۿ]+', line)
    ignore = {"اسم", "العميل", "الفني"}
    words = [w for w in words if w not in ignore]
    return " ".join(words)

def extract_from_line(line, keywords):
    import re
    if ":" in line:
        value = line.split(":", 1)[1].strip()
    else:
        value = line
    value = re.sub(r'[؀-ۿ]+', '', value)
    value = re.sub(r'[:\-]', '', value)
    return value.strip()

import unicodedata

def normalize_line(line):
    line = unicodedata.normalize('NFKC', line)
    line = re.sub(r'[^\w؀-ۿ\s:.+-]', '', line)
    line = re.sub(r'\s+', ' ', line)
    return line.strip()

def extract_pattern(text, pattern):
    import re
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

def fix_reverse(text):
    if not text:
        return text
    return text[::-1]

def fix_vin(v):
    if not v:
        return v
    v = v.strip().replace(" ", "")
    if v[0].isdigit():
        return v[::-1]
    return v

def fix_engine(e):
    if not e:
        return e
    parts = e.split("+")
    parts = [p[::-1] for p in parts]
    return "+".join(parts[::-1])

def fix_mileage(m):
    if not m:
        return m
    m = m[::-1]
    m = m.lstrip("0")
    if m.isdigit():
        return m
    return m

def fix_dtc(code):
    code = code.replace(".", "")
    code = code[::-1]
    match = re.search(r'([PBCU][0-9A-Z]{4})', code)
    return match.group(1) if match else code

def extract_faults_raw(text):
    import re
    text = re.sub(r'[‎‏‪-‮]', '', text)
    lines = text.split("\n")
    start = False
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "غير طبيعي" in line:
            start = True
            result.append(line)
            continue
        if "على ما يرام" in line:
            break
        if not start:
            continue
        line = re.sub(r'(DTC|Present|الحالي|التاريخ)', '', line, flags=re.IGNORECASE)
        line = re.sub(r'^\d+\.', '', line).strip()
        if not line:
            continue
        result.append(line)
    return result

import re
def parse(text):
    lines = []
    for line in text.split("\n"):
        line = normalize_line(line)
        if any('؀' <= c <= 'ۿ' for c in line):
            line = line[::-1]
        lines.append(line)
    
    data = {"car_info": {"year": "", "make": "", "model": "", "vin": "", "engine": "", "mileage": ""},
            "customer_info": {"customer": "", "technician": "", "phone": ""},
            "meta": {"car_version": "", "app_version": "", "test_time": "", "sn": ""},
            "systems": {}, "systems_ok": [], "faults_raw": []}
    text_clean = re.sub(r'[‎‏‪-‮]', '', text)
    text_clean = re.sub(r'\s+', ' ', text_clean)
    car_ver = re.search(r'V\d+\.\d+', text_clean)
    app_ver = re.findall(r'V\d+\.\d+\.\d+', text_clean)
    if car_ver:
        data["meta"]["car_version"] = car_ver.group()
    if len(app_ver) > 0:
        data["meta"]["app_version"] = app_ver[-1]
    date_match = re.search(r'\d{2}-\d{2}-\d{4}', text_clean)
    time_match = re.search(r'\d{2}:\d{2}:\d{2}', text_clean)
    if date_match and time_match:
        data["meta"]["test_time"] = date_match.group() + " " + time_match.group()
    in_ok_section = False

    faults_raw = []
    capture = False
    current_title = ""
    for i, line in enumerate(lines):
        line = normalize_line(line)
        if not line:
            continue
        if "غير طبيعي" in line:
            capture = True
        if "على ما يرام" in line:
            capture = False
        if capture:
            faults_raw.append(line)
        systems = re.findall(r'(.*?)', line)
        for s in systems:
            if len(s) <= 5:
                if s not in data["systems_ok"]:
                    data["systems_ok"].append(s)
        if "رمز" in line and "خطأ" in line:
            in_dtc_section = True
            continue
        if "على ما يرام" in line:
            in_ok_section = True
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
                data["car_info"]["vin"] = fix_vin(vin.group())
        elif "حجمالمحرك" in clean:
            clean_engine = re.sub(r'[^\w\.\+\-\s]', '', line)
            parts = re.findall(r'[A-Z0-9\.\+\-]+', clean_engine)
            fixed_parts = []
            for p in parts:
                if re.search(r'[A-Z]', p):
                    fixed_parts.append(p[::-1])
                else:
                    fixed_parts.append(p)
            if fixed_parts:
                data["car_info"]["engine"] = " ".join(sorted(fixed_parts, key=lambda x: (not 'L' in x, len(x))))
        elif "عداد" in clean:
            numbers = re.findall(r'\d+', line)
            if numbers:
                value = max(numbers, key=len)
                data["car_info"]["mileage"] = value
        elif "اسمالعميل" in clean:
            data["customer_info"]["customer"] = extract_arabic_name(line)
        elif "اسمالفني" in clean:
            data["customer_info"]["technician"] = extract_arabic_name(line)
        elif "الهاتف" in clean:
            phone = re.search(r'\d{6,}', line)
            if phone:
                data["customer_info"]["phone"] = phone.group()
        elif "إصدار برنامج السيارة" in clean:
            data["meta"]["car_version"] = extract_from_line(line, ["إصدار برنامج السيارة"])
        elif "إصدار تطبيق التشخيص" in clean:
            data["meta"]["app_version"] = extract_from_line(line, ["إصدار تطبيق التشخيص"])
        elif "وقت الاختبار" in clean:
            data["meta"]["test_time"] = extract_from_line(line, ["وقت الاختبار"])
        elif "SN" in line and not data["meta"]["sn"]:
            sn = re.search(r'\d{8,}', line)
            if sn:
                data["meta"]["sn"] = sn.group()

        title_candidate = re.sub(r'^\d+\.\s*', '', line).strip()
        title_candidate = re.sub(r'^[^؀-ۿA-Za-z0-9]+', '', title_candidate).strip()

        if (
            re.match(r'^\d+\.', line)
            and re.search(r'[؀-ۿ]', title_candidate)
            and "غير طبيعي" not in title_candidate
        ):
            current_title = title_candidate
            if current_title not in data["systems"]:
                data["systems"][current_title] = []


        dtc_match = re.search(r'([0-9]+\.[0-9A-Z]{4}[PCBU])', line)
        if dtc_match:
            raw_code = dtc_match.group(1)
            code = fix_dtc(raw_code)
            if not code:
                continue
                
            parts = line.split(raw_code, 1)
            if len(parts) < 2:
                continue

            desc = parts[1].strip()
            desc = re.sub(r'(الحالي|التاريخ)', '', desc)
            desc = re.sub(r'[0-9]+.[0-9A-Z]{4}[PBCU]', '', desc)
            desc = desc.strip()

            if len(desc) < 3:
                continue

            if i + 1 < len(lines):
                next_line = normalize_line(lines[i + 1])
                if next_line and not re.search(
                    r'[PCBU][0-9A-Z]{4}', next_line
                ):
                    if not any(x in next_line for x in ["على ما يرام", "DTC", "الأنظمة"]):
                        desc += " " + next_line

            if any(x in desc for x in ["إخلاء", "المسؤولية", "هذا التقرير", "لا تتحمل", "أي مسؤولية", "LAUNCH", "بيانات", "service"]):
                continue
                
            if "dtc" not in data:
                data["dtc"] = []
            title_to_use = current_title.strip() if current_title else ""
            item = {"code": code, "desc": desc.strip(), "title": title_to_use}
            data["dtc"].append(item)
            if title_to_use:
                if title_to_use not in data["systems"]:
                    data["systems"][title_to_use] = []
                data["systems"][title_to_use].append(item)
        if in_ok_section:
            if re.search(r'إ.?خل.?اء|مسؤ.?ول|تقرير|بيانات', line):
                break
            if i > 0 and "على ما يرام" in lines[i-1]:
                pass
            clean_line = re.sub(r'^\d+\.', '', line).strip()
            if not clean_line:
                continue
            if "DTC" in line:
                continue
            added = False
            if re.match(r'^[A-Z0-9\s\.]+$', clean_line):
                if clean_line not in data["systems_ok"]:
                    data["systems_ok"].append(clean_line)
                added = True
            if added:
                continue
            if len(clean_line) > 100:
                continue
            if any(x in clean_line for x in ["هذا التقرير", "بيانات", "LAUNCH"]):
                continue
            if clean_line not in data["systems_ok"]:
                data["systems_ok"].append(clean_line)
    data["faults_raw"] = faults_raw
    return data
