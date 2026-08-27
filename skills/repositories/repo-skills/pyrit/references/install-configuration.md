# PyRIT Install and Configuration

## Package identity

PyRIT installs as distribution `pyrit` and imports as `pyrit`. The baseline for this skill is `1.1.0.dev0` and supports Python `>=3.10,<3.15`.

Basic install patterns:

```bash
python -m pip install pyrit
python -m pip install 'pyrit[huggingface]'
python -m pip install 'pyrit[playwright]'
python -m pip install 'pyrit[gcg]'
```

Use optional extras only when the task needs them. The base package is sufficient for package inspection, core setup, offline converters, `TextTarget`, SQLite memory, and CLI help checks.

## Optional extras and services

| Extra/service | Use | Verification boundary |
|---|---|---|
| `huggingface` | HuggingFace target/model workflows. | May require model downloads and torch runtime. |
| `gcg` | GCG prompt generation. | Heavy optional path; torch/accelerate/sentencepiece and model/tokenizer downloads, often GPU-beneficial. |
| `playwright` | Browser/Copilot target automation. | Requires browser binaries, UI selectors, and account/session setup. |
| `fairness_bias`, `opencv`, `speech`, `litellm` | Specialized benchmarks/media/provider integrations. | Install only for selected workflows. |
| OpenAI/Azure/LiteLLM/Azure SQL/Key Vault | Live services. | Requires credentials/endpoints/network and user-approved scope. |

## PyRIT home and config

PyRIT commonly uses a PyRIT home directory containing config and environment files. Configuration may load database settings, initializers, targets, scorers, datasets, and environment files. Keep secrets in environment files or managed secret stores, never in generated examples.

Programmatic workflows can call `initialize_pyrit_async(...)`; config-driven workflows can call `initialize_from_config_async(config_path=None)` or use `pyrit_backend --config-file` / `pyrit_scan --config-file`.

## Minimum no-secret check

Run the bundled root helper in the environment where PyRIT should be installed:

```bash
python scripts/pyrit_api_smoke.py --json
```

This only imports and introspects selected APIs. It does not prove live API credentials, model quality, browser readiness, Azure SQL connectivity, GPU/model-download paths, or backend server behavior.
