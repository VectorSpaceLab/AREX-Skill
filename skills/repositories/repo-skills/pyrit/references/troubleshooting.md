# PyRIT Cross-Cutting Troubleshooting

## Install/import issues

Run `scripts/pyrit_api_smoke.py --json`. If metadata or imports fail, install PyRIT into the active environment rather than relying on a checkout path. Use optional extras only for the selected workflow.

## Missing optional dependency

Symptoms: `ImportError` for torch, Playwright, speech, OpenCV, LiteLLM, spaCy, browser tools, or service SDK pieces.

Recovery: identify the owning sub-skill and install only the documented extra needed for the task. Do not install `all` just to inspect base PyRIT.

## Credentials and external services

OpenAI/Azure/HTTP/Playwright/Azure SQL workflows need endpoints, tokens, accounts, network, or database permissions. Keep credentials outside prompts and examples. A no-secret smoke validates wiring only, not live behavior.

## Backend or CLI confusion

`pyrit_scan` and `pyrit_shell` are clients; most commands require a running backend. Start or stop a backend only with user approval. Route command issues to `cli-backend-scanner`.

## Wrong layer ownership

If an attack appears to branch on raw responses, move the judgment to a scorer. If a target transforms prompts, move that to a converter. If a scenario implements per-turn logic, move it to an attack/executor. Route to `attacks-scenarios` for orchestration boundaries.

## Data/config validation

For seed and dataset issues, route to `converters-datasets`. For PyRIT config and memory database issues, route to `setup-memory-core`. For target/scorer config, route to `targets-scorers`.
