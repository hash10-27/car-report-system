
import re


def normalize_line(line):
    line = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', line)
    line = re.sub(r'\s+', ' ', line)
    return line.strip()


def fix_dtc(code):
    if not code:
        return ""
    code = code.strip().replace(' ', '')
    code = code.replace('.', '')
    return code


def is_noise(s):
    s = normalize_line(s)
    return (
        not s or
        s in {'LH', 'HL', 'المختلطة'} or
        s.startswith('Worker exiting') or
        s.startswith('==>') or
        'INFO' in s or
        s == 'DTC' or
        re.fullmatch(r'DTC\s*\(?\d+\)?', s) or
        s.startswith('Present') or
        s.startswith('الحالي') or
        s.startswith('التاريخ') or
        'غير طبيعي' in s or
        'على ما يرام' in s or
        'رمز خطأ النظام' in s or
        'إخلاء المسؤولية' in s or
        'هذا التقرير' in s or
        'LAUNCH' in s
    )


def extract_code_desc(line):
    s = normalize_line(line)
    s = re.sub(r'^(Present|الحالي|التاريخ)\s*', '', s)
    m = re.search(r'(\d+\.\d+[A-Z0-9]{3,4}[PCBU]|\d+\.[0-9A-Z]{4}[PCBU])', s)
    if not m:
        return None, None
    code = fix_dtc(m.group(1))
    desc = s[m.end():].strip()
    desc = re.sub(r'^[\s:ـ\-–]+', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    return code, desc


def looks_like_title(s):
    s = normalize_line(s)
    if is_noise(s):
        return False
    if extract_code_desc(s)[0]:
        return False
    if re.fullmatch(r'DTC\s*\(?\d+\)?', s):
        return False
    if len(s) < 3:
        return False
    if re.search(r'\d+\.\d+[A-Z0-9]{3,4}[PCBU]', s) or re.search(r'\d+\.[0-9A-Z]{4}[PCBU]', s):
        return False
    return True


def extract_faults_raw(text):
    text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)
    lines = [normalize_line(x) for x in text.splitlines()]
    result = []
    capture = False
    for line in lines:
        if not line:
            continue
        if 'النظام التالي غير طبيعي' in line or 'قبل الإصلاح رمز خطأ النظام' in line or 'قبل الإصلاح' == line:
            capture = True
            continue
        if 'الأنظمة التالية على ما يرام' in line or 'على ما يرام' in line:
            break
        if capture:
            result.append(line)
    return result


def parse(text):
    data = {
        'car_info': {'year': '', 'make': '', 'model': '', 'vin': '', 'engine': '', 'mileage': ''},
        'customer_info': {'customer': '', 'technician': '', 'phone': ''},
        'meta': {'car_version': '', 'app_version': '', 'test_time': '', 'sn': ''},
        'systems': {},
        'systems_ok': [],
        'faults_raw': [],
        'dtc': []
    }

    text_clean = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)
    text_clean = re.sub(r'\s+', ' ', text_clean)

    m = re.search(r'\b(20\d{2})\b', text_clean)
    if m:
        data['car_info']['year'] = m.group(1)

    if 'KIA' in text_clean:
        data['car_info']['make'] = 'KIA'

    vin = re.search(r'\bKNADE\d{12}\b', text_clean)
    if vin:
        data['car_info']['vin'] = vin.group(0)

    engine = re.search(r'\bDOHC\s*1\.6\s*G\b', text_clean)
    if engine:
        data['car_info']['engine'] = engine.group(0)

    car_ver = re.search(r'V\d+\.\d+', text_clean)
    if car_ver:
        data['meta']['car_version'] = car_ver.group(0)

    app_ver = re.search(r'V\d+\.\d+\.\d+', text_clean)
    if app_ver:
        data['meta']['app_version'] = app_ver.group(0)

    tm = re.search(r'\d{2}-\d{2}-\d{4}:\s*\d{2}:\d{2}:\d{2}', text_clean)
    if tm:
        data['meta']['test_time'] = tm.group(0)

    sn = re.search(r'\b\d{9,}\b', text_clean)
    if sn:
        data['meta']['sn'] = sn.group(0)

    cust = re.search(r'اسم العميل\s*([^\n]+)', text)
    if cust:
        data['customer_info']['customer'] = normalize_line(cust.group(1))
    tech = re.search(r'اسم الفني[:\s]*([^\n]+)', text)
    if tech:
        data['customer_info']['technician'] = normalize_line(tech.group(1))
    phone = re.search(r'الهاتف[:\s]*([0-9]{6,})', text)
    if phone:
        data['customer_info']['phone'] = phone.group(1)

    lines = [normalize_line(x) for x in text.splitlines()]
    for i, line in enumerate(lines):
        if 'الأنظمة التالية على ما يرام' in line:
            for nxt in lines[i+1:i+6]:
                if nxt and not is_noise(nxt):
                    cleaned = re.sub(r'^\.?\d+\s*', '', nxt)
                    cleaned = cleaned.strip(' .:')
                    if cleaned and cleaned not in data['systems_ok']:
                        data['systems_ok'].append(cleaned)

    faults = extract_faults_raw(text)
    data['faults_raw'] = faults

    current_title = ''
    i = 0
    while i < len(faults):
        line = faults[i]
        if is_noise(line):
            i += 1
            continue

        if looks_like_title(line):
            current_title = line
            i += 1
            continue

        code, desc = extract_code_desc(line)
        if code:
            desc_parts = []
            if desc:
                desc_parts.append(desc)
            j = i + 1
            while j < len(faults):
                nxt = faults[j]
                if is_noise(nxt):
                    j += 1
                    continue
                if looks_like_title(nxt):
                    break
                ncode, ndesc = extract_code_desc(nxt)
                if ncode:
                    break
                cleaned = normalize_line(nxt)
                cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
                cleaned = re.sub(r'^(Present|الحالي|التاريخ)\s*', '', cleaned)
                if cleaned:
                    desc_parts.append(cleaned)
                j += 1
            full_desc = re.sub(r'\s+', ' ', ' '.join(desc_parts)).strip()
            if full_desc:
                data['dtc'].append({'system': current_title or 'غير محدد', 'code': code, 'desc': full_desc})
                data['systems'].setdefault(current_title or 'غير محدد', []).append({'code': code, 'desc': full_desc})
            i = j
            continue
        i += 1

    return data
