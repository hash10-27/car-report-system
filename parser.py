import re
import unicodedata

# ================================
# 🔹 تنظيف
# ================================
def normalize_line(line):
    line = unicodedata.normalize('NFKC', line)
    line = re.sub(r'\s+', ' ', line)
    return line.strip()


# ================================
# 🔹 استخراج الأعطال RAW
# ================================
def extract_faults_raw(text):
    lines = text.split("\n")

    capture = False
    result = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if "غير طبيعي" in line:
            capture = True

        if "على ما يرام" in line:
            break

        if capture:
            result.append(line)

    return result


# ================================
# 🔥 Parser كامل
# ================================
def parse(text):

    lines = [normalize_line(l) for l in text.split("\n")]

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
        "systems_ok": [],
        "faults_raw": extract_faults_raw(text)
    }

    # ============================
    # 🚗 معلومات السيارة
    # ============================
    for line in lines:

        clean = line.replace(" ", "")

        # سنة
        if "السنة" in clean:
            y = re.search(r'\d{4}', line)
            if y:
                data["car_info"]["year"] = y.group()

        # الشركة
        elif "الصانع" in clean:
            m = re.search(r'[A-Z]+', line)
            if m:
                data["car_info"]["make"] = m.group()[::-1]

        # الموديل
        elif "الطراز" in clean:
            words = re.findall(r'[A-Za-z]+', line)
            if words:
                data["car_info"]["model"] = " ".join(words)[::-1]

        # VIN
        elif "تعريف" in clean:
            vin = re.search(r'[A-Z0-9]{17}', line)
            if vin:
                v = vin.group()
                data["car_info"]["vin"] = v[::-1] if v[0].isdigit() else v

        # المحرك
        elif "حجمالمحرك" in clean:
            parts = re.findall(r'[A-Z0-9\.\+]+', line)
            fixed = [p[::-1] if re.search(r'[A-Z]', p) else p for p in parts]
            data["car_info"]["engine"] = " ".join(fixed)

        # العداد
        elif "عداد" in clean:
            nums = re.findall(r'\d+', line)
            if nums:
                data["car_info"]["mileage"] = max(nums, key=len)

        # ============================
        # 👤 العميل
        # ============================
        elif "اسمالعميل" in clean:
            data["customer_info"]["customer"] = " ".join(
                re.findall(r'[\u0600-\u06FF]+', line)
            )

        elif "اسمالفني" in clean:
            data["customer_info"]["technician"] = " ".join(
                re.findall(r'[\u0600-\u06FF]+', line)
            )

        elif "الهاتف" in clean:
            p = re.search(r'\d{6,}', line)
            if p:
                data["customer_info"]["phone"] = p.group()

        # ============================
        # 🧠 Meta
        # ============================
        elif "SN" in line:
            sn = re.search(r'\d{6,}', line)
            if sn:
                data["meta"]["sn"] = sn.group()

        elif "V" in line:
            v = re.findall(r'V\d+\.\d+(\.\d+)?', line)
            if v:
                data["meta"]["app_version"] = v[-1]

        elif re.search(r'\d{2}-\d{2}-\d{4}', line):
            d = re.search(r'\d{2}-\d{2}-\d{4}', line)
            t = re.search(r'\d{2}:\d{2}:\d{2}', line)
            if d and t:
                data["meta"]["test_time"] = d.group() + " " + t.group()

        # ============================
        # ✅ الأنظمة السليمة
        # ============================
        if "على ما يرام" in line:
            idx = lines.index(line)

            for i in range(idx+1, min(idx+6, len(lines))):
                clean_line = re.sub(r'^\d+\.', '', lines[i]).strip()

                if not clean_line:
                    continue

                if any(x in clean_line for x in ["إخلاء", "التقرير", "بيانات"]):
                    break

                data["systems_ok"].append(clean_line)

    return data