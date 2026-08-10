# Restaurant #1 — Pilot Learning Plan

## Purpose

Restaurant #1 is a learning pilot, not a sales demonstration. Its purpose is to determine whether a restaurant owner can use Barni's core workflow independently, trust what Barni remembers, and recognize enough value to use it again.

Use this plan with:

- `PILOT_GUIDE.md` during the session.
- `PILOT_CHECKLIST.md` before the session.
- `PILOT_RETROSPECTIVE_TEMPLATE.md` immediately after the session.

## 1. Objectives

We are trying to learn:

1. Whether the owner understands what Barni is without an explanation.
2. Whether uploading, reviewing, correcting, and approving an invoice feels like one continuous workflow.
3. Whether the owner understands what Barni learned after approval.
4. Whether the owner trusts Search to recover a remembered supplier, product, or invoice.
5. Whether Business Memory feels like useful business knowledge rather than stored documents.
6. Whether evidence and original invoices make Barni's conclusions trustworthy.
7. Whether recovery states allow the owner to continue without operator intervention.
8. Whether Accountant Workspace solves a recognizable monthly task.
9. Which parts of the product create value without prompting.
10. Which visible features, language, or steps add effort without helping the owner decide or act.

The pilot is not intended to validate future AI, predictions, automated actions, broad analytics, or feature demand outside the current Alpha workflow.

## 2. Success Metrics

Measure from the moment the owner receives control of the product. Do not exclude waiting, confusion, corrections, or recovery time.

| Metric | How to measure | Restaurant #1 success signal |
|---|---|---|
| Time to first invoice | Start at `Enter Barni`; stop when the first source reaches Review or a safe recovery state | 2 minutes or less |
| Time to finish morning workflow | Start at `Enter Barni`; stop when today's invoices are approved or intentionally deferred and the owner understands the final state | 5 minutes or less for the agreed pilot batch |
| Number of questions asked | Count every product-use question directed to the operator; exclude conversation about the restaurant itself | 3 or fewer, with no question required to discover the primary action |
| Places where the owner hesitated | Record every pause longer than 5 seconds, including step and visible state | No Critical hesitation; no repeated hesitation at the same step |
| Features ignored | Record visible controls or sections never examined or used | Ignored elements do not obstruct the primary workflow; repeated avoidance becomes a simplification candidate |
| Features loved | Record spontaneous positive reaction, voluntary return, or owner-described value | At least one unprompted moment tied to Search, learned memory, evidence, insight, or export |

Also record:

- Invoices attempted, approved, corrected, deferred, duplicated, and recovered.
- Manual corrections per invoice.
- Unhandled errors and operator interventions.
- Whether the owner can find the newly approved invoice without help.
- Whether the owner can explain one thing Barni learned.
- Whether the owner would use Barni again during a normal workday.

Metrics describe what happened. They do not override observed loss of trust.

## 3. Observation Rules

Watch without interrupting:

- Where the owner's eyes and cursor go first on each screen.
- Whether the primary action is understood without reading every section.
- Words the owner rereads, questions, or interprets incorrectly.
- Whether waiting states make progress and safety clear.
- Whether the owner checks the original invoice before approving.
- Which extracted fields the owner verifies first.
- Whether uncertainty feels honest or alarming.
- Whether completion feedback explains what changed.
- The owner's natural Search language and whether the first query succeeds.
- Whether the owner distinguishes Search results, Business Memory, and Insights.
- Whether evidence is opened voluntarily or only after doubt appears.
- Whether the owner notices unresolved work and understands how to continue later.
- Which features are skipped without affecting task completion.
- Spontaneous reactions: relief, confidence, surprise, doubt, frustration, or delight.

Operator rules:

1. Do not explain a screen before the owner attempts it.
2. Allow at least five seconds of hesitation before asking, “What are you looking for?”
3. Ask what the owner expected; do not tell them what the product intended.
4. Do not take control of the mouse or keyboard unless continuing would risk data or privacy.
5. Do not correct, approve, reject, merge, skip, or resolve an invoice for the owner.
6. Do not defend wording or implementation.
7. Record exact quotes and observable behavior separately from interpretation.
8. Do not propose solutions during the session.
9. Do not collect sensitive invoice content in general observation notes.
10. Record every intervention; assisted completion is not independent completion.

