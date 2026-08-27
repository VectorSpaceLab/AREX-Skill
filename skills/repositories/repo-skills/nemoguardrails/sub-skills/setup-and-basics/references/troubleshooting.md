# Setup and install troubleshooting

## Python version mismatch

Symptoms:

- Resolver reports that `nemoguardrails` is not available for the interpreter.
- `pip install` ignores expected wheels or attempts difficult source builds.
- Optional extras resolve on one machine but not another.

Actions:

1. Check `python --version`; use Python `>=3.10,<3.14`.
2. Check `python -m pip --version` and ensure it points to the same environment.
3. Recreate the environment with a supported interpreter rather than forcing unsupported dependencies.
4. For extras with native or version-gated dependencies, prefer Python 3.10-3.12 when Python 3.13 dependency markers prevent installation.

## Broken package install

Symptoms:

- `import nemoguardrails` fails.
- `python -m pip check` reports incompatible dependencies.
- Top-level imports such as `Guardrails`, `LLMRails`, or `RailsConfig` are missing.

Actions:

```bash
python -m pip install --upgrade pip
python -m pip install --force-reinstall nemoguardrails
python -m pip check
python sub-skills/setup-and-basics/scripts/check_install.py
```

If the user intentionally installed extras, reinstall with the same targeted extra list. Avoid switching to `nemoguardrails[all]` unless the task genuinely needs many optional surfaces.

## Missing optional dependency or extra

NeMo Guardrails optional import helpers format missing dependency errors in a task-oriented way. Typical messages include:

- `Missing optional dependency 'PACKAGE'. Install it with pip install PACKAGE or uv add PACKAGE.`
- `Missing optional dependency 'PACKAGE'. Install the NeMo Guardrails extra with pip install 'nemoguardrails[EXTRA]'.`

Actions:

1. Identify which feature the user is trying to use.
2. Install the narrow extra or direct package that owns that feature.
3. Re-run a no-provider import check before retrying live execution.

Examples:

| Symptom | Likely install | Notes |
| --- | --- | --- |
| Server start says server dependencies are missing | `python -m pip install 'nemoguardrails[server]'` | Then retry `python -m nemoguardrails server --help` before starting a live server. |
| Eval UI or eval command import fails | `python -m pip install 'nemoguardrails[eval]'` | Eval execution can still need model/provider credentials later. |
| OpenTelemetry tracing import fails | `python -m pip install 'nemoguardrails[tracing]'` | Exporter-specific packages may be separate from the base tracing extra. |
| Chainlit chat UI missing | `python -m pip install 'nemoguardrails[chat-ui]'` | Server usage may also need `server`. |
| Presidio sensitive-data detection missing | `python -m pip install 'nemoguardrails[sdd]'` | Python version markers may skip Presidio packages on newer interpreters. |
| YARA jailbreak detector missing | `python -m pip install 'nemoguardrails[jailbreak]'` | Native wheels/build prerequisites can be platform-dependent. |
| Language detection missing | `python -m pip install 'nemoguardrails[multilingual]'` | Safe to import-check; actual rails need config. |
| Google Cloud language client missing | `python -m pip install 'nemoguardrails[gcp]'` | Credentials and project settings are separate runtime requirements. |
| LangChain package missing | Install the specific `langchain*` package stack needed by the workflow | LangChain packages are optional framework dependencies, not a published NeMo Guardrails extra in this package metadata. |

When users ask why an ImportError suggests `nemoguardrails[server]` during server startup, answer that the base package can import the CLI, but starting server/action-server requires FastAPI/Uvicorn/OpenAI-client related dependencies from the `server` extra.

## Console command broken, module invocation works

Symptoms:

- `nemoguardrails --help` is missing, points to the wrong interpreter, or has a stale shebang.
- `python -m nemoguardrails --help` works in the active environment.

Actions:

1. Prefer the module form in automation:

   ```bash
   python -m nemoguardrails --help
   python -m nemoguardrails --version
   ```

2. Repair entry points in the environment:

   ```bash
   python -m pip install --force-reinstall --no-deps nemoguardrails
   ```

3. If using an editable or local package install, reinstall the same requirement form that was originally used, then re-run `python -m pip check`.

The module form proves the package is importable even when shell `PATH` or console-script generation is broken.

## FastEmbed and network smoke pitfalls

The base package includes embedding-related dependencies. Import checks are safe, but some guardrails configurations or testing harnesses can instantiate default embedding providers. A naive smoke may then try to download a model or access a cache.

Safe setup checks should avoid:

- Starting interactive chat with a real provider config.
- Calling `generate`/`generate_async` before a fake model and deterministic embeddings plan are in place.
- Treating a Hugging Face/FastEmbed download as part of basic package verification.

Use the bundled `check_install.py` helper for setup verification. For deterministic generation or chat smokes, route to the run-rails sub-skill and use its no-provider helper rather than inventing a live smoke.

## Live provider credentials are not required for install verification

Do not ask for OpenAI, NVIDIA, Google Cloud, or other provider credentials to prove that the package installed. Credentials are needed only for provider-backed runtime workflows. A complete basic verification can stop at:

- Python version check.
- `python -m pip check`.
- Top-level imports and testing-helper imports.
- CLI module help/version.
- Optional extra module import checks requested by the task.

## Moved import paths

Some old LangChain/provider helper paths intentionally raise ImportError and point to their new integration locations. If a user reports old imports failing, prefer the current integration paths:

| Old-style import symptom | Use instead |
| --- | --- |
| `nemoguardrails.llm.helpers` ImportError | `nemoguardrails.integrations.langchain.helpers` |
| `nemoguardrails.llm.providers.huggingface` ImportError | `nemoguardrails.integrations.langchain.providers.huggingface` |
| `nemoguardrails.llm.providers.trtllm` ImportError | `nemoguardrails.integrations.langchain.providers.trtllm` |

`register_llm_provider` remains callable from `nemoguardrails.llm.providers` for provider-registration compatibility. Route detailed integration work to the run/configure sub-skills.

## Supported hard cases

1. **Server optional dependency failure.** If `nemoguardrails server` fails with a missing dependency message, identify that server/action-server runtime dependencies live under the `server` extra, install `nemoguardrails[server]`, rerun CLI help/import checks, then route actual server startup to `run-rails`.
2. **Console command failure with working module invocation.** If `nemoguardrails --help` is broken but `python -m nemoguardrails --help` works, keep automation on the module form and repair/reinstall entry points rather than assuming the package itself is unavailable.
