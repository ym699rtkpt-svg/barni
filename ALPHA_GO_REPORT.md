# ALPHA-GO-03 — Live Five-Invoice Acceptance Report

## Decision

- **Current Demo Readiness: 94/100**
- **Current Risk: 10/100**
- **Thursday Pilot: GO**

## Exact evidence

The configured extraction preflight on the isolated acceptance application at `127.0.0.1:8515` passed. Five representative source documents then entered the real Upload → extraction → Review → Approve → Business Memory → Search → Accountant flow. No seeded approvals or fallback extraction were used.

| Case | Source preserved | Extracted result | Manual correction | Observed processing time | Recovery |
|---|---|---|---|---:|---|
| Clear Hebrew PDF — Invoice 841 | YES | Supplier `מיכל עלים בגבעה`; 2026-07-31; #841; ₪1,043.35; `חשבונית מס`; 1 product | None to core fields. Review flagged an inconsistent extracted tax breakdown. | 5 sec | None |
| Photographed invoice — 01/008273 | YES | Date 2026-07-12; #01/008273; ₪1,770.00; `חשבונית מס`; supplier and product missing | Supplier and one source-supported service line entered. Tax breakdown remained flagged for review. | 5 sec | Safe review state |
| Hebrew PDF — Invoice 781 | YES | Supplier `בבאיי משה`; 2026-07-27; #781; ₪3,304.00; `חשבונית מס`; 1 product; totals valid | None | 49 sec end-to-end observed | None |
| Mixed Hebrew/English PDF — SI266000634 | YES | Supplier `עין גב אחזקות - אגודה שיתופית חקלאית`; 2026-06-30; #SI266000634; ₪7,469.40; `חשבונית מס`; totals valid; product missing | One source-supported service line entered | 19 sec | Safe review state |
| Multi-line account statement | YES | Supplier `עלה עלה בע"מ`; 2026-06-01; no invoice number; ₪1,790.33; `ריכוז חשבון`; 44 price lines / 39 learned products | None; missing invoice number was explicitly surfaced | 70 sec | Safe review state |

## Acceptance thresholds

| Threshold | Result |
|---|---|
| 5/5 source files preserved | **PASS** — five original files exist in the isolated archive |
| 5/5 reach review or safe recovery | **PASS** |
| At least 4/5 have usable core-field extraction | **PASS — 4/5**; the photographed invoice required supplier correction |
| Zero unhandled customer-facing exceptions | **PASS** |
| Every approved invoice updates Business Memory | **PASS** — final memory: 5 invoices, 5 suppliers, 43 products |
| Search finds every approved invoice | **PASS** — each invoice was found immediately after approval, including the document with no invoice number via supplier |
| Accountant ZIP contains expected sources | **PASS** — July package: 3/3 sources; June package: 2/2 sources; both include summary CSV, summary PDF, and metadata JSON; zero missing files |

## Restart Persistence — PASS

Barni was stopped and relaunched against the original isolated five-invoice acceptance workspace. No invoice was re-uploaded, re-extracted, reseeded, or re-approved during restart validation.

After relaunch:

- Home reported 5 Approved, 0 Pending Review, 0 Learning, 0 Needs Attention, and 0 Duplicates.
- Search found #841, #01/008273, #781, #SI266000634, and the invoice without a number through supplier `עלה עלה בע"מ`.
- Business Memory reported 5 invoices, 5 suppliers, and 43 products.
- July Accountant Workspace reported 3 documents, 0 missing sources, and Ready for accountant.
- The independently rebuilt July package contained all three July sources; the June package contained both June sources.

The restart process used a presence-only local preflight value because extraction was not part of restart validation. No credential value was read from, copied from, or exposed by the original acceptance process, and no extraction request was made during this gate.

## Final release status

All P0 acceptance thresholds and the restart persistence gate pass. The release candidate is approved for the first controlled restaurant pilot once the reviewed working tree is frozen as the `barni-alpha-rc2` artifact and the isolated demo verifies from that exact revision.

The remaining risks are non-blocking: live core extraction was usable without core-field correction for 4/5 representative documents rather than 5/5; manual review remains necessary for difficult photographs and missing product lines; and the test suite continues to emit non-failing SQLite connection warnings.