## 4. Questions for Sunday

Ask after the owner has completed the workflow. Do not lead with feature names or suggest the desired answer.

1. In your own words, what does Barni do for your business?
2. At which point, if any, did Barni first feel useful?
3. What did you expect to happen after approving an invoice?
4. Which result did you trust least, and what would have helped you trust it?
5. If you opened Barni tomorrow morning, what would you expect it to show first?
6. What would you naturally search for during a normal restaurant day?
7. Did Business Memory tell you something useful, or did it feel like stored paperwork? Why?
8. Which step felt slower or more complicated than the way you work today?
9. Which part could disappear without reducing the value you received?
10. Would you use Barni again next week? What specific outcome would bring you back?

## 5. Decision Matrix

Classify every finding using evidence from observation, metrics, owner quotes, and task outcome.

| Classification | Use when | Required evidence | Action |
|---|---|---|---|
| Fix before Restaurant #2 | The issue blocks the core workflow, risks data or trust, causes an unsupported conclusion, requires operator rescue, or prevents the owner from recognizing core value | Reproducible failure, Critical/High hesitation, incorrect business outcome, or assisted completion of a required step | Assign an owner and acceptance test; Restaurant #2 waits until verified |
| Observe again | The finding may matter but occurred once, has ambiguous cause, depends on this restaurant's habits, or conflicts with another observation | Exact observation and a defined question to test with Restaurant #2 | Change nothing yet; add a targeted observation to the next learning plan |
| Nice to have | The idea could improve convenience or delight but does not affect task completion, trust, evidence, or return intent | Owner request or observed opportunity with no current workflow harm | Add to the post-Alpha opportunity list; do not interrupt pilot hardening |
| Ignore | The finding lacks evidence, concerns unsupported future scope, reflects operator preference only, duplicates an existing solution, or does not improve understanding or effort | Reason for exclusion recorded | Close it; do not add it to the roadmap |

Classification rules:

- Severity and customer impact outrank implementation effort.
- One strong trust failure can outweigh otherwise successful timing metrics.
- Do not promote a requested feature without identifying the underlying job.
- Do not generalize a single preference into a product rule; use `Observe again`.
- Every `Fix before Restaurant #2` item needs a measurable acceptance test.
- Silence and unused functionality are not automatically problems. Classify only when they affect value or effort.

## 6. Exit Criteria

Restaurant #1 is successful only when all mandatory criteria pass:

### Independent workflow

- The owner uploads at least one real invoice through the normal workflow.
- The invoice reaches Review or a clear safe-recovery state.
- The owner completes necessary corrections and approves, or deliberately defers with a correct understanding of the consequence.
- No unhandled customer-facing exception occurs.
- No operator action is required to preserve data or finish a mandatory step.

### Immediate trust and value

- The approved invoice appears immediately in Search.
- Business Memory reflects the approved invoice.
- The owner can open the original source and understands that it is evidence for Barni's stored information.
- Any visible insight is supported by real evidence; unsupported insight remains absent.
- The owner can explain at least one thing Barni learned or noticed.

### Operational completion

- Final workflow counts are consistent across visible pages.
- Accountant Workspace reflects the correct readiness state.
- The session ends without lost or orphaned source files.
- Every operator intervention, recovery event, and deferred invoice is recorded.

### Customer outcome

- The owner completes the agreed morning workflow in 5 minutes or less, excluding only time explicitly paused by the owner for unrelated work.
- There is no unresolved Critical blocker or trust failure.
- The owner identifies at least one genuine moment of value without being prompted toward it.
- The owner says they would use Barni again for a specific business outcome.

### Learning completion

- The retrospective is completed on the same day.
- Every finding is classified as `Fix before Restaurant #2`, `Observe again`, `Nice to have`, or `Ignore`.
- Every release-blocking finding has an owner and acceptance test.
- The team records a clear decision: continue unchanged, continue after fixes, or pause.

If any mandatory criterion fails, the pilot may still produce valuable learning, but Restaurant #1 is not considered successful. The team must not convert a failed criterion into a success by explaining the product, excluding inconvenient time, or doing the owner's work.
