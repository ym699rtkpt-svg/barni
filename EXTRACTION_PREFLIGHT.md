# BAR-INFRA-002 — Extraction Preflight

## Purpose

Barni checks extraction configuration before showing the landing page or accepting an invoice. A restaurant owner can no longer reach upload and discover only afterward that the extraction service was not configured.

The preflight changes startup availability only. It does not change OCR, extraction, invoice, approval, or Business Memory logic.

## What is checked

The shared extraction preflight checks only whether the running process contains a non-empty environment variable named:

```text
OPENAI_API_KEY
```

It does not:

- print the credential;
- log the credential;
- validate or transmit the credential;
- store it in Streamlit session state;
- write it to a file or database;
- reveal any part of its value.

The startup preflight and production extractor use the same check, preventing them from disagreeing about whether configuration is present.

## When it is checked

The check runs on every Streamlit script execution immediately after page configuration and global styles, before:

- the landing page;
- customer navigation;
- Feed Barni;
- invoice upload;
- OCR or extraction.

Streamlit may rerun the script during normal interaction. The check remains fail-closed on every rerun. The READY confirmation is shown only once per browser session to avoid noise.

## Startup states

### Configured

Barni shows:

> 🟢 Extraction Service Ready

The confirmation appears unobtrusively once, and the existing landing page and application continue normally.

### Not configured

Barni shows:

> 🔴 Extraction Service Not Configured

The application stops before the landing page and upload workflow. The screen explains that `OPENAI_API_KEY` must be configured in the same terminal, IDE, or process environment used to start Streamlit, and that Barni must then be restarted.

No business data is changed while startup is blocked.

## Expected operator action

1. Stop the unconfigured Streamlit process.
2. Configure the credential through the local terminal, IDE launch configuration, process manager, or secure secret manager.
3. Do not put the value in source code, Git, documentation, demo data, or visible terminal output.
4. Start Streamlit again from the configured environment.
5. Confirm the application reports `🟢 Extraction Service Ready`.

For an interactive zsh session, the preflight screen provides this value-hidden setup pattern:

```bash
read -s "OPENAI_API_KEY?OpenAI API key: "
export OPENAI_API_KEY
printf '\n'
.venv/bin/streamlit run app.py
```

Entering the value into `read -s` prevents it from being echoed. The environment variable lasts for that shell session. Operators using an IDE or process manager should configure the same variable in that launcher instead.

## Expected customer experience

The restaurant owner should receive the application only after the operator sees the READY state.

When correctly configured:

- startup continues normally;
- the READY message appears once;
- upload and extraction behavior remain unchanged.

When incorrectly configured:

- the customer cannot upload an invoice into a known-broken extraction environment;
- no document is accepted and then unexpectedly downgraded because of missing configuration;
- the operator sees one precise recovery action before handing over the application.

## Verification

Focused automated tests cover:

- present credential → ready;
- missing credential → not configured;
- blank credential → not configured.

Runtime verification should exercise both startup states without exposing a real credential value. A non-secret placeholder is sufficient to verify that the READY branch renders; it does not validate external API connectivity or replace the five-invoice live extraction acceptance gate.
