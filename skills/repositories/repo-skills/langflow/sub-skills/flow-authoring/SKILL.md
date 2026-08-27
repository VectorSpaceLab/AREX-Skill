---
name: flow-authoring
description: "Build, validate, import/export, tweak, and run Langflow flow JSON
  and starter workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Flow Authoring

Use this sub-skill when the task is to create, inspect, edit, validate, import/export, smoke-run, or troubleshoot Langflow flow JSON. It focuses on flow documents, starter workflows, runtime tweaks, chat/text input expectations, graph-run output signals, and offline checks.

Route elsewhere when the task is primarily about:

- Python component classes, inputs/outputs, dynamic loading, or bundle extensions: `../component-development/SKILL.md`.
- REST clients, SDK code, OpenAPI contracts, or application integration: `../sdk-and-api-clients/SKILL.md`.
- Server startup, Docker, database, auth, environment operations, or production deployment: `../deployment-and-operations/SKILL.md`.

## Start Here

1. Read `references/flow-json-and-tweaks.md` before editing exported flows, writing tweaks, or diagnosing node/edge/schema issues.
2. Read `references/workflows.md` before choosing between visual import/export, API run requests, `lfx validate`, and `lfx run` smoke checks.
3. Read `references/troubleshooting.md` when validation, `lfx run`, webhook/API triggering, credentials, optional dependencies, or output extraction fails.
4. Use `scripts/validate_flow_json.py` for a safe static preflight that does not import Langflow; then use `lfx validate` for deeper installed-package checks when `lfx` is available.

## Fast Commands

```bash
python scripts/validate_flow_json.py flow.json
lfx validate flow.json --level 1 --skip-components --skip-edge-types --skip-required-inputs --skip-version-check --skip-credentials
lfx validate flow.json --level 4 --skip-components --format json
lfx run flow.json "hello" --no-check-variables --format json
cat flow.json | lfx run --stdin --input-value "hello" --no-check-variables --format json
```

Prefer the bundled helper first for quick JSON and topology mistakes. Prefer `lfx validate` when the local installation should evaluate Langflow-specific structural, edge, required-input, version, and credential warnings. Prefer `lfx run` only after static validation passes and the flow is expected to run without unavailable credentials, network services, model backends, or local files.

## Evidence Base

This guidance is distilled from Langflow flow docs, run endpoint docs, data-type docs, bundled starter project JSON, starter-project regression tests, graph execution tests, `lfx validate/run` tests, and frozen starter-flow fixtures. Runtime instructions here are self-contained and do not require reopening those source files.
