from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import RGBColor, Pt
import re


def replace_all(doc, key, value):
    for p in doc.paragraphs:
        if key in p.text:
            p.text = p.text.replace(key, value)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if key in cell.text:
                    cell.text = cell.text.replace(key, value)


def center_cell(cell):
    for paragraph in cell.paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    tc = cell._element
    tcPr = tc.get_or_add_tcPr()
    vAlign = OxmlElement('w:vAlign')
    vAlign.set(qn('w:val'), 'center')
    tcPr.append(vAlign)


def style_cell(cell, bold=False, color=None):
    for p in cell.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.bold = bold
            run.font.size = Pt(11)
            if color:
                run.font.color.rgb = color


def fix_dtc(code):
    if not code:
        return ""
    code = code.strip()
    code = code.replace(" ", "")
    code = re.sub(r'[^0-9A-Z.]', '', code)
    return code.replace(".", "")


def is_noise_line(line):
    s = line.strip()
    return (
        not s
        or s in {"LH", "HL", "المختلطة"}
        or s == "DTC"
        or re.fullmatch(r"DTCs*d+", s)
        or s.startswith("DTC ")
        or s.startswith("Present")
        or s.startswith("الحالي")
        or s.startswith("التاريخ")
        or "غير طبيعي" in s
        or "رمز خطأ النظام" in s
        or s.startswith("النظام التالي")
        or "Worker exiting" in s
        or "INFO" in s
    )


def extract_code_desc(line):
    s = line.strip()
    s = re.sub(r'^(الحالي|التاريخ|Present)s*', '', s).strip()

    m = re.search(r'(d+.[0-9A-Z]{4}[PCBU]|d+.d+[A-Z0-9]{4}[PCBU])', s)
    if not m:
        return None, None

    code = fix_dtc(m.group(1))
    desc = s[m.end():].strip()
    desc = re.sub(r'^s*[:-–]?s*', '', desc)
    desc = re.sub(r's+', ' ', desc).strip()
    return code, desc


def is_title_candidate(line):
    s = line.strip()
    if is_noise_line(s):
        return False
    if extract_code_desc(s)[0]:
        return False
    if len(s) < 3:
        return False
    if re.search(r'd+.[0-9A-Z]{4}[PCBU]', s) or re.search(r'd+.d+[A-Z0-9]{4}[PCBU]', s):
        return False
    return True


def fill_system_tables(doc, faults_raw):
    table = doc.tables[1]

    if isinstance(faults_raw, str):
        faults_raw = faults_raw.splitlines()

    current_title = ""
    i = 0

    while i < len(faults_raw):
        line = faults_raw[i].strip()

        if not line or is_noise_line(line):
            i += 1
            continue

        if line.startswith("DTC") and len(line.split()) <= 2:
            i += 1
            continue

        code, desc = extract_code_desc(line)

        if code:
            full_desc_parts = []
            if desc:
                full_desc_parts.append(desc)

            j = i + 1
            while j < len(faults_raw):
                nxt = faults_raw[j].strip()

                if not nxt:
                    j += 1
                    continue

                if is_noise_line(nxt):
                    j += 1
                    continue

                if is_title_candidate(nxt):
                    break

                next_code, next_desc = extract_code_desc(nxt)
                if next_code:
                    break

                cleaned = re.sub(r'^s*d+.?s*', '', nxt).strip()
                cleaned = re.sub(r's+', ' ', cleaned)

                if cleaned:
                    full_desc_parts.append(cleaned)

                j += 1

            full_desc = " ".join(full_desc_parts)
            full_desc = re.sub(r's+', ' ', full_desc).strip()

            row = table.add_row().cells
            row[0].text = current_title or "غير محدد"
            row[1].text = code
            row[2].text = full_desc

            style_cell(row[0], bold=True)
            center_cell(row[0])
            center_cell(row[1])
            center_cell(row[2])

            i = j
            continue

        if is_title_candidate(line):
            current_title = re.sub(r's+', ' ', line).strip()

            row = table.add_row().cells
            row[0].text = f"🔹 {current_title}"
            row[1].text = ""
            row[2].text = ""

            style_cell(row[0], bold=True, color=RGBColor(0, 102, 204))
            center_cell(row[0])

            i += 1
            continue

        i += 1


def fill_ok_systems_table(doc, systems_ok):
    table = doc.tables[-1]

    for system in systems_ok:
        if any(x in system for x in [
            "إخلاء المسؤولية",
            "هذا التقرير",
            "بيانات",
            "LAUNCH"
        ]):
            continue

        row = table.add_row().cells
        clean_name = re.sub(r'^d+.', '', system).strip()
        row[0].text = clean_name
        row[1].text = "✔"

        style_cell(row[0])
        style_cell(row[1], bold=True, color=RGBColor(0, 150, 0))

        for cell in row:
            center_cell(cell)


def fill_template(template_path, output_path, data):
    doc = Document(template_path)

    replacements = {
        "{year}": data["car_info"]["year"],
        "{make}": data["car_info"]["make"],
        "{model}": data["car_info"]["model"],
        "{vin}": data["car_info"]["vin"],
        "{engine}": data["car_info"]["engine"],
        "{mileage}": data["car_info"]["mileage"],
        "{customer}": data["customer_info"]["customer"],
        "{technician}": data["customer_info"]["technician"],
        "{phone}": data["customer_info"]["phone"],
        "{car_version}": data["meta"]["car_version"],
        "{app_version}": data["meta"]["app_version"],
        "{test_time}": data["meta"]["test_time"],
        "{sn}": data["meta"]["sn"],
        "{systems_ok}": "".join(data["systems_ok"]),
        "{systems}": "".join(
            f"{d.get('code','')} {d.get('desc','')}" for d in data.get("dtc", [])
        )
    }

    for key, value in replacements.items():
        replace_all(doc, key, str(value))

    fill_ok_systems_table(doc, data["systems_ok"])
    fill_system_tables(doc, data["faults_raw"])

    table = doc.tables[0]
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i == 1:
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in p.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(0, 102, 204)
            else:
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in p.runs:
                        run.bold = True

            center_cell(cell)

    doc.save(output_path)