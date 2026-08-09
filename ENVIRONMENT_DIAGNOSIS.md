# ALPHA-GO-02 — Environment Diagnosis

## Root cause

The running Streamlit process was launched without `OPENAI_API_KEY` in its process environment.

Presence-only verification of the process listening on `127.0.0.1:8511` returned:

> Running Streamlit extraction credential: NOT CONFIGURED

The process is running from the correct project directory with the expected application command:

```text
.venv/bin/streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8511 --browser.gatherUsageStats false
```

This is not a wrong-directory problem, wrong-Python problem, or alternate application entry point. The credential was absent from the environment inherited by that process when it started.

The application does not load `.env` files and does not read `st.secrets`. It reads `OPENAI_API_KEY` directly from `os.environ`. Therefore, creating `.env` or `.streamlit/secrets.toml` alone would not configure the current implementation.

## Where the application expects the credential

The production extraction path is:

```text
Feed upload
→ daily_intake.process_files
→ hybrid_engine.extract_hybrid
→ ai_extractor.extract_with_ai
→ OpenAI client
```

`ai_extractor.extract_with_ai` performs an explicit check equivalent to:

```python
os.environ.get("OPENAI_API_KEY")
```

If that value is absent or empty, it raises a missing-configuration error before constructing the OpenAI client.

The OpenAI model is selected separately from:

```text
INVOICE_AI_MODEL
```

when provided, otherwise the application uses its configured default model. The model variable does not replace the API credential.

## How configuration is currently loaded

Configuration is inherited from the operating-system environment of the process that starts Streamlit.

### Normal startup

The documented startup command is:

```bash
streamlit run app.py
```

This command inherits exported variables from the terminal, IDE launch configuration, process manager, or parent process. It does not load a project configuration file first.

### Demo startup

The demo launcher creates a child environment by copying its own environment and then adds only `BARNI_DATA_ROOT`:

```text
parent shell environment
→ copied into demo Streamlit environment
→ BARNI_DATA_ROOT set to .barni-demo
```

Therefore, `demo_environment.py start` will pass through `OPENAI_API_KEY` when it is already exported in the parent environment. It does not create, discover, or load that credential.

## Current configuration

Verified state:

| Configuration source | State | Used by extraction? |
|---|---|---|
| Running Streamlit process environment | `OPENAI_API_KEY` absent | Yes; this is the authoritative source |
| Current diagnostic shell environment | `OPENAI_API_KEY` absent | Yes, for processes launched from that shell |
| `.env` | Absent | No automatic loader exists |
| `.env.local` | Absent | No automatic loader exists |
| `.streamlit/secrets.toml` | Absent | Application does not read `st.secrets` |
| `.streamlit/config.toml` | Present; visual theme only | No |
| `requirements.txt` | No `python-dotenv` dependency | Confirms `.env` is not automatically loaded |

No secret value was read, printed, logged, or stored during this diagnosis. Only presence or absence was checked.

## Is a `.env` file expected?

No.

There is no `load_dotenv` call and no dotenv dependency. Python and Streamlit do not automatically copy values from `.env` into `os.environ` in this project.

A `.env` file would be ignored unless an external launch tool explicitly loads it before starting Streamlit. Relying on such implicit IDE behavior would make terminal and demo startup inconsistent.

## Is an environment variable expected?

Yes.

The current implementation explicitly requires a non-empty process environment variable named:

```text
OPENAI_API_KEY
```

It must exist before the Streamlit process starts. Adding it to a terminal after Streamlit is already running will not update the existing process; Streamlit must be stopped and restarted from the configured environment.

## Does startup differ from test execution?

Yes, in what is exercised—not in how Python environment variables work.

The automated suite passes without `OPENAI_API_KEY` because it primarily verifies:

- local parsing;
- lifecycle transitions;
- safe OCR timeout and upload recovery;
- seeded or constructed invoice documents;
- Search, Business Memory, evidence, and export behavior;
- fallback behavior when live AI extraction is unavailable.

The hybrid extractor catches the missing live extraction error and returns a local-parser fallback for review. As a result, absence of the credential does not necessarily fail the application or the regression suite. It reduces structured extraction quality and routes the invoice into review.

The tests do not constitute a credential-enabled live extraction acceptance run. A passing test suite therefore does not prove that the running Streamlit process can reach the extraction service.

## Is the application reading the wrong configuration?

No. It is reading the configuration source implemented by the application: `os.environ`.

The failure is a mismatch between launch expectations and launch configuration:

- The application expects an exported environment variable.
- The process was started without that variable.
- The README documents starting Streamlit but does not document configuring the extraction credential first.
- Neither `.env` nor Streamlit secrets are part of the implemented configuration path.

The demo launcher is also behaving correctly: it preserves variables from its parent environment, but its parent environment did not contain the credential.

## Required configuration

Configure `OPENAI_API_KEY` in the same local environment that launches Streamlit.

Acceptable configuration owners include:

- an exported variable in the launch terminal;
- an IDE run configuration that injects the variable into the Streamlit process;
- a local process manager or deployment service environment;
- a secure local secret manager that exports the variable before launch.

The value must not be committed to Git, placed in source code, added to documentation, printed during verification, or copied into demo seed data.

## Exact steps required to reach PASS

### 1. Stop the existing Streamlit process

Stop the process currently listening on port `8511`. Configuration changes cannot be injected into an already-running process.

### 2. Configure the credential in the launch environment

In zsh, a presence-safe interactive option is:

```bash
read -s "OPENAI_API_KEY?OpenAI API key: "
export OPENAI_API_KEY
printf '\n'
```

This avoids placing the value directly in the command text. The variable lasts for that shell session. Alternatively, configure the same variable through the IDE or process manager used for the pilot.

### 3. Verify presence without printing the value

```bash
.venv/bin/python -c 'import os; print("Extraction service: READY" if bool(os.environ.get("OPENAI_API_KEY", "").strip()) else "Extraction service: NOT CONFIGURED")'
```

Required result:

```text
Extraction service: READY
```

### 4. Start Barni from that same environment

Normal customer data:

```bash
.venv/bin/streamlit run app.py
```

Isolated demo data:

```bash
.venv/bin/python demo_environment.py start
```

Do not start Streamlit from a different terminal, IDE action, or background launcher unless that launcher has the same variable configured.

### 5. Verify the running process inherited the credential

Determine the listening process ID without printing its environment:

```bash
pid=$(lsof -tiTCP:8501 -sTCP:LISTEN)
```

Then perform a presence-only check:

```bash
ps eww -p "$pid" -o command= | awk '{ ready=0; for (i=1; i<=NF; i++) if ($i ~ /^OPENAI_API_KEY=./) ready=1 } END { print ready ? "Extraction service: READY" : "Extraction service: NOT CONFIGURED" }'
```

If Barni uses a different port, substitute that port in the `lsof` command. Do not run or share an unfiltered `ps eww` output because process environments can contain secrets.

### 6. Run the live acceptance gate

Only after the running-process check reports `READY`, process the five representative invoices through the real upload and extraction path. The ALPHA-GO-01 acceptance and restart checks remain required before the Thursday pilot can move from NO-GO.

## PASS definition

Environment diagnosis reaches PASS when both checks report `READY`:

1. The shell or launch environment immediately before startup.
2. The actual running Streamlit process after startup.

At that point the environment blocker is resolved. Product readiness still depends on the five-invoice live extraction, approval, persistence, Search, Business Memory, and accountant export acceptance results.
