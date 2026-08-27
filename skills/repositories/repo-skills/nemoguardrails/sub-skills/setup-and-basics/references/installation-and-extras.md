# Installation and extras

## Python support

NeMo Guardrails declares support for Python `>=3.10,<3.14`:

- Supported interpreter families: 3.10, 3.11, 3.12, 3.13.
- Use `python --version` and `python -m pip --version` to ensure `pip` belongs to the intended interpreter.
- If an optional extra does not resolve on Python 3.13, retry on Python 3.10-3.12 when the extra depends on packages that publish wheels only for older versions.

## Public install patterns

Prefer a clean virtual environment and install only the feature groups needed for the task.

```bash
python -m pip install --upgrade pip
python -m pip install nemoguardrails
python -m pip check
python -m nemoguardrails --help
```

Install targeted extras by quoting the requirement so the shell does not interpret brackets:

```bash
python -m pip install 'nemoguardrails[server]'
python -m pip install 'nemoguardrails[eval]'
python -m pip install 'nemoguardrails[server,tracing]'
```

Use `python -m nemoguardrails ...` as the most robust CLI form. The `nemoguardrails` console command should also be installed, but it can be missing or stale if entry points were created by a different environment.

## Extras matrix

| Extra | Adds | Install when | Cautions |
| --- | --- | --- | --- |
| base package | Core Guardrails APIs, config loading, CLI shell, FastEmbed dependency, Typer/Rich, HTTP utilities | Import checks, config parsing, local scripts that do not start the API server | Base install is not proof that every built-in rail/provider is available. Avoid live generation during install verification. |
| `server` | FastAPI, Starlette, Uvicorn, OpenAI client, file watching, async file support | Starting `nemoguardrails server`, actions server, OpenAI-compatible HTTP endpoints, server schema smokes | Missing this extra commonly surfaces as a server-start ImportError. Installing it does not provide provider credentials. |
| `eval` | Streamlit, pandas, tqdm, Tornado and numeric dependencies | `nemoguardrails eval ...` commands, eval UI, evaluation data processing | Eval workflows may later call live models or judges depending on config; install verification should stop at help/import checks. |
| `tracing` | OpenTelemetry API and async file support | User-configured tracing/exporter setup and local tracing import checks | Tracing is separate from anonymous package telemetry; exporter endpoints and credentials are still user-managed. |
| `chat-ui` | Chainlit | Chat UI mounting with the server | UI dependencies can be larger and may have web-server/runtime constraints. Do not install just to do a basic import check. |
| `sdd` | Presidio analyzer/anonymizer on Python versions where those dependencies apply | Sensitive data detection and masking rails | The dependency markers exclude some newer Python versions. Prefer Python 3.10-3.12 if SDD packages are needed and do not resolve. Some Presidio/spaCy language models may require separate setup. |
| `jailbreak` | `yara-python` | Jailbreak detection rails that use YARA rules | Native wheels may be platform-sensitive. If unavailable, route the user to either install platform build prerequisites or choose a different rail. |
| `multilingual` | `fast-langdetect` | Multilingual/language-detection rails | Import check is safe; production behavior still depends on chosen rail config. |
| `gcp` | Google Cloud Natural Language client | Google Cloud moderation rails | Requires separate Google Cloud credentials/project configuration at runtime. Do not treat install success as an authenticated smoke. |
| `all` | Published optional dependencies listed above | Disposable exploration environments or when a task truly spans many extras | Avoid as the default. It increases resolver size and can pull UI, eval, GCP, server, and native packages that are irrelevant to a small task. It still does not provide every third-party provider SDK or any credentials. |

LangChain integration is optional but is not a package extra in this distribution. Install the LangChain packages needed by the chosen workflow separately, then route execution details to `../../run-rails/references/integrations.md`.

## No-live-provider verification sequence

Run these before asking users for API keys or starting any live model workflow:

```bash
python --version
python -m pip show nemoguardrails
python -m pip check
python -m nemoguardrails --version
python -m nemoguardrails --help
python sub-skills/setup-and-basics/scripts/check_install.py
```

A successful sequence proves:

- The interpreter is in the supported range.
- The package metadata and top-level imports are visible.
- Required dependencies for the installed extras do not have broken version requirements.
- CLI module dispatch can render help without starting chat, server, eval, or provider calls.

It does **not** prove:

- A guardrails configuration is valid.
- A provider API key, endpoint, model name, or deployment is correct.
- Built-in rails that need optional services/models are usable.
- FastEmbed/Hugging Face caches are warm for workflows that instantiate embeddings.
