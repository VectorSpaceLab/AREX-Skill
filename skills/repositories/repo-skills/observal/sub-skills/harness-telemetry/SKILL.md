---
name: harness-telemetry
description: "Guide Observal harness registry, adapters, hooks, session
  delivery, reconcile, parsers, and telemetry ingest changes."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Observal Harness Telemetry

Use this sub-skill when the task touches Observal harness support, local harness scanning, config generation for `observal agent pull`, `observal scan`, `observal doctor`, managed hook specs, session push/reconcile, session parser dispatch, telemetry ingest acknowledgements, or layer/managed-file attribution.

## Route by task

- Adding or promoting a harness: read `references/harness-support.md`, then `references/session-parsers.md` and `references/telemetry-pipeline.md` before editing code.
- Debugging missing sessions after hook installation: read `references/telemetry-pipeline.md`, then use the decision tree in `references/troubleshooting.md`.
- Changing trace display, raw-line classification, token/model extraction, or parser registration: read `references/session-parsers.md`.
- Changing scan/doctor/layer behavior: read `references/harness-support.md` and verify with the helper script in `scripts/check_harness_registry.py`.
- Investigating CLI/API/auth/config failures owned by harness telemetry: read `references/troubleshooting.md`.

## Boundaries

This sub-skill owns harness registry entries, CLI harness adapters, server harness adapters, hook specs, doctor patch/cleanup for telemetry hooks, session-source discovery, session push/reconcile behavior, local durable outbox behavior, server session parser registration, ingest/checkpoint/finalization semantics, and layer managed-file attribution.

Do not use this sub-skill for general Typer command hierarchy, registry component CRUD, FastAPI business routes outside ingest/config harness metadata, database migrations, web UI implementation, release/compliance workflow, or root-skill provenance/routing work unless the change directly affects harness telemetry.

## Operating rules

- Keep harness-specific logic in one CLI adapter and one server adapter; do not add broad if/elif chains to orchestrators.
- Treat `packages/observal-shared/observal_shared/harness_registry.py` as the shared source of truth for harness ids, capabilities, paths, event maps, parser ids, and model catalog files.
- Use the shared session push engine (`observal_cli.hooks.session_push --harness <id>`) unless a host requires a thin response bridge or native extension.
- Keep MCP commands and remote URLs direct. Do not add telemetry wrappers or OTLP environment variables for harness support.
- Make scan and doctor fail soft for absent harness installs, but fail loudly for malformed files only where the existing adapter contract already does so.
- Preserve user-owned hook/config entries when doctor patching or cleanup runs; remove or rewrite only Observal-managed entries.

## Fast verification entrypoint

From an Observal checkout, run:

```bash
python skills/disco/observal/sub-skills/harness-telemetry/scripts/check_harness_registry.py --repo-root . --pretty
```

Expected high-level signal: every registered harness has CLI/server adapter files and parser coverage; hook-spec files are expected for most harnesses, while Cursor and Pi are handled by direct doctor/extension code rather than dedicated `harness_specs/*_hooks_spec.py` modules.
