
import re
import unicodedata
from datetime import datetime


MAX_REASONABLE_AMOUNT = 5_000_000.0


def clean_text(text: str) -> str:
    replacements = {
        "\uf8ff": "נ",
        "\ue09b": "",
        "״": '"',
        "“": '"',
        "”": '"',
    }
    out = []
    for char in text:
        if char in replacements:
            out.append(replacements[char])
        elif char in "\n\t" or unicodedata.category(char) != "Cf":
            out.append(char)

    result = "".join(out)
    result = result.replace("סה ״כ", 'סה"כ').replace('סה "כ', 'סה"כ')
    result = result.replace("מע ״מ", 'מע"מ').replace('מע "מ', 'מע"מ')
    return result


def lines(text: str) -> list[str]:
    return [
        re.sub(r"[ \t]+", " ", row).strip()
        for row in clean_text(text).splitlines()
        if row.strip()
    ]


def amount(value):
    if value is None:
        return None

    cleaned = (
        str(value)
        .replace(",", "")
        .replace("₪", "")
        .replace('ש"ח', "")
        .replace("שח", "")
        .replace("יח'", "")
        .strip()
    )

    try:
        number = float(cleaned)
    except ValueError:
        return None

    if abs(number) > MAX_REASONABLE_AMOUNT:
        return None

    return number


def normalize_date(raw: str) -> str:
    if not raw:
        return ""

    for fmt in (
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
        "%d\\%m\\%Y",
    ):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue

    return ""


def first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip() if match.lastindex else match.group(0).strip()
    return ""


def value_before_label(rows: list[str], labels: list[str]):
    number_pattern = r"-?\d{1,3}(?:,\d{3})*(?:\.\d{2})|-?\d+(?:\.\d+)?"

    for row in rows:
        if not any(label in row for label in labels):
            continue

        values = [
            amount(value)
            for value in re.findall(number_pattern, row)
        ]
        values = [value for value in values if value is not None]

        if values:
            return values[0]

    return None


def vat_value(rows: list[str]):
    """Read the VAT amount without matching subtotal labels such as 'before VAT'."""
    for row in rows:
        if 'מע"מ' not in row:
            continue
        if any(phrase in row for phrase in ('לפני מע"מ', 'כולל מע"מ', 'חייב מע"מ')):
            continue
        values = re.findall(r"-?\d{1,3}(?:,\d{3})*(?:\.\d{2})", row)
        if values:
            return amount(values[0])
    return None


def classify_document(text: str) -> str:
    joined = "\n".join(lines(text))

    if "ריכוז חשבון" in joined or "סיכום חשבון לחודש" in joined:
        return "ריכוז חשבון"
    if "חשבונית זיכוי" in joined or re.search(r"\bזיכוי\b", joined):
        return "חשבונית זיכוי"
    if "יתרת איסופים לתשלום" in joined:
        return "דרישת תשלום"
    if "תעודת משלוח" in joined and "חשבונית מס" not in joined:
        return "תעודת משלוח"
    if "חשבונית מס/קבלה" in joined or "חשבונית מס קבלה" in joined:
        return "חשבונית מס/קבלה"
    if "קבלה מספר" in joined and "חשבונית מס" not in joined:
        return "קבלה"
    if "חשבונית מס" in joined:
        return "חשבונית מס"

    return "אחר"


def identify_supplier(joined: str) -> tuple[str, str]:
    rules = [
        ("עין גב אחזקות", 'עין גב אחזקות - אגודה שיתופית חקלאית', "557030772"),
        ("קבוצת עדן דוד", 'קבוצת עדן דוד בע"מ', "516308996"),
        ("בבאיי משה", "בבאיי משה", "074677089"),
        ("מיכל עלים בגבעה", "מיכל עלים בגבעה", "032892846"),
        ("עלה עלה", 'עלה עלה בע"מ', "513993436"),
        ("קניון בשביל כולם", "קניון בשביל כולם", "205651987"),
        ("טמפו", "טמפו שיווק / טמפו משקאות", "557652815"),
        ("אלקטרה קמעונאות", 'אלקטרה קמעונאות בע"מ', "516387115"),
        ("קיי אס פי", '57 קיי אס פי אקספרס בע"מ', "515348381"),
        ("י.מ.ר אביזרים", 'י.מ.ר אביזרים 2017 בע"מ', "515564268"),
        ("ניביט", "ניביט / רשת סופרמרקטים", "514068980"),
        ("בועז מזרחי אדם", "בועז מזרחי אדם", "028005379"),
        ("רביע מדאח", "רביע מדאח", "029938016"),
        ("אבי שושן", 'אבי שושן החוויה יבוא ושיווק בע"מ', "514712439"),
        ("פאנדנגו", 'פאנדנגו איסוף ומחזור בע"מ', "512529207"),
    ]

    for token, name, supplier_id in rules:
        if token in joined:
            return name, supplier_id

    # Most Hebrew invoices place the issuer and its VAT ID before the recipient
    # block. Restrict the fallback to that header so a customer is never learned
    # as the supplier merely because its ID also appears on the invoice.
    header = joined.split("לכבוד", 1)[0]
    header_rows = header.splitlines()
    vat_id = first_match(header, [r"(?:ע\.?מ\.?|ח\.?פ\.?)\s*[:.]?\s*(\d{9})"])
    if vat_id:
        for row in header_rows:
            candidate = row.strip(" .:-")
            if not candidate or vat_id in candidate or "מספר" in candidate:
                continue
            if re.search(r"[א-תA-Za-z]", candidate):
                return candidate, vat_id

    return "", ""


