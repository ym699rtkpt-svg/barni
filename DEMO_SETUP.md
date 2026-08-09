# Barni Demo Environment

The demo environment is an isolated, reproducible business named **Cedar Table Demo Restaurant**. It uses the same invoice lifecycle, Business Memory, Search, Business Facts, and accountant export services as the customer product.

Demo data lives only in `.barni-demo/` inside the project. Normal Barni data is not read, changed, or reset.

## Seeded Scenario

Each reset creates:

- 3 suppliers.
- 5 approved invoices in the current accounting month.
- 7 products across food, dairy, and kitchen operations.
- Repeat purchases from two known suppliers.
- Olive Oil increasing from ₪42.00 to ₪48.00 per unit (+14.3%).
- Milk 3% increasing from ₪7.90 to ₪8.30 per unit.
- A newly learned supplier: Galilee Kitchen Supply.
- One unresolved duplicate invoice.
- One recoverable failed-reading example.
- Source PDFs and evidence links for every approved invoice.

The duplicate and failed-reading examples intentionally keep the demo workflow in a “needs attention” state until they are resolved. Reset restores them after any review.

## Reset Demo

From the project root, run the one reset command:

```bash
.venv/bin/python demo_environment.py reset
```

This command deletes only `.barni-demo/`, rebuilds the database and evidence files, runs all migrations, seeds through the canonical approval workflow, and verifies the result.

Never point `BARNI_DATA_ROOT` at customer data when resetting the demo. The reset command always targets the repository’s dedicated `.barni-demo/` directory and refuses any other path.

## Start Demo Mode

```bash
.venv/bin/python demo_environment.py start
```

To use another port:

```bash
.venv/bin/python demo_environment.py start --port 8510
```

The start command verifies the demo before launching Streamlit. If demo data does not exist, it creates and verifies it first.

## Verify Demo

Run the automated demo contract:

```bash
.venv/bin/python demo_environment.py verify
```

Verification checks:

- 5 approved invoices are stored.
- 3 canonical suppliers and at least 7 canonical products exist.
- The duplicate and failed-reading examples appear in the shared workflow.
- Search finds Olive Oil and Fresh Fields Produce.
- The trusted price ledger explains the 14.3% Olive Oil increase.
- All five approved invoices appear in the seeded accounting month.
- The accountant package builds successfully.
- Every approved invoice still resolves to a source evidence file.

## Product Review Walkthrough

1. Open **Feed Barni**. Confirm the duplicate and failed-reading examples need attention.
2. Open **Search Invoices** and search for:
   - `Olive Oil`
   - `Fresh Fields Produce`
   - `FF-1002`
3. Open **Business Memory**. Confirm supplier, product, and price history are populated.
4. Open the latest Fresh Fields invoice and verify the price evidence links to both purchases.
5. Open **Accountant Workspace**. Select the seeded month shown by `verify`.
6. Confirm the unresolved demo examples are clearly reported.
7. Prepare the accountant package and confirm the download becomes available.
8. Run the reset command and repeat the walkthrough from the original state.

## Full Regression Suite

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q
```

The demo environment does not require an OpenAI credential because it seeds already-reviewed evidence through Barni’s existing trusted lifecycle. Live upload and extraction still require the normal demo-machine configuration.
