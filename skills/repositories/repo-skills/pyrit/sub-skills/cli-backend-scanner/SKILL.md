---
name: cli-backend-scanner
description: "Use PyRIT command-line scanners, backend service, shell, GUI entry
  points, scanner configs, and CLI troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyRIT CLI, Backend, Scanner, and GUI Router

Use this sub-skill when the task is to run or diagnose PyRIT through `pyrit_scan`, `pyrit_shell`, `pyrit_backend`, the local REST backend, or the CoPyRIT browser UI. Treat these entry points as clients/services around the PyRIT scenario, target, dataset, converter, and scoring internals.

## Read First

- For exact command surfaces, server/client split, config precedence, REST routes, GUI notes, and Docker caveats, read [CLI and backend reference](references/cli-backend-reference.md).
- For task-oriented command recipes, including list commands, rapid-response scans, result inspection, shell sessions, GUI usage, and safe shutdown, read [scanner workflows](references/scanner-workflows.md).
- For backend startup failures, port conflicts, invalid config, missing targets/credentials, bad scenario or technique names, empty dataset filters, server URL mismatch, GUI/backend split, and container caveats, read [troubleshooting](references/troubleshooting.md).
- Before assuming console scripts are available, run the safe no-server smoke helper: [scripts/pyrit_cli_smoke.py](scripts/pyrit_cli_smoke.py).

## Route By User Intent

- **"Use pyrit_scan", "run a scan", "list scenarios", "inspect scenario results"**: use [scanner workflows](references/scanner-workflows.md) and confirm a backend is already running or the user explicitly wants `--start-server`.
- **"Start/stop/configure the backend" or "serve CoPyRIT"**: use [CLI and backend reference](references/cli-backend-reference.md#backend-service-pyrit_backend) plus [troubleshooting](references/troubleshooting.md#backend-startup-port-and-timeout-failures).
- **"Interactive scanner shell"**: use [scanner workflows](references/scanner-workflows.md#interactive-shell-workflow) and keep shell-only commands distinct from `pyrit_scan` flags.
- **"GUI", "CoPyRIT", "browser UI"**: use [CLI and backend reference](references/cli-backend-reference.md#copyrit-gui-high-level-usage) for the backend/UI split; do not enter frontend TypeScript development.
- **"Docker" or "container"**: use Docker guidance only as reference-oriented operational context; do not run Docker build/run helpers unless the user explicitly asks for container operations.

## Boundaries

- This sub-skill owns CLI syntax, backend service lifecycle, REST client behavior, scan command construction, result views, GUI high-level usage, and command troubleshooting.
- For scenario semantics, attack-technique selection, scenario parameters, result interpretation, and executor internals, route to sibling [`attacks-scenarios`](../attacks-scenarios/SKILL.md).
- For registering, configuring, and troubleshooting prompt targets, target credentials, scorer choices, and LLM-backed scoring failures, route to sibling [`targets-scorers`](../targets-scorers/SKILL.md).
- For dataset schemas, converter stacks, seed prompt formats, and dataset/converter optional dependencies, route to sibling [`converters-datasets`](../converters-datasets/SKILL.md).
- For PyRIT home files, memory backend selection, initialization files, registry behavior, and configuration-loader details, route to sibling [`setup-memory-core`](../setup-memory-core/SKILL.md).
- Frontend TypeScript development, Azure infrastructure deployment internals, broad Docker build automation, and low-level attack/target/scorer implementation changes are out of scope here.

## Safety Rules

- Do not invent or run a live scan against an external model without user authorization, a configured target, and credentials handled outside the command text.
- `pyrit_scan` discovery and run commands require a reachable backend unless the command is help-only or stopping a local backend.
- Prefer a local loopback backend (`localhost` or `127.0.0.1`) for ad hoc use. Binding `pyrit_backend` to a non-loopback host exposes an unauthenticated API unless the deployment has explicitly configured authentication controls.
- Keep secrets out of CLI arguments, logs, shell history, and generated examples. Use environment files or configured target initializers for credentials.
