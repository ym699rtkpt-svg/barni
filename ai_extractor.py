
from __future__ import annotations

import base64
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from openai import OpenAI
from pydantic import BaseModel, Field


DocumentType = Literal[
    "חשבונית מס",
    "חשבונית מס/קבלה",
    "קבלה",
    "חשבונית זיכוי",
    "תעודת משלוח",
    "ריכוז חשבון",
    "דרישת תשלום",
    "אחר",
]

REQUIRED_EXTRACTION_COMMANDS = ("pdftotext", "pdftoppm", "tesseract")
REQUIRED_OCR_LANGUAGES = ("eng", "heb")
REQUIRED_EXTRACTION_MODULES = ("openai", "pydantic", "PIL")


@dataclass(frozen=True)
class ExtractionCapabilityReport:
    """Presence-only deployment diagnostics; never contains credential values."""

    credential_configured: bool
    available_commands: tuple[str, ...]
    available_ocr_languages: tuple[str, ...]
    available_python_modules: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.missing

    def internal_summary(self) -> str:
        if self.ready:
            return "Extraction runtime READY"
        return "Extraction runtime NOT READY; missing: " + ", ".join(self.missing)


def extraction_service_ready(
    environment: Mapping[str, str] | None = None,
) -> bool:
    """Return credential availability without reading or exposing its value."""
    source = os.environ if environment is None else environment
    return bool(str(source.get("OPENAI_API_KEY", "")).strip())


