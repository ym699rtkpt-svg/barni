# BAR-ALPHA-02 — Unified Evidence & Confidence Contract

## Purpose

Barni may explain a conclusion only when it can identify the business, the claim, the evidence, and the specific kind of confidence involved. This contract creates that common language without changing OCR, the database schema, or the existing invoice lifecycle.

The governing chain is:

`Source → EvidenceRef → typed confidence → Claim → explanation → source opening`

Human-readable copy is presentation. The structured claim is the trust record.

## Audit: Formats Before BAR-ALPHA-02

| Area | Previous evidence shape | Previous confidence meaning | Risk |
|---|---|---|---|
| Identity and review | `InvoiceEvidence` objects plus `evidence_json.invoice_ids` | Match probability as a float | Useful context, but no shared scope or claim |
| Business Facts | Free-form `evidence_json`, `confidence_json`, and aggregate `business_confidence` | Fact completeness/trust | Component completeness could be mistaken for AI confidence |
| Price comparison | Tuple of invoice IDs | Implied by `TRUSTED` status | Invoice lines and observed values were not part of the comparison result contract |
| Invoice Intelligence | Free-form evidence dictionary and `source_record_ids` | Observation/rule confidence | Different rules could attach different shapes |
| Barni Thinking | Re-resolved `InvoiceEvidence` | Separate presentation confidence text | Review could drift from the insight's actual sources |
| Business Stories | `StoryEvidence` objects and `evidence_values` | Implied by story generation | Narrative was not itself a structured claim |
| Search and Home opening | Direct integer invoice IDs | None | Opening worked, but the source-link convention was not reusable |
| Attention design | Proposed evidence and confidence fields | Observation ranking confidence | No implemented contract to receive future observations |

The active high-value paths now expose the shared contract. Old shapes remain readable during Alpha compatibility migration.

## `EvidenceRef`

`services/evidence.py` owns the only generic source-reference type.

Every reference includes:

- `business_id`: mandatory tenant scope;
- `source_type`: invoice, invoice line, identity decision, business fact, or review candidate;
- `source_id`: stable parent record identifier;
- `subrecord_id`: optional line or field identifier;
- `observed_value`: the value used by the conclusion;
- `field_name`: the source field when relevant;
- `captured_at`: observation date or capture timestamp;
- `location`: an archived document location when available;
- `integrity_ref`: reserved for a checksum or immutable object reference;
- `metadata`: descriptive context only, never hidden reasoning.

Invoice-line references use the invoice as `source_id` and the line as `subrecord_id`. This makes source opening reliable while retaining line-level traceability. `source_invoice_id()` is the shared navigation resolver.

## Shared Claim Contract

Every migrated conclusion is represented by `Claim`:

- business scope;
- claim type;
- subject type and ID;
- human-readable statement;
- optional structured value;
- one or more `EvidenceRef` objects;
- one typed confidence assessment;
- producer and producer version;
- creation timestamp;
- optional metadata.

A claim marked `SUPPORTED` cannot be constructed without evidence. Evidence from another business cannot be attached. These invariants fail closed at the contract boundary.

## Confidence Taxonomy

Confidence is not one universal score.

1. **Extraction confidence** — how reliably a value was read from a source document. It belongs to extraction and must not imply business truth.
2. **Identity confidence** — how strongly evidence supports an entity match. It belongs to canonical identity and review.
3. **Fact trust confidence** — whether identity, units, packages, VAT, currency, quantity, and evidence make a business fact usable.
4. **Observation confidence** — how strongly trusted facts support a detected change or condition.
5. **Answer confidence** — whether a user-facing story or answer is sufficiently grounded in its underlying claims.

Each assessment also has a qualitative status: `SUPPORTED`, `PARTIAL`, `INSUFFICIENT`, `CONFLICT`, or `NOT_ASSESSED`.

`combine_confidence()` accepts only assessments of the same type and combines them conservatively. Mixing extraction confidence with identity, fact trust, observation, or answer confidence raises an error. Cross-layer reasoning must preserve the individual assessments or apply an explicit, separately documented policy; it must never average them silently.

