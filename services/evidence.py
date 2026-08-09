"""Shared evidence, claim, and confidence contracts for Barni.

This module deliberately contains no database or UI code. Producers create typed
claims; consumers decide how to store or present them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping


LOCAL_BUSINESS_ID = "barni-local-business"


class SourceType(str, Enum):
    INVOICE = "invoice"
    INVOICE_LINE = "invoice_line"
    IDENTITY_DECISION = "identity_decision"
    BUSINESS_FACT = "business_fact"
    REVIEW_CANDIDATE = "review_candidate"


class ConfidenceType(str, Enum):
    EXTRACTION = "extraction"
    IDENTITY = "identity"
    FACT_TRUST = "fact_trust"
    OBSERVATION = "observation"
    ANSWER = "answer"


class ConfidenceStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"
    CONFLICT = "conflict"
    NOT_ASSESSED = "not_assessed"


class EvidenceContractError(ValueError):
    pass


class ConfidenceTypeMismatchError(EvidenceContractError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class EvidenceRef:
    business_id: str
    source_type: SourceType | str
    source_id: int | str
    subrecord_id: int | str | None = None
    observed_value: Any = None
    field_name: str = ""
    captured_at: str = ""
    location: str = ""
    integrity_ref: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.business_id).strip():
            raise EvidenceContractError("Evidence must be scoped to a business.")
        if not str(self.source_type).strip() or self.source_id in (None, ""):
            raise EvidenceContractError("Evidence must identify its source.")
        object.__setattr__(self, "source_type", SourceType(self.source_type))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "business_id": self.business_id, "source_type": self.source_type.value,
            "source_id": self.source_id, "subrecord_id": self.subrecord_id,
            "observed_value": self.observed_value, "field_name": self.field_name,
            "captured_at": self.captured_at, "location": self.location,
            "integrity_ref": self.integrity_ref, "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EvidenceRef":
        data = {key: value.get(key) for key in (
            "business_id", "source_type", "source_id", "subrecord_id",
            "observed_value", "field_name", "captured_at", "location",
            "integrity_ref", "metadata")}
        data["metadata"] = data["metadata"] or {}
        return cls(**data)


@dataclass(frozen=True)
class Confidence:
    type: ConfidenceType | str
    status: ConfidenceStatus | str
    value: float | None = None
    explanation: str = ""
    components: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "type", ConfidenceType(self.type))
        object.__setattr__(self, "status", ConfidenceStatus(self.status))
        if self.value is not None and not 0 <= float(self.value) <= 1:
            raise EvidenceContractError("Confidence values must be between 0 and 1.")
        object.__setattr__(self, "components", dict(self.components))

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "status": self.status.value,
                "value": self.value, "explanation": self.explanation,
                "components": dict(self.components)}


def combine_confidence(values: Iterable[Confidence]) -> Confidence:
    """Combine only like-for-like confidence. Cross-type mixing is an error."""
    items = tuple(values)
    if not items:
        raise EvidenceContractError("At least one confidence assessment is required.")
    kinds = {item.type for item in items}
    if len(kinds) != 1:
        raise ConfidenceTypeMismatchError("Different confidence types cannot be combined.")
    numeric = [float(item.value) for item in items if item.value is not None]
    status = max(items, key=lambda item: list(ConfidenceStatus).index(item.status)).status
    return Confidence(items[0].type, status, min(numeric) if numeric else None,
                      "Combined conservatively from like-for-like assessments.")


@dataclass(frozen=True)
class Claim:
    business_id: str
    claim_type: str
    subject_type: str
    subject_id: int | str
    statement: str
    evidence: tuple[EvidenceRef, ...]
    confidence: Confidence
    producer: str
    producer_version: str
    created_at: str = field(default_factory=utc_now)
    value: Any = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.business_id or not self.claim_type or not self.statement:
            raise EvidenceContractError("Claims require scope, type, and statement.")
        if any(ref.business_id != self.business_id for ref in self.evidence):
            raise EvidenceContractError("Claim and evidence business scopes must match.")
        if self.confidence.status == ConfidenceStatus.SUPPORTED and not self.evidence:
            raise EvidenceContractError("A supported claim requires evidence.")
        object.__setattr__(self, "metadata", dict(self.metadata))


def invoice_ref(invoice_id: int, *, business_id: str = LOCAL_BUSINESS_ID,
                observed_value: Any = None, field_name: str = "",
                captured_at: str = "", location: str = "",
                metadata: Mapping[str, Any] | None = None) -> EvidenceRef:
    return EvidenceRef(business_id, SourceType.INVOICE, int(invoice_id),
                       observed_value=observed_value, field_name=field_name,
                       captured_at=captured_at, location=location,
                       metadata=metadata or {})


def invoice_line_ref(invoice_id: int, line_id: int, *,
                     business_id: str = LOCAL_BUSINESS_ID,
                     observed_value: Any = None, field_name: str = "",
                     captured_at: str = "", location: str = "") -> EvidenceRef:
    return EvidenceRef(business_id, SourceType.INVOICE_LINE, int(invoice_id),
                       subrecord_id=int(line_id), observed_value=observed_value,
                       field_name=field_name, captured_at=captured_at,
                       location=location, metadata={"invoice_id": int(invoice_id)})


def source_invoice_id(ref: EvidenceRef) -> int | None:
    if ref.source_type in {SourceType.INVOICE, SourceType.INVOICE_LINE}:
        try:
            return int(ref.source_id)
        except (TypeError, ValueError):
            return None
    value = ref.metadata.get("invoice_id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
