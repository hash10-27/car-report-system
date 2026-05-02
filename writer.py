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


def build_dtc_text(dtc_list):
    if not dtc_list:
        return "لا يوجد أعطال"
    lines = []
    for d in dtc_list:
        system = d.get('system') or d.get('title') or 'غير محدد'
        line = f"{system} | {d.get('code','')} | {d.get('desc','')}"
        lines.append(line)
    return "".join(lines)


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


def fill_dtc_table(doc, dtc_list):
    table = doc.tables[1]
    for d in dtc_list:
        row_cells = table.add_row().cells
        row_cells[0].text = d.get("system") or d.get("title") or "غير محدد"
        row_cells[1].text = d.get("code", "")
        row_cells[2].text = d.get("desc", "")


def format_systems(systems):
    if not systems:
        return "لا يوجد"
    return "".join(systems)


def fill_ok_systems_table(doc, systems_ok):
    table = doc.tables[2]
    for system in systems_ok:
        if any(x in system for x in ["إخلاء المسؤولية", "هذا التقرير", "بيانات", "LAUNCH"]):
            continue
        row = table.add_row().cells
        clean_name = re.sub(r'^\d+\.', '', system).strip()
        row[0].text = clean_name
        row[1].text = "✔"
        style_cell(row[0])
        style_cell(row[1], bold=True, color=RGBColor(0, 150, 0))
        for cell in row:
            center_cell(cell)


def extract_raw_dtc_block(text):
    lines = text.split("")
    capture = False
    result = []
    for line in lines:
        if "رمز خطأ النظام" in line:
            capture = True
            continue
        if "على ما يرام" in line:
            break
        if capture:
            result.append(line.strip())
    return "".join(result)

def fill_system_tables(doc, faults_raw):
    table = doc.tables[1]

    if isinstance(faults_raw, str):
        faults_raw = faults_raw.splitlines()

    def clean_line(s):
        return re.sub(r'^\s*\d+\.?\s*', '', s).strip()

    def has_dtc(line):
        return bool(
            re.search(r'\d+\.[0-9A-Z]{4}[PCBU]', line) or
            re.search(r'd+.d+[A-Z0-9]{4}[PCBU]', line)
        )

    def is_noise(s):
        s = clean_line(s)
        return (
            not s or
            s in ["LH", "HL", "المختلطة"] or
            "غير طبيعي" in s or
            s == "DTC" or
            s.startswith("DTC ") or
            s.startswith("Present") or
            s.startswith("الحالي") or
            s.startswith("التاريخ") or
            "رمز خطأ النظام" in s or
            s.startswith("النظام التالي")
        )

    def is_title_line(s):
        s = clean_line(s)
        if is_noise(s) or has_dtc(s):
            return False
        if len(s) < 3:
            return False
        if re.match(r'^[0-9A-Zs()/-+._]+$', s):
            return False
        return True

    current_title = ""

    for line in faults_raw:
        line = clean_line(line)
        if not line or is_noise(line):
            continue

        if not has_dtc(line) and is_title_line(line):
            current_title = line
            row = table.add_row().cells
            row[0].text = f"🔹 {current_title}"
            row[1].text = ""
            row[2].text = ""
            style_cell(row[0], bold=True, color=RGBColor(0, 102, 204))
            center_cell(row[0])
            continue

        if re.match(r'^(?DTCs*(?d+)?$', line.replace(' ', '')):
            continue

        if has_dtc(line):
            parts = re.split(r'(?=d+.[0-9A-Z]{4}[PCBU]|d+.d+[A-Z0-9]{4}[PCBU])', line)

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                m = re.search(r'(d+.[0-9A-Z]{4}[PCBU]|d+.d+[A-Z0-9]{4}[PCBU])', part)
                if not m:
                    continue

                code = fix_dtc(m.group(1))
                if not code:
                    continue

                desc = part[m.end():].strip()
                desc = re.sub(r'^(الحالي|التاريخ|Present)s*', '', desc)
                desc = re.sub(r'\s+', ' ', desc).strip()

                if len(desc) < 2:
                    continue

                row = table.add_row().cells
                row[0].text = current_title or "غير محدد"
                row[1].text = code
                row[2].text = desc

                style_cell(row[0], bold=True)
                center_cell(row[0])
                center_cell(row[1])
                center_cell(row[2])

def fill_template(template_path, output_path, data):
    doc = Document(template_path)
    fill_ok_systems_table(doc, data["systems_ok"])

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
        "{systems}": "".join(f"{d['code']} {d['desc']}" for d in data.get("dtc", []))
    }

    for key, value in replacements.items():
        replace_all(doc, key, str(value))

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
