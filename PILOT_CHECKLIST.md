# Restaurant #1 — Pre-Pilot Checklist

Date: __________  Operator: __________  Restaurant: __________

## Release

- [ ] `git rev-parse HEAD` = `0a86cc5848e578ce0d37eaa9a92ff5b6dd33e5b2`
- [ ] `git describe --exact-match --tags HEAD` = `barni-alpha-rc2`
- [ ] `git status --porcelain` returns nothing
- [ ] No code, dependency, configuration, or workflow change is planned during the session

## Environment

- [ ] Correct pilot machine, power, network, browser, and charger are ready
- [ ] Pilot workspace is known and is not `.barni-demo/`
- [ ] Extraction preflight shows `🟢 Extraction Service Ready`
- [ ] Credential value is not visible in terminal history, notes, screenshots, or source
- [ ] Barni opens at the expected local URL and survives one controlled restart

## Verification

- [ ] `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q` passes
- [ ] `.venv/bin/python demo_environment.py verify` passes
- [ ] Landing → Home → Feed → Review opens without an exception
- [ ] Search finds seeded product, supplier, and invoice examples
- [ ] Business Memory shows supplier, product, price history, and evidence
- [ ] Accountant package builds and includes expected source documents

## Pilot Materials

- [ ] Five representative invoices are available with owner consent
- [ ] PDF, photo, Hebrew, mixed-language, and review-likely examples are included where available
- [ ] Observation notes and [PILOT_RETROSPECTIVE_TEMPLATE.md](PILOT_RETROSPECTIVE_TEMPLATE.md) are open
- [ ] Screen capture or photography consent is explicit; otherwise recording is off
- [ ] Operator will not coach, edit data, approve decisions, or promise fixes

## Recovery and End State

- [ ] Relaunch command, data directory, and responsible operator are known
- [ ] Operator knows to pause rather than guess if revision or workspace is uncertain
- [ ] Final counts, Search, Business Memory, and export will be verified before shutdown
- [ ] Restaurant data will be preserved; no reset or deletion will run after the session

**Pilot may begin only when every box is checked.**
