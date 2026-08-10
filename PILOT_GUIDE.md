# Barni Restaurant #1 Pilot Guide

## Purpose

Run one calm, evidence-led session in which the restaurant owner completes Barni's real workflow without coaching from the product team. Observe the experience; do not redesign or repair the product during the session.

Frozen release candidate:

- Tag: `barni-alpha-rc2`
- Commit: `0a86cc5848e578ce0d37eaa9a92ff5b6dd33e5b2`

## Start the Demo Rehearsal

Use the seeded Cedar Table demo only for the operator rehearsal. It is not the restaurant's workspace.

```bash
git rev-parse HEAD
.venv/bin/python demo_environment.py reset
.venv/bin/python demo_environment.py verify
.venv/bin/python demo_environment.py start --port 8510
```

The revision must match the frozen commit above. Verification must pass every check. Open:

> http://localhost:8510

If startup reports `Extraction Service Not Configured`, stop Barni, configure `OPENAI_API_KEY` in the same terminal that launches it, and start again. Never display, paste into chat, photograph, log, or commit the credential.

## Verify the Pilot Is Ready

Before the owner arrives:

1. Complete [PILOT_CHECKLIST.md](PILOT_CHECKLIST.md).
2. Confirm the frozen revision and a clean working tree.
3. Confirm the extraction preflight is green.
4. Run the automated tests and demo verification.
5. Rehearse Landing → Feed → Review → Search → Business Memory → Accountant Workspace.
6. Confirm the actual pilot workspace is separate from `.barni-demo/`.
7. Confirm the operator knows the exact pilot data directory and recovery command.
8. Keep the pilot checklist, retrospective template, and a timestamped observation note ready.

## What Not to Do During the Pilot

- Do not edit code, configuration, database records, queue files, or source documents.
- Do not pull changes, change branches, switch tags, install packages, or restart into another build.
- Do not run `demo_environment.py reset` against restaurant data. The reset command is for `.barni-demo/` only.
- Do not expose Internal tools, raw logs, stack traces, confidence internals, or the extraction credential.
- Do not approve, correct, merge, reject, skip, or resolve an invoice for the owner.
- Do not explain a screen before the owner has attempted to understand it.
- Do not turn a hesitation into training. Record it as product evidence.
- Do not promise a fix, feature, timeline, or business conclusion during the session.
- Do not photograph or copy invoice contents without explicit consent.

## If Barni Is Accidentally Closed

Stay calm. Approved invoices and uploaded source files are stored locally.

1. Record the time and what the owner was doing.
2. Return to the same terminal and confirm the same `BARNI_DATA_ROOT` and credential environment will be used.
3. Start the same frozen build again with the original launch command.
4. Reopen the same local URL.
5. Verify the shared counters, the last approved invoice in Search, and Business Memory before continuing.
6. Resume from Feed Barni. Use the existing retry or review action; do not upload the same file again unless Barni explicitly confirms the first upload was not retained.

If the workspace, credential environment, or frozen revision cannot be confirmed, pause the pilot. Do not guess.

## Collect Observations

The operator observes silently and records facts, not interpretations.

For every hesitation longer than five seconds, record:

- Timestamp and workflow step.
- What the owner was trying to do.
- What was visible.
- What the owner expected.
- What happened instead.
- Exact owner quote.
- Whether assistance was required.
- Severity: Critical, High, Medium, or Low.

Also record:

- Time to first upload, first review, first approval, first successful Search, first understood insight, and export.
- Every manual correction required.
- Every recovery path or restart.
- Moments of visible trust, doubt, delight, or confusion.
- Evidence references, without copying sensitive invoice contents into general notes.

Do not debate findings during the session. Use [PILOT_RETROSPECTIVE_TEMPLATE.md](PILOT_RETROSPECTIVE_TEMPLATE.md) immediately afterward.

## End the Session

1. Let the owner decide whether to finish or defer any remaining review.
2. Confirm the final shared workflow counts.
3. Search for the newly approved invoice.
4. Confirm Business Memory reflects the approved work.
5. Prepare the accountant package only if the owner requests it; confirm source coverage before download.
6. Record the final state, elapsed time, unresolved work, and any recovery event.
7. Stop Streamlit with `Ctrl+C` in its launch terminal.
8. Preserve the restaurant workspace and observation notes according to the agreed local data policy. Do not reset or delete them.
9. Complete the retrospective before discussing implementation changes.

The session is successful when the owner can explain what Barni learned and what they would do next—without the operator explaining Barni first.
