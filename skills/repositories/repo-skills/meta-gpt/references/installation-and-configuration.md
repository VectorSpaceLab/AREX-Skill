# Installation and Configuration

## When To Read

Read this before installing MetaGPT, initializing `config2.yaml`, choosing optional dependencies, or diagnosing provider/browser/Mermaid setup.

## Package Baseline

MetaGPT is distributed as `metagpt` and exposes a `metagpt` console script. The package metadata declares:

| Fact | Value |
| --- | --- |
| Distribution | `metagpt` |
| Version in this snapshot | `1.0.0` |
| Python range | `>=3.9,<3.12` |
| Console entry | `metagpt=metagpt.software_company:app` |
| Main CLI framework | Typer |

Use Python 3.9 or 3.10 when following the public docs. Avoid Python 3.12+ unless the package metadata and dependencies have been updated.

## Install Paths

For normal use:

```bash
python -m pip install metagpt
metagpt --help
```

For a local checkout:

```bash
python -m pip install -e .
metagpt --help
```

If editable install fails with permission errors in a system Python, use a virtual environment or `python -m pip install -e . --user` only when that matches the user's environment policy.

## Configuration Files

MetaGPT reads configuration from these locations, with later user configuration taking precedence:

1. Checkout or package config such as `config/config2.yaml` when available.
2. User config `~/.metagpt/config2.yaml`.
3. Environment variables merged into the config model.

Initialize a user config when needed:

```bash
metagpt --init-config
```

Then edit `~/.metagpt/config2.yaml` and replace placeholder values:

```yaml
llm:
  api_type: "openai"
  model: "gpt-4-turbo"
  base_url: "https://api.openai.com/v1"
  api_key: "YOUR_REAL_KEY"
```

Do not paste real API keys into issue reports, generated code examples, or skill artifacts. When helping a user debug, ask them to verify the key privately.

## Provider Notes

MetaGPT contains provider modules for OpenAI-compatible APIs and several vendor providers. Typical config fields include `api_type`, `model`, `base_url`, `api_key`, and optional proxy settings. Use root troubleshooting when the symptom is provider-specific, such as quota, rate limit, missing model, proxy connectivity, or placeholder key validation.

## Optional Dependencies

The base requirements are broad. Install only the dependencies needed for the chosen workflow:

| Workflow | Extra or dependency family | Notes |
| --- | --- | --- |
| Core software-company CLI/library | base package requirements | Requires valid LLM config for real runs. |
| RAG/vector stores | `[rag]` extra or selected vector/document packages | See `rag-and-tools/references/dependencies.md`. |
| Browser/search tools | Playwright/Selenium/search API packages and browser binaries | Browser binaries and API keys may be external prerequisites. |
| Android Assistant | `android_assistant` extra/deps and Android device/emulator | Hardware/service-gated; do not run as smoke test. |
| Mermaid rendering | Node `@mermaid-js/mermaid-cli`, Playwright, pyppeteer, or mermaid.ink | Choose one renderer and configure `mermaid.engine`/path. |
| Tests/dev | test/dev extras and provider mocks | Avoid full broad installs unless maintaining the repo. |

## Mermaid And Browser Rendering

MetaGPT can render diagrams through Mermaid tooling. Public docs describe these options:

- Node/NPM `@mermaid-js/mermaid-cli`.
- Python Playwright with browser installation.
- Pyppeteer with an existing browser path.
- `mermaid.ink`, which does not support PDF export.

If browser installation or global NPM install is unsafe, use `mermaid.ink` for lightweight diagram rendering or skip diagram export.

## Safe Checks

Run these checks before spending tokens or running generated code:

```bash
metagpt --help
python scripts/check_metagpt_environment.py --json
```

Sub-skill helpers are also safe by default:

```bash
python sub-skills/software-company/scripts/inspect_role_action.py --json
python sub-skills/data-interpreter/scripts/di_import_check.py --json
python sub-skills/rag-and-tools/scripts/rag_import_check.py --group core --json
python sub-skills/extensions-and-environments/scripts/optimizer_help_check.py --mode help --json
python sub-skills/maintainer-apis/scripts/list_public_symbols.py --module metagpt --json
```

Each helper is diagnostic-only and should not call an LLM, browse the web, run project generation, download datasets, or start simulations.
