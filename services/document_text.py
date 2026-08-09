"""Local document text extraction shared by every invoice intake path."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def _command(name: str) -> str:
    candidates = (
        shutil.which(name),
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
    )
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"Required document reader is unavailable: {name}")


def _run(args: list[str], *, timeout: int) -> None:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Document reading failed.")


def _ocr_image(path: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="barni_ocr_") as folder:
        output = Path(folder) / "text"
        _run([
            _command("tesseract"), str(path), str(output),
            "-l", "heb+eng", "--psm", "6",
        ], timeout=60)
        target = output.with_suffix(".txt")
        return target.read_text(encoding="utf-8", errors="ignore") if target.exists() else ""


def _pdf_pages(path: Path, *, max_pages: int = 8) -> list[Path]:
    folder = Path(tempfile.mkdtemp(prefix="barni_pdf_"))
    prefix = folder / "page"
    _run([
        _command("pdftoppm"), "-f", "1", "-l", str(max_pages),
        "-png", "-r", "180", str(path), str(prefix),
    ], timeout=90)
    return sorted(folder.glob("page-*.png"))


def extract_document_text(path: Path, *, max_pages: int = 8) -> tuple[str, str]:
    """Return locally extracted text and the evidence-preserving method name."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".txt") as output:
            try:
                _run([_command("pdftotext"), "-layout", str(path), output.name], timeout=30)
                text = Path(output.name).read_text(encoding="utf-8", errors="ignore")
                if len(re.sub(r"\s+", "", text)) >= 40:
                    return text, "local_pdf_text"
            except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired):
                pass

        pages = _pdf_pages(path, max_pages=max_pages)
        try:
            text = "\n".join(_ocr_image(page) for page in pages)
        finally:
            for page in pages:
                page.unlink(missing_ok=True)
            if pages:
                pages[0].parent.rmdir()
        return text, "local_pdf_ocr"

    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return _ocr_image(path), "local_image_ocr"

    raise ValueError(f"Unsupported invoice file type: {suffix}")
