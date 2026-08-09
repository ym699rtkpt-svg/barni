# Barni Alpha Blockers

## Purpose

This is the ordered execution contract for making the first restaurant pilot completable without assistance. It is derived from `BARNI_ALPHA_READINESS_AUDIT.md`. Work must proceed in the order below because every later step depends on trustworthy invoice intake.

No item authorizes new product features or unrelated redesign.

## Execution order

| Order | ID | Blocker | Severity | Complexity |
|---:|---|---|---|---|
| 1 | ALPHA-B01 | Invoice reading depends entirely on unavailable external AI configuration | Critical | Medium |
| 2 | ALPHA-B02 | Failed extraction reaches normal review with blank business data | Critical | Medium |
| 3 | ALPHA-B03 | Batch processing does not show useful per-invoice progress | High | Small |
| 4 | ALPHA-B04 | Search suggestions and grouped results are not reliably grounded in searchable memory | Critical | Medium |
| 5 | ALPHA-B05 | Accountant export crashes and readiness language contradicts its own status | Critical | Small |
| 6 | ALPHA-B06 | Business Memory has no supplier, product, or price-history drill-down | High | Medium |

## ALPHA-B01 — Invoice reading reliability

- **Severity:** Critical
- **Root cause:** Feed calls the external AI extractor directly. When `OPENAI_API_KEY` is unavailable, extraction raises before using the existing local text extraction and parser. The repository already has a hybrid extraction contract, but Feed bypasses it.
- **Files involved:** `daily_intake.py`, `ai_extractor.py`, `hybrid_engine.py`, `parser_engine.py`, `app.py`, new shared document-text service, focused extraction tests.
- **Estimated fix complexity:** Medium
- **Suggested order:** 1
- **Acceptance test:** With no API key, upload the ten audit invoices. Every supported file must produce a stored extraction record rather than a processing error. Native PDFs must use embedded text when present; scans and images must use local OCR. Each record must preserve its extraction method and enter either ready or review—not error—unless the file is genuinely unreadable.

## ALPHA-B02 — Review data population and safe approval

- **Severity:** Critical
- **Root cause:** Processing errors are included in the ordinary review queue, where empty `document` data renders blank fields and still exposes the approval action. Local fallback data is not currently populated because Feed never invokes the hybrid path.
- **Files involved:** `daily_intake.py`, `hybrid_engine.py`, `review_form.py`, review-flow tests.
- **Estimated fix complexity:** Medium
- **Suggested order:** 2
- **Acceptance test:** Open every invoice from the ten-file batch. Successfully extracted fields must appear in review. A record without the minimum supported business data must show recovery actions and must not expose an enabled “Approve & Teach Barni” action. At least one representative invoice must be safely approvable and immediately update the canonical lifecycle.

## ALPHA-B03 — Processing progress visibility

- **Severity:** High
- **Root cause:** Progress callbacks describe generic stages but do not identify the current file or `n of total`. Long batches therefore appear stalled, and the final completion language can imply learning even when every file failed.
- **Files involved:** `daily_intake.py` and UI-focused tests.
- **Estimated fix complexity:** Small
- **Suggested order:** 3
- **Acceptance test:** Process a ten-file batch. The running UI must show the current file, completed count, total count, and outcome counts. Completion copy must distinguish successful reads from invoices needing help and must never say Barni learned when zero documents were read.

## ALPHA-B04 — Search reliability

- **Severity:** Critical
- **Root cause:** Static English suggestions are unrelated to the current restaurant's stored suppliers and products. Supplier grouping compares raw supplier text after canonical matching, which can hide valid canonical results. Product discovery depends on an already-filtered invoice result set and provides no recovery path when suggestions miss.
- **Files involved:** `smart_archive.py`, `database.py`, Business Identity/Search data adapters, Search tests.
- **Estimated fix complexity:** Medium
- **Suggested order:** 4
- **Acceptance test:** Using displayed stored values, search by canonical supplier, supplier alias, product, product alias, invoice number, and date in Hebrew and English where data exists. Summaries must match results, exact invoice matches must rank first, and every displayed source invoice must open. Every clickable suggestion must return at least one result.

## ALPHA-B05 — Accountant export and readiness

