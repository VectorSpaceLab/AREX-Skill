# Langflow Troubleshooting

## When To Read

Read this for cross-cutting Langflow failures that do not clearly belong to one sub-skill yet. For detailed failures, route to the nearest sub-skill troubleshooting file.

## Route Failure by Symptom

| Symptom | First route |
| --- | --- |
| Flow JSON does not import, validate, run, or accept tweaks | `sub-skills/flow-authoring/references/troubleshooting.md` |
| Custom component does not appear, output handle breaks, class rename breaks saved flows, bundle is not discovered | `sub-skills/component-development/references/troubleshooting.md` |
| FastAPI route, graph execution, auth/authz, database, migration, upload, telemetry, or service dependency fails | `sub-skills/backend-runtime/references/troubleshooting.md` |
| `lfx run`, `lfx serve`, `lfx validate`, `lfx-mcp`, Flow DevOps, or stateless persistence surprises | `sub-skills/executor-cli/references/troubleshooting.md` |
| SDK client, REST API call, OpenAPI example, streaming event, push/pull, or normalization fails | `sub-skills/sdk-and-api-clients/references/troubleshooting.md` |
| React/Vite frontend, icons, stores, API controllers, Jest, Playwright, proxy, or build fails | `sub-skills/frontend-development/references/troubleshooting.md` |
| Install, CLI startup, Docker/Compose, PostgreSQL, volumes, `.env`, API keys, logs, workers, storage, or reverse proxy fails | `sub-skills/deployment-and-operations/references/troubleshooting.md` |
| Monorepo setup, focused tests, formatting, generated artifacts, version pins, release scripts, docs, or CI checks fail | `sub-skills/repo-maintenance/references/troubleshooting.md` |

## Common Cross-cutting Issues

### `No module named langflow`, `No module named lfx`, or SDK import fails

Likely causes:

- Running commands outside the intended Python environment.
- Installing only one workspace package when the task needs `langflow-base`, `lfx`, `langflow-sdk`, or extension bundles.
- Using an older global install instead of the active checkout/package.

Fix:

1. Confirm the environment with `python -c "import sys; print(sys.executable)"`.
2. Check package metadata with `python -m pip show langflow langflow-base lfx langflow-sdk`.
3. For source checkout work, use the repo-maintenance setup guidance before running package-specific commands.
4. For installed-package use, install the public distribution and only the extras required by the selected workflow.

### `langflow --help` or CLI startup fails on a missing provider package

Current server imports may touch route modules that import optional provider SDKs. If a CLI command fails before showing help with a missing dependency such as `openai`, the active environment is missing a dependency for that application surface.

Fix:

- Install the provider dependency required by that route or use a Langflow distribution/image that includes it.
- Do not install every optional extra unless the user explicitly needs broad provider coverage.
- If the task only needs `lfx`, use `lfx --help` or `lfx ...` directly instead of the full application CLI.

### PyTorch or transformer model execution is unavailable

A warning such as `PyTorch was not found. Models won't be available` means tokenizers/config/file utilities may import, but local model execution is not available.

Fix:

- Ignore this for flow JSON validation, SDK/API work, backend route checks, frontend work, and ordinary repo maintenance.
- Install PyTorch/model extras only when the selected component or workflow requires local model execution and the hardware/backend is known.
- For Docker/operations, choose CPU/GPU images and dependencies deliberately; do not assume GPU availability.

### API keys or provider credentials are missing

Many starter flows and components intentionally require provider credentials. Missing credentials are not the same as a broken flow or package.

Fix:

- Keep real keys in environment variables or secret managers, not in flow JSON or examples.
- Use `LANGFLOW_API_KEY` or request headers for Langflow/LFX API access; use provider-specific variables for model/tool providers.
- For offline smoke tests, prefer flows that do not call external providers or stop once graph load succeeds and the expected credential error appears.

### Same task could route to multiple sub-skills

Use the layer being changed or debugged:

- Flow document: `flow-authoring`.
- Local executor behavior: `executor-cli`.
- Running-server API calls: `sdk-and-api-clients`.
- Backend implementation: `backend-runtime`.
- Deployment config/runtime environment: `deployment-and-operations`.
- Repository test/format/version policy: `repo-maintenance`.
- Python component contract: `component-development`.
- React UI behavior: `frontend-development`.

## Safe Escalation

Before running broad commands or mutating state:

- Prefer static helpers and focused tests.
- Avoid destructive migrations, Docker volume removal, package publishing, live cloud deployment, credentialed provider calls, and model/GPU workloads unless explicitly requested.
- Back up databases and config directories before migration or deployment changes.
- Do not commit or persist generated secrets.
