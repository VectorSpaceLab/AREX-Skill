---
name: ui-and-deployment
description: "Operate Sparrow Gradio and Next UI shells, service topology,
  deployment checks, and UI troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# ui-and-deployment

Use this sub-skill when the task is to run, configure, deploy, smoke-check, or troubleshoot Sparrow's user-facing shells and their service wiring.

## Route here for

- Gradio shell operation: document-processing page, dashboard page, feedback page, upload limits, Sparrow key controls, Oracle-backed dashboard/feedback, Gradio queueing, and temporary file cleanup.
- Next shell operation: `/process`, `/dashboard`, `/feedback`, `/api/inference`, `/api/summarize`, package scripts, package metadata checks, upload gates, streaming route behavior, and deployment environment variables.
- Service topology checks across UI, LLM API, optional Oracle DB, optional OCR service, and optional agents service.
- UI-facing diagnosis where the symptom might be an upload validation failure, unreachable backend API, restricted-key configuration, missing database records, npm dependency state, CORS/port mismatch, or reverse-proxy buffering.

## Route elsewhere

- LLM API request semantics, engine options, CLI usage, model backend selection, pipeline behavior, schema validation internals, and backend HTTP endpoint contracts: route to `api-engine-and-cli`.
- OCR model behavior, OCR endpoint details, PDF/image text extraction, bounding boxes, and OCR dependencies: route to `ocr-service`.
- Agent workflow execution, agent selection, Prefect/Celery/Redis behavior, async task polling, and workflow-specific payloads: route to `agent-workflows`.
- Do not change API payload meaning from this sub-skill; only verify that the UI forwards the expected fields and displays failures coherently.

## Operating workflow

1. Identify the active shell: Gradio Python UI, Next UI, or both behind a proxy. Use [UI deployment](references/ui-deployment.md) for run commands, shell responsibilities, and configuration keys.
2. Confirm the service graph and startup order from [service topology](references/service-topology.md): UI -> LLM API, optional UI/LLM API -> Oracle DB, optional side services for OCR and agents.
3. Run metadata-only checks before installing or building Node packages. Use [`scripts/ui_config_check.py`](scripts/ui_config_check.py) against a Next `package.json`, or run it without a package file to print the embedded expectations.
4. For user-visible failures, triage with [troubleshooting](references/troubleshooting.md). Separate local upload validation, UI server route failures, backend API failures, restricted-key/Oracle failures, and rendering issues before changing code.
5. If the root cause is outside UI/deployment ownership, hand off with the exact observed UI symptom, the shell in use, relevant environment/config keys, service port/status, and the route target skill named above.

## Fast checks

- Next package metadata should expose `dev`, `build`, `start`, and `lint` scripts and include the runtime dependencies used by the process page, dashboard, feedback, Oracle access, PDF page counting, GeoIP, and long-timeout fetch handling.
- Gradio upload validation is image/PDF-focused and removes copied inference inputs in a `finally` block; a background cleaner handles stale Gradio temp cache entries.
- Next upload validation is browser-side before `/api/inference`; server actions then forward valid files to the LLM API. A browser-side invalid type should not create backend API traffic.
- Dashboard and feedback are optional Oracle-backed features. Empty dashboard data is expected when database access is disabled; failed feedback persistence is usually a database/config issue, not an LLM issue.