def parse_invoice(text: str) -> dict:
    rows = lines(text)
    joined = "\n".join(rows)

    document_type = classify_document(joined)
    supplier, supplier_id = identify_supplier(joined)

    invoice_number = first_match(joined, [
        r"חשבונית מס\s+([0-9]+\s*/\s*[0-9]+)",
        r"חשבונית מס מספר\s+(\d+)",
        r"חשבונית מס\s*\)מקור\(\s*\n(\d+)",
        r"חשבונית מס/קבלה\s+מס\.?\s*(\d+)",
        r"חשבונית זיכוי מס\.?\s*(\d+)",
        r"מספר\s*:?\s*([0-9]{2}/[0-9]{6})",
        r"קבלה מספר\s+(\d+)",
        r"חשבונית מס/קבלה\s*-\s*([A-Z0-9]+)",
        r"מספר תעודה\s*:?\s*([A-Z0-9]+)",
        r"חשבונית מס\s+([A-Z]{1,3}\d{6,})",
    ])
    invoice_number = re.sub(r"\s*/\s*", "/", invoice_number)

    invoice_date = ""

    if document_type == "ריכוז חשבון":
        month_map = {
            "ינואר": 1, "פברואר": 2, "מרץ": 3, "אפריל": 4,
            "מאי": 5, "יוני": 6, "יולי": 7, "אוגוסט": 8,
            "ספטמבר": 9, "אוקטובר": 10, "נובמבר": 11, "דצמבר": 12,
        }

        month_line = first_match(joined, [
            r"ריכוז חשבון.*?לחודש\s*:\s*([^\n]+)"
        ])
        year_match = re.search(r"(20\d{2})", month_line)

        if year_match:
            for month_name, month_number in month_map.items():
                if month_name in month_line:
                    invoice_date = f"{year_match.group(1)}-{month_number:02d}-01"
                    break
    else:
        invoice_date = normalize_date(first_match(joined, [
            r"([0-3]?\d[./\\-][01]?\d[./\\-](?:20)?\d{2})\s+תאריך\s*:",
            r"תאריך חשבונית\s*:?\s*([0-3]?\d[./\\-][01]?\d[./\\-](?:20)?\d{2})",
            r"([0-3]?\d[./\\-][01]?\d[./\\-](?:20)?\d{2})\s+חשבונית מס מספר",
            r"חשבונית מס מספר\s+\d+\s+([0-3]?\d[./\\-][01]?\d[./\\-](?:20)?\d{2})",
            r"^([0-3]?\d\\[01]?\d\\20\d{2})$",
            r"תאריך חשבונית([0-3]?\d[./\\-][01]?\d[./\\-](?:20)?\d{2})",
            r"תאריך\s*:?\s*([0-3]?\d[./\\-][01]?\d[./\\-](?:20)?\d{2})",
        ]))

    due_date = normalize_date(first_match(joined, [
        r"לתשלום עד\s*:?\s*([0-3]?\d[./-][01]?\d[./-](?:20)?\d{2})",
        r"תאריך פירעון\s*:?\s*([0-3]?\d[./-][01]?\d[./-](?:20)?\d{2})",
        r"תאריך אחרון לתשלום\s*:?\s*([0-3]?\d[./-][01]?\d[./-](?:20)?\d{2})",
    ]))

    subtotal = vat = total = None

    if supplier == "בבאיי משה":
        subtotal = value_before_label(rows, ['סה"כ חייב מע"מ'])
        vat = value_before_label(rows, ['מע"מ 18.00 %'])
        total = value_before_label(rows, ['סה"כ לתשלום'])

    elif supplier == "מיכל עלים בגבעה":
        invoice_number = invoice_number or first_match(joined, [
            r"חשבונית מס\s*\)מקור\(\s*\n(\d+)"
        ])
        subtotal = value_before_label(rows, ["לפני מע''מ"])
        vat = value_before_label(rows, ["מע''מ"])
        total = value_before_label(rows, ["סה''כ"])

    elif supplier == 'עלה עלה בע"מ':
        subtotal = value_before_label(rows, ['סה"כ לפני מע"מ'])
        vat = value_before_label(rows, ['סכום המע"מ'])
        total = value_before_label(rows, ['סה"כ כולל מע"מ'])

    elif supplier == 'עין גב אחזקות - אגודה שיתופית חקלאית':
        subtotal = value_before_label(rows, ['מחיר כולל', 'סה"כ לפני מע"מ'])
        vat = value_before_label(rows, ['מע"מ'])
        total = value_before_label(rows, ['סה"כ מחיר', 'סה"כ כולל מע"מ'])

    else:
        subtotal = value_before_label(rows, [
            'סה"כ ללא מע"מ',
            'סה"כ לפני מע"מ',
            'סה"כ חייב מע"מ',
            'סה"כ אחרי עיגול',
            'מחיר כולל',
        ])
        vat = vat_value(rows)
        total = value_before_label(rows, [
            'סה"כ לתשלום',
            'סה"כ כולל מע"מ',
            'סה"כ לחיוב',
            'סה"כ מחיר',
        ])

    if total is not None and subtotal is not None and vat is None:
        vat = round(total - subtotal, 2)

    if total is not None and vat is not None and subtotal is None:
        subtotal = round(total - vat, 2)

    if document_type == "חשבונית זיכוי":
        subtotal = -abs(subtotal) if subtotal is not None else None
        vat = -abs(vat) if vat is not None else None
        total = -abs(total) if total is not None else None

    return {
        "document_type": document_type,
        "supplier": supplier,
        "supplier_id": supplier_id,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "subtotal": subtotal,
        "vat": vat,
        "total": total,
        "currency": "ILS",
    }


