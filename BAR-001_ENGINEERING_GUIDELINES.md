# BAR-001: Barni Engineering Guidelines

## Purpose

These are the permanent engineering rules for anyone working on Barni. They apply to every feature, fix, refactor, migration, and user-interface change unless a task explicitly states otherwise.

Barni prioritizes reliability over novelty. The product must remain understandable and trustworthy for a non-technical restaurant manager.

## Reliability and Compatibility

1. Never break existing functionality.
2. Preserve all existing database data.
3. Never delete, recreate, reset, or replace the database unless explicitly instructed.
4. Preserve existing business logic unless the task specifically requires changing it.
5. Handle missing, incomplete, malformed, and empty data without crashing the application.
6. Prefer backward-compatible changes when extending existing behavior.

## Data Integrity and Auditability

1. Never invent business conclusions that are not supported by stored data.
2. Important insights and recommendations must be traceable to invoices or other stored data.
3. Treat migrations and data backfills as production operations: make them transactional, repeatable where practical, and safe for existing records.
4. Verify record counts or other integrity signals before and after data-affecting work when practical.
5. Do not hide uncertainty. If the available data is insufficient, communicate that clearly and calmly.

## Code and Architecture

1. Prefer existing helpers, services, and domain functions over duplicating logic.
2. Keep UI logic separate from business logic where practical.
3. Make every code change modular, focused, and easy to review.
4. Prefer clear code over clever code.
5. Avoid unnecessary dependencies.
6. Do not introduce new architecture unless it solves a concrete problem.
7. Keep changes within the requested scope. Avoid unrelated refactors.

## Product and User Experience

1. Barni should prioritize reliability over novelty.
2. Every feature should ideally do at least one of the following:

   - Save time.
   - Save money.
   - Improve confidence in a business decision.

3. The product must remain understandable to a non-technical restaurant manager.
4. Avoid technical wording in user-facing UI.
5. Keep business messages concise, calm, and supported by the available data.

## Verification

1. Run compile checks after every Python change. At minimum, run:

   ```bash
   python3 -m py_compile <changed_file.py>
   ```

2. If runtime behavior is relevant, verify it when practical.
3. Match verification effort to risk. Database, migration, financial, and approval-flow changes require stronger checks than presentation-only changes.
4. Fix all syntax and indentation errors before considering a task complete.
5. Never use destructive database operations as a testing shortcut.

## Task Completion Report

Before finishing any task, summarize:

- Files changed.
- Behavior changed.
- Verification performed.
- Any remaining risk.

