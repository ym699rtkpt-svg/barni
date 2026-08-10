from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any, Iterable, Mapping


_FINAL_HEBREW = str.maketrans({"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"})
_HEBREW_TO_LATIN = {
    "א": "a", "ב": "v", "ג": "g", "ד": "d", "ה": "h", "ו": "v",
    "ז": "z", "ח": "h", "ט": "t", "י": "y", "כ": "k", "ל": "l",
    "מ": "m", "נ": "n", "ס": "s", "ע": "a", "פ": "f", "צ": "ts",
    "ק": "k", "ר": "r", "ש": "sh", "ת": "t",
}
_LATIN_VOWELS = frozenset("aeiouywh")


def normalize_search_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.translate(_FINAL_HEBREW)
    text = re.sub(r"[^0-9a-z\u05d0-\u05ea]+", " ", text)
    return " ".join(text.split())


def _latinize(value: str) -> str:
    return "".join(_HEBREW_TO_LATIN.get(character, character) for character in value)


def _latin_skeleton(value: str) -> str:
    return "".join(
        character
        for character in value
        if character.isdigit() or ("a" <= character <= "z" and character not in _LATIN_VOWELS)
    )


def search_representations(value: object) -> tuple[str, ...]:
    normalized = normalize_search_text(value)
    if not normalized:
        return ()
    latinized = normalize_search_text(_latinize(normalized))
    skeleton = _latin_skeleton(latinized)
    values = [normalized, latinized]
    if len(skeleton) >= 2:
        values.append(skeleton)
    return tuple(dict.fromkeys(item for item in values if item))


def contains_search_match(candidate: object, query: object) -> bool:
    needles = search_representations(query)
    haystacks = search_representations(candidate)
    return bool(needles and haystacks) and any(
        needle in haystack
        for needle in needles
        for haystack in haystacks
    )


def prefix_search_match(candidate: object, query: object) -> bool:
    needles = search_representations(query)
    haystacks = search_representations(candidate)
    return bool(needles and haystacks) and any(
        word.startswith(needle)
        for needle in needles
        for haystack in haystacks
        for word in haystack.split()
    )


@dataclass(frozen=True)
class SearchSuggestion:
    kind: str
    label: str
    detail: str
    invoice_id: int


@dataclass(frozen=True)
class _Candidate:
    suggestion: SearchSuggestion
    source_order: int


def _text(row: Mapping[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def build_search_suggestions(
    query: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    limit: int = 8,
) -> list[SearchSuggestion]:
    normalized_query = normalize_search_text(query)
    query_length = len(normalized_query.replace(" ", ""))
    if not query_length:
        return []

    candidates = _suggestion_candidates(rows)
    matcher = prefix_search_match if query_length == 1 else contains_search_match
    kind_order = {"Supplier": 0, "Product": 1, "Invoice number": 2, "Invoice": 3, "Date": 4}
    matched = [
        candidate
        for candidate in candidates
        if matcher(candidate.suggestion.label, normalized_query)
    ]
    matched.sort(
        key=lambda candidate: (
            0 if prefix_search_match(candidate.suggestion.label, normalized_query) else 1,
            kind_order.get(candidate.suggestion.kind, 9),
            candidate.source_order,
            normalize_search_text(candidate.suggestion.label),
        )
    )
    return [candidate.suggestion for candidate in matched[: max(0, limit)]]


def _suggestion_candidates(
    rows: Iterable[Mapping[str, Any]],
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, label: str, detail: str, invoice_id: int, order: int) -> None:
        cleaned = label.strip()
        key = (kind, normalize_search_text(cleaned))
        if not cleaned or not key[1] or key in seen:
            return
        seen.add(key)
        candidates.append(
            _Candidate(SearchSuggestion(kind, cleaned, detail.strip(), invoice_id), order)
        )

    invoice_seen: set[int] = set()
    for order, row in enumerate(rows):
        try:
            invoice_id = int(row.get("invoice_id") or row.get("id"))
        except (TypeError, ValueError):
            continue
        supplier = _text(row, "canonical_supplier_name") or _text(row, "supplier")
        number = _text(row, "invoice_number")
        invoice_date = _text(row, "invoice_date")
        document_type = _text(row, "document_type") or "Invoice"
        product = _text(row, "canonical_product_name")
        item_code = _text(row, "item_code")
        invoice_label = f"{supplier or document_type} · {invoice_date or 'Date unavailable'}"
        invoice_detail = f"Invoice #{number}" if number else document_type

        add("Supplier", supplier, invoice_detail, invoice_id, order)
        add("Product", product, supplier or invoice_detail, invoice_id, order)
        if product:
            add("Product", item_code, product or supplier, invoice_id, order)
        if invoice_id not in invoice_seen:
            invoice_seen.add(invoice_id)
            add("Invoice", invoice_label, invoice_detail, invoice_id, order)
            add("Invoice number", number, supplier or invoice_date, invoice_id, order)
            add("Date", invoice_date, supplier or invoice_detail, invoice_id, order)

    return candidates


def search_suggestion_catalog(
    rows: Iterable[Mapping[str, Any]],
    *,
    limit: int = 250,
) -> list[SearchSuggestion]:
    """Return a bounded canonical-memory catalog for client-side type-ahead."""
    return [
        candidate.suggestion
        for candidate in _suggestion_candidates(rows)[: max(0, limit)]
    ]