- **Severity:** Critical
- **Root cause:** Package creation references JSON serialization without importing its module. Readiness checks render positive labels even when they fail, and month-scoped readiness is presented beside broader unresolved counts without clear scope.
- **Files involved:** `services/accountant_workspace.py`, `ui/accountant_workspace.py`, accountant tests.
- **Estimated fix complexity:** Small
- **Suggested order:** 5
- **Acceptance test:** Select a real accounting month, prepare the package, download/open the ZIP, and verify `summary.csv`, `summary.pdf`, `metadata.json`, and every expected source invoice. UI checks must never say “No duplicate invoices” when duplicates exist; the selected month and blocking scope must be explicit.

## ALPHA-B06 — Business Memory drill-down

- **Severity:** High
- **Root cause:** Business Memory exposes counts, charts, and recent learning but no direct customer path into supplier history, product history, or trusted price history. Data exists in canonical Identity, invoice items, and the Comparable Price Ledger, but the page stops at overview metrics.
- **Files involved:** `services/business_memory.py`, `ui/business_memory.py`, existing Search/detail navigation, memory tests.
- **Estimated fix complexity:** Medium
- **Suggested order:** 6
- **Acceptance test:** From Business Memory, open a real supplier, see its invoices, open a real product, see its purchase and trusted price history, follow evidence to the source invoice, and return without losing context. Counts must use canonical identity definitions consistently.

## Pilot completion gate

The pilot is complete only when a fresh customer session can:

1. Upload ten representative restaurant invoices.
2. See understandable progress.
3. Review populated data and safely approve each valid invoice.
4. See Home and Business Memory update immediately.
5. Find approved invoices by supplier, product, invoice number, and date.
6. Open source evidence.
7. Understand at least one evidence-backed change when real history supports it.
8. Produce and inspect the accountant package.

Any processing crash, unsafe blank approval, contradictory status/count, unsupported conclusion, broken evidence link, or failed export keeps Alpha blocked.

## Execution record — 9 August 2026

| ID | Implementation result | Runtime verification |
|---|---|---|
| ALPHA-B01 | Feed now uses byte-verified approved evidence for exact repeats and the existing hybrid/local OCR path when no approved source matches. External AI configuration is optional rather than a hard failure. | The audit batch changed from 10/10 processing errors to 10/10 invoices read. |
| ALPHA-B02 | Review uses populated structured evidence. Approval is disabled when supplier, date, total, document type, or required product evidence is missing. Saved corrections are revalidated instead of being marked ready unconditionally. | The first audit invoice opened with supplier, date, number, total, and 11 products populated. Its approval control was enabled because minimum evidence existed. Blank-review tests confirm unsafe approval is blocked. |
| ALPHA-B03 | Processing reports current file, completed count, total count, and stage. Completion language distinguishes successful reading from complete failure. | Ten-file processing completed with a `10 invoices read` summary and meaningful supplier/product/price-point counts. |
| ALPHA-B04 | Suggestions now come from canonical products and stored suppliers. Canonical product names participate in grouped product matches, and supplier group counts use supplier-aware search. | A real supplier suggestion returned its invoice and supplier group. A real product suggestion returned one purchase, its invoice, latest price, and supplier. Invoice-number Search and source opening remained functional. |
| ALPHA-B05 | Accountant package JSON serialization is restored. Readiness checks now state the actual failed condition and selected month explicitly. | A July package was prepared successfully with a Download action. Independent ZIP inspection confirmed Summary CSV, Summary PDF, Metadata JSON, and all 34 expected invoice files. |
| ALPHA-B06 | Business Memory now offers canonical supplier history and product/price history with source-invoice navigation. Products with trusted ledger observations are prioritized. Insights uses the same canonical supplier count. | Supplier history displayed a dated invoice. Product history exposed source invoice 11, and the source action opened the correct approved invoice in Search detail. |

### Remaining customer decision

The ten audit files are byte-identical to invoices already approved in Business Memory. Barni correctly detected them as duplicates. Completing their review requires the restaurant owner to choose **Replace**, **Keep both**, or **Skip duplicate** after comparing evidence. No automatic choice was made because duplicate resolution is a consequential business decision.

The product path is operational, but this particular ten-file rerun cannot be declared independently completed until the owner makes those duplicate decisions or supplies ten genuinely new pilot invoices.
