# MetaGPT Troubleshooting

## Configuration Validation Fails

Symptoms:

- Importing config-backed modules raises a validation error about `llm.api_key`.
- CLI project generation fails before reaching an LLM call.
- A fixed checkout config appears ignored.

Likely causes:

- `~/.metagpt/config2.yaml` still contains placeholder values.
- A checkout-local sample config has `YOUR_API_KEY` and no user config overrides it.
- The wrong provider `api_type`, `base_url`, or model name is configured.

Recovery:

1. Run `metagpt --init-config` if no user config exists.
2. Edit `~/.metagpt/config2.yaml` and replace placeholders privately.
3. Confirm `base_url` ends in the provider's expected path, such as `/v1` for OpenAI-compatible APIs.
4. Re-run `metagpt --help` and `python scripts/check_metagpt_environment.py --json` before a real task.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError` for packages such as `docx`, `pandas`, `faiss`, `chromadb`, `playwright`, `selenium`, `paddleocr`, or vector store clients.
- `pip check` reports missing broad MetaGPT requirements.
- `pip install -e .` is slow or stalls on large wheels.

Recovery:

1. Verify Python is `>=3.9,<3.12`.
2. Install the base package in an isolated environment.
3. Add only workflow-specific optional dependencies instead of installing every extra blindly.
4. For RAG/vector store issues, read `sub-skills/rag-and-tools/references/dependencies.md`.
5. For Android, browser, OCR, Stable Diffusion, or simulation dependencies, read the owning extension or Data Interpreter troubleshooting file.

## CLI Command Fails

Symptoms:

- `metagpt --help` fails with Typer/Click errors.
- Boolean options are rejected.
- `--inc`, `--project-path`, or `--recover-path` does not behave as expected.

Recovery:

- Use the exact dashed option names shown by `metagpt --help`: `--code-review/--no-code-review`, `--run-tests/--no-run-tests`, `--implement/--no-implement`, `--inc/--no-inc`, and `--init-config/--no-init-config`.
- If Typer help fails, check the Click/Typer version combination; Typer `0.9.0` is known to work with Click `8.1.x` better than newer Click releases in some environments.
- For incremental work, provide `--inc` plus either `--project-path` or a project name that resolves to the configured workspace.
- For recovery, `--recover-path` must point to an existing serialized team directory whose path ends in `team`.

## Provider Call Fails

Symptoms:

- Rate limit, quota, missing model, proxy, timeout, or connection errors.
- Replies look like generic assistant messages rather than structured MetaGPT outputs.
- Long outputs are truncated or parse incorrectly.

Recovery:

1. Confirm model access and billing/quota with the provider.
2. Reduce RPM/concurrency or switch to a model/provider with sufficient context length.
3. Check `base_url`, proxy config, and network access.
4. For repeated parse failures, use a longer-context model and inspect the generated intermediate artifacts before retrying.

## Mermaid, Browser, Or Diagram Export Fails

Symptoms:

- Mermaid CLI syntax/runtime errors.
- Browser executable not found.
- Playwright/pyppeteer tries to download browsers unexpectedly.

Recovery:

- Install one rendering path deliberately: Node Mermaid CLI, Playwright, pyppeteer with an existing browser, or `mermaid.ink`.
- If global NPM install is unsafe, use a local Node install or switch to `mermaid.ink` when PDF is not required.
- Set `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true` only when an existing compatible browser is available.

## Data Or External Service Tasks Are Unsafe By Default

MetaGPT examples can read/write local files, execute generated code, browse websites, send email, call remote LLMs, download datasets, and start simulations. Before running any such workflow:

- Confirm credentials and private data handling.
- Confirm network and browsing are allowed.
- Confirm output directories are disposable or backed up.
- Prefer a dry-run/import/helper check first.
- Route to the owning sub-skill for workflow-specific safety gates.

## Where To Go Next

- Core CLI/project generation: `sub-skills/software-company/references/troubleshooting.md`.
- Data Interpreter tasks: `sub-skills/data-interpreter/references/troubleshooting.md`.
- RAG/search/browser/tools: `sub-skills/rag-and-tools/references/troubleshooting.md`.
- AFlow/SPO/extensions/environments: `sub-skills/extensions-and-environments/references/troubleshooting.md`.
- Internal repo maintenance/tests: `sub-skills/maintainer-apis/references/troubleshooting.md`.