def _available_tesseract_languages(command: str | None) -> set[str]:
    if not command:
        return set()
    try:
        result = subprocess.run(
            [command, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if result.returncode != 0:
        return set()
    return {
        value.strip()
        for value in result.stdout.splitlines()
        if value.strip() and not value.lower().startswith("list of available")
    }


def extraction_capability_report(
    environment: Mapping[str, str] | None = None,
) -> ExtractionCapabilityReport:
    """Check extraction deployment capabilities without making an AI request."""
    command_paths = {
        name: shutil.which(name)
        for name in REQUIRED_EXTRACTION_COMMANDS
    }
    available_commands = tuple(
        name for name, path in command_paths.items() if path
    )
    ocr_languages = _available_tesseract_languages(command_paths.get("tesseract"))
    available_modules = tuple(
        name
        for name in REQUIRED_EXTRACTION_MODULES
        if importlib.util.find_spec(name) is not None
    )

    missing: list[str] = []
    if not extraction_service_ready(environment):
        missing.append("credential:OPENAI_API_KEY")
    missing.extend(
        f"command:{name}"
        for name in REQUIRED_EXTRACTION_COMMANDS
        if name not in available_commands
    )
    missing.extend(
        f"ocr-language:{name}"
        for name in REQUIRED_OCR_LANGUAGES
        if name not in ocr_languages
    )
    missing.extend(
        f"python-module:{name}"
        for name in REQUIRED_EXTRACTION_MODULES
        if name not in available_modules
    )
    return ExtractionCapabilityReport(
        credential_configured=extraction_service_ready(environment),
        available_commands=available_commands,
        available_ocr_languages=tuple(sorted(ocr_languages)),
        available_python_modules=available_modules,
        missing=tuple(missing),
    )


class InvoiceItem(BaseModel):
    item_code: str = ""
    description: str
    quantity: float | None = None
    unit: str = ""
    unit_price: float | None = None
    line_total: float | None = None


class InvoiceDocument(BaseModel):
    document_type: DocumentType
    supplier: str = ""
    supplier_id: str = ""
    invoice_number: str = ""
    invoice_date: str = Field(
        default="",
        description="ISO date YYYY-MM-DD. For a monthly statement, use the first day of the month.",
    )
    due_date: str = Field(default="", description="ISO date YYYY-MM-DD")
    subtotal: float | None = None
    taxable_amount: float | None = Field(
        default=None,
        description="Amount subject to VAT before VAT. Null when not stated.",
    )
    exempt_amount: float | None = Field(
        default=None,
        description="Amount exempt from VAT. Null when not stated.",
    )
    vat_rate: float | None = Field(
        default=None,
        description="VAT rate as a percentage, for example 18.0.",
    )
    vat: float | None = None
    total: float | None = None
    tax_treatment: Literal[
        "חייב במע״מ",
        "פטור ממע״מ",
        "מעורב",
        "לא רלוונטי",
        "לא ברור",
    ] = "לא ברור"
    currency: str = "ILS"
    related_document_number: str = ""
    statement_month: str = Field(
        default="",
        description="YYYY-MM for monthly statements, otherwise empty.",
    )
    items: list[InvoiceItem] = []
    warnings: list[str] = []
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


SYSTEM_PROMPT = """
You extract structured accounting data from Israeli restaurant supplier documents.

Rules:
1. Read Hebrew and English.
2. Distinguish the supplier from the customer. The customer is often "מפגש הדייגים".
3. Never invent a value. Use an empty string or null when the document does not support it.
   For supplier, copy only a company name explicitly visible on the document. Never infer,
   complete, translate, or guess a supplier name from general knowledge or similarity.
4. Classify the document accurately: invoice, invoice/receipt, receipt, credit note,
   delivery note, monthly statement, payment request, or other.
5. Credit-note amounts must be negative.
6. Invoice dates and due dates must use YYYY-MM-DD.
7. For monthly statements, invoice_date is the first day of the statement month and
   statement_month is YYYY-MM.
8. Extract every visible item row. Preserve supplier item codes where present.
9. Do not treat supplier IDs, customer IDs, phone numbers, order numbers, or dates as money.
10. Extract VAT structure explicitly:
    - taxable_amount: amount subject to VAT before VAT
    - exempt_amount: amount exempt from VAT
    - vat_rate: printed VAT percentage
    - tax_treatment: חייב במע״מ / פטור ממע״מ / מעורב / לא רלוונטי / לא ברור
11. Validate totals according to tax treatment:
    - regular taxable: taxable_amount + VAT = total
    - mixed: taxable_amount + exempt_amount + VAT = total
    - exempt: exempt_amount = total and VAT may be zero or absent
    Do not invent VAT when it is not printed or not relevant.
12. For a delivery-note summary row, describe it as a related delivery note rather than
    inventing a product.
12. Return only data matching the required schema.
""".strip()


def _command_path(name: str) -> str:
    candidates = [
        shutil.which(name),
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"לא נמצאה הפקודה {name}")


def _run(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "הפקודה נכשלה")
    return result


def extract_native_pdf_text(path: Path) -> str:
    pdftotext = _command_path("pdftotext")
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp:
        _run([pdftotext, "-layout", str(path), temp.name], timeout=20)
        return Path(temp.name).read_text(encoding="utf-8", errors="ignore")


def pdf_to_images(path: Path, max_pages: int = 6, dpi: int = 180) -> list[Path]:
    pdftoppm = _command_path("pdftoppm")
    temp_dir = Path(tempfile.mkdtemp(prefix="invoice_ai_"))
    prefix = temp_dir / "page"
    _run([
        pdftoppm,
        "-f", "1",
        "-l", str(max_pages),
        "-png",
        "-r", str(dpi),
        str(path),
        str(prefix),
    ], timeout=45)
    return sorted(temp_dir.glob("page-*.png"))


def image_data_url(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def build_input(path: Path, max_pages: int = 6) -> tuple[list[dict], str]:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        try:
            native_text = extract_native_pdf_text(path)
        except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired):
            native_text = ""
        if len("".join(native_text.split())) >= 80:
            content = [{
                "type": "input_text",
                "text": (
                    "Extract this document. The following text came directly from the PDF "
                    "with layout preservation:\n\n" + native_text
                ),
            }]
            return content, "ai_pdf_text"

        images = pdf_to_images(path, max_pages=max_pages)
        if not images:
            raise RuntimeError("No readable PDF pages were produced.")
        content = [{
            "type": "input_text",
            "text": "Extract this scanned PDF from the page images.",
        }]
        content.extend({
            "type": "input_image",
            "image_url": image_data_url(image),
            "detail": "high",
        } for image in images)
        return content, "ai_pdf_vision"

    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return [
            {"type": "input_text", "text": "Extract this document image."},
            {
                "type": "input_image",
                "image_url": image_data_url(path),
                "detail": "high",
            },
        ], "ai_image_vision"

    raise ValueError(f"סוג קובץ לא נתמך ב-AI: {suffix}")


def extract_with_ai(
    path: Path,
    model: str | None = None,
    max_pages: int = 6,
) -> tuple[dict, str]:
    if not extraction_service_ready():
        raise RuntimeError(
            "חסר OPENAI_API_KEY. יש להגדיר מפתח API לפני הפעלת מנוע ה-AI."
        )

    client = OpenAI()
    chosen_model = model or os.environ.get("INVOICE_AI_MODEL", "gpt-5.6")
    content, method = build_input(path, max_pages=max_pages)

    response = client.responses.parse(
        model=chosen_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        text_format=InvoiceDocument,
    )

    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("המודל לא החזיר פלט מובנה.")

    result = parsed.model_dump()
    return result, method