def _row(code, description, quantity, unit_price, line_total):
    return {
        "קוד מוצר": str(code).strip(),
        "תיאור": description.strip(),
        "כמות": float(quantity),
        "מחיר יחידה": float(unit_price),
        'סה"כ שורה': float(line_total),
    }


def extract_items(text: str) -> list[dict]:
    rows = lines(text)
    joined = "\n".join(rows)
    results = []

    # Common SAP layout: line total, unit price, quantity, description, code,
    # row number. Some descriptive lines intentionally contain no price.
    if "programname:SAP" in joined:
        priced = re.compile(
            r"^(-?\d{1,3}(?:,\d{3})*\.\d{2})\s+₪\s+"
            r"(-?\d{1,3}(?:,\d{3})*\.\d{2})\s+₪\s+"
            r"(-?\d+(?:\.\d+)?)\s+(.+?)\s+(\d+)\s+\d+$"
        )
        descriptive = re.compile(
            r"^(-?\d+(?:\.\d+)?)\s+(.+?)\s+(\d+)\s+\d+$"
        )
        active = False
        for row_text in rows:
            if "קוד פריט" in row_text and "תיאור" in row_text:
                active = True
                continue
            if active and 'סה"כ לפני מע"מ' in row_text:
                break
            if not active:
                continue
            match = priced.match(row_text)
            if match:
                line_total, unit_price, quantity, description, code = match.groups()
                results.append(
                    _row(code, description, quantity, amount(unit_price), amount(line_total))
                )
                continue
            match = descriptive.match(row_text)
            if match:
                quantity, description, code = match.groups()
                results.append(_row(code, description, quantity, 0.0, 0.0))
        return results

    # Simple Freelance layout.
    if "בבאיי משה" in joined:
        pattern = re.compile(
            r"^(\d{1,3}(?:,\d{3})*\.\d{2})\s+ש\"ח\s+"
            r"(\d{1,3}(?:,\d{3})*\.\d{2})\s+"
            r"(\d+(?:\.\d+)?)\s+(.+)$"
        )
        for row_text in rows:
            match = pattern.match(row_text)
            if match:
                line_total, unit_price, quantity, description = match.groups()
                return [_row("", description, quantity, amount(unit_price), amount(line_total))]

    # Delivery-note invoice.
    if "מיכל עלים בגבעה" in joined:
        match = re.search(
            r"([0-9,]+\.\d{2})\s+ת\.מ מס'\s*(\d+)\s+"
            r"([0-3]?\d-\d{2}-\d{4})",
            joined
        )
        if match:
            line_total, code, _ = match.groups()
            value = amount(line_total)
            return [_row(code, f"תעודת משלוח מס' {code}", 1, value, value)]

    # Aleh Aleh monthly summary, 44 consolidated item rows.
    if "ריכוז חשבון עלה עלה" in joined:
        item_pattern = re.compile(
            r"^(?:#\s+שח\s+|#\s+|)"
            r"₪\s*(-?\d+(?:,\d{3})*\.\d{2})\s+"
            r"(?:\.01\s+)?"
            r"₪\s*(-?\d+(?:,\d{3})*\.\d{2})\s+"
            r"(-?\d+(?:\.\d+)?)\s+"
            r"(.+?)\s+(\d+)\s+(\d+)$"
        )

        active = False
        seen_codes = []

        for row_text in rows:
            if row_text == "ריכוז פריטים":
                active = True
                continue

            if active and 'סה"כ חייב במע"מ' in row_text:
                break

            if not active:
                continue

            match = item_pattern.match(row_text)
            if not match:
                continue

            line_total, unit_price, quantity, description, code, _ = match.groups()
            results.append(
                _row(code, description, quantity, amount(unit_price), amount(line_total))
            )

        return results

    # Eden David layout.
    eden = re.compile(
        r"^(-?\d{1,3}(?:,\d{3})*\.\d{2})\s+"
        r"(-?\d{1,3}(?:,\d{3})*\.\d{2})\s+"
        r"(-?\d+(?:\.\d+)?)\s+"
        r"(.+?)\s+([A-Z0-9][A-Z0-9/_-]*)\s+\d+$"
    )

    # Morning / Libre invoice.
    morning = re.compile(
        r"^₪?(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"₪?(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"(.+?)\s+(-?\d+(?:\.\d+)?)\s+(.+)$"
    )

    # Priority item row, e.g. Y.M.R.
    priority = re.compile(
        r"^(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"(-?\d+(?:,\d{3})*\.\d{2})ש\"ח\s+"
        r"(-?\d+(?:\.\d+)?)יח'\s+"
        r"(-?\d+(?:\.\d+)?)יח'\s+"
        r"(.+?)\s+(?:\*+\d+\*+\s+)?(\d+)\s+\d+$"
    )

    # Electra delivery row.
    electra = re.compile(
        r"^(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"(-?\d+(?:\.\d+)?)\s+"
        r"(.+?)\s+(\d+)\s+\d{2}/\d{2}/\d{4}\s+\d+$"
    )

    # KSP rows.
    ksp = re.compile(
        r"^₪\s*(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"₪\s*(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"₪\s*(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"(-?\d+(?:\.\d+)?)\s+(.+?)\s+(\d+)\s+\d+\s+\d+$"
    )

    # Boaz Morning row: total, unit price, description, quantity, code.
    boaz = re.compile(
        r"^₪?(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"₪?(-?\d+(?:,\d{3})*\.\d{2})\s+"
        r"(.+?)\s+(\d+(?:\.\d+)?)\s+([^\s]+)$"
    )

    seen = set()

    for row_text in rows:
        match = electra.match(row_text)
        if match:
            line_total, unit_price, quantity, description, code = match.groups()
            item = _row(code, description, quantity, amount(unit_price), amount(line_total))
            key = tuple(item.values())
            if key not in seen:
                results.append(item)
                seen.add(key)
            continue

        match = eden.match(row_text)
        if match:
            line_total, unit_price, quantity, description, code = match.groups()
            item = _row(code, description, quantity, amount(unit_price), amount(line_total))
            key = tuple(item.values())
            if key not in seen:
                results.append(item)
                seen.add(key)
            continue

        match = priority.match(row_text)
        if match:
            line_total, unit_price, _, quantity, description, code = match.groups()
            results.append(_row(code, description, quantity, amount(unit_price), amount(line_total)))
            continue

        match = ksp.match(row_text)
        if match:
            _, line_total, unit_price, quantity, description, code = match.groups()
            if amount(line_total) != 0:
                results.append(_row(code, description, quantity, amount(unit_price), amount(line_total)))
            continue

        if "בועז מזרחי אדם" in joined:
            match = boaz.match(row_text)
            if match and "Rose" in row_text:
                line_total, unit_price, description, quantity, code = match.groups()
                item = _row(code, description, quantity, amount(unit_price), amount(line_total))
                key = tuple(item.values())
                if key not in seen:
                    results.append(item)
                    seen.add(key)

    # Tempo rows, broad but constrained to rows beginning with monetary totals.
    if "טמפו" in joined:
        tempo = re.compile(
            r"^(-?\d+(?:,\d{3})*\.\d{2})\s+"
            r"(?:-?\d+(?:,\d{3})*\.\d{2}\s+){1,5}"
            r"(-?\d+(?:\.\d+)?)\s+"
            r"(\d+)\s+(\d+)\s+(.+)$"
        )
        for row_text in rows:
            match = tempo.match(row_text)
            if match:
                line_total, quantity, code, barcode, description = match.groups()
                results.append(_row(code, description, quantity, 0.0, amount(line_total)))

    return results