Normal product UI should communicate uncertainty in Barni's voice. Raw values remain internal unless a technical view explicitly requests them.

## Migrated Active Paths

### Comparable Price Ledger

New facts persist typed invoice-line references inside the existing evidence JSON column. Old records containing `invoice_ids` and `invoice_item_ids` are converted by a compatibility reader. `BusinessFact.claim` uses fact-trust confidence. `PriceComparison.claim` uses observation confidence and includes both current and previous invoice-line evidence.

Rejected comparisons remain traceable and explain their conflict. They do not become trusted claims.

### Identity Review

Review candidates expose `evidence_refs` derived from their existing invoice evidence. User decisions and review storage remain unchanged in this phase, preserving reversibility and Alpha data. The typed view gives future identity decision claims a stable input without creating a second evidence store.

### Invoice Intelligence and Proactive Observations

The existing intelligence engine remains the only rule engine. After rules run, it binds every insight to an observation claim. Existing rule dictionaries and source IDs remain compatibility fields. Attention can consume these claims later without reimplementing evidence or confidence rules.

### Narrative and Invoice Review

Every `BusinessStory` now owns an answer claim derived from its evidence. Barni Thinking resolves supporting invoices through insight claims, so the explanation and its evidence cannot silently diverge. Existing narrative copy and layout are unchanged.

### Home, Feed, Search, and Source Opening

Story cards resolve “Open invoice” through the shared evidence resolver. Search continues using the current backend and invoice detail flow. The same resolver can be reused by Search results and future answer components without knowing producer-specific evidence shapes.

### Accountant Workspace

Readiness remains governed by BAR-ALPHA-01 lifecycle state. BAR-ALPHA-02 does not reinterpret readiness as confidence. When accountant claims are introduced, they must use this contract and cite the invoices included or excluded.

## Compatibility Policy

- No database schema was changed.
- Existing `evidence_json`, `confidence_json`, `StoryEvidence`, `InvoiceEvidence`, `source_record_ids`, and rule evidence dictionaries remain readable.
- New Business Facts write both the legacy keys and typed `refs` into the same JSON payload.
- Typed claims are generated deterministically from stored records and current engine output.
- Producer versions distinguish the unified contract from legacy output.
- Legacy adapters may be removed only after stored Alpha records have been backfilled and all consumers use typed claims.

## Verification Contract

Automated coverage verifies:

- a price comparison cites both invoice lines and both invoices;
- an identity review exposes typed supporting evidence;
- a narrative preserves evidence in its answer claim;
- an evidence reference opens the correct invoice;
- claim and evidence business scopes cannot differ;
- unrelated confidence types cannot be combined;
- supported claims without evidence are rejected;
- legacy price evidence remains readable.

The pre-existing workflow, identity, facts, intelligence, narrative, Search, and lifecycle suites remain the regression contract.

## Known Legacy Areas and Risks

- Alpha is single-business, so `barni-local-business` is the explicit scope until account tenancy exists. It must be replaced by a real business ID before multi-tenant operation.
- Identity decisions are durably evidence-backed in their existing audit tables but are not yet persisted as generic Claim records.
- Some intelligence rules still author free-form evidence dictionaries before the engine binds the final Claim. Future rule work should emit typed subject and evidence inputs directly.
- Historical facts are adapted at read time. A future controlled backfill should add typed refs to every stored fact.
- Integrity references are modeled but not populated because archived-file hashing is not yet a shared service.
- Search results themselves are not claims; only evidence-backed conclusions need claims. Their invoice opening path is compatible with the common resolver.
- No dedicated Attention runtime exists yet. Its future observations must accept Claim objects rather than invent another evidence structure.

## Architectural Boundary

Evidence answers “where did this come from?” Confidence answers “what kind of support do we have?” Claims answer “what is Barni asserting?” Lifecycle answers “where is the invoice in the workflow?” These responsibilities must remain separate.

This contract advances the company mission by making the path from data to understanding inspectable, scoped, and difficult to misrepresent.
