---
name: api-engine-and-cli
description: "Operate Sparrow LLM API and CLI surfaces, request routing,
  validation, table templates, and protected-access configuration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# API Engine and CLI

Use this sub-skill when the task is to run, debug, or translate requests for Sparrow's LLM-facing command line and HTTP API surfaces: `sparrow.sh`, the Typer engine command, the FastAPI `/api/v1/sparrow-llm/inference` endpoint, or `/api/v1/sparrow-llm/instruction-inference`.

## Route the task

- CLI/API arguments, endpoint fields, request translation, and response parsing: read [references/cli-and-api.md](references/cli-and-api.md).
- Query preparation, wildcard behavior, hints, schema validation, and validation bypass flags: read [references/query-and-validation.md](references/query-and-validation.md).
- Protected access, `sparrow_key`, config-file keys, and database toggles: read [references/configuration.md](references/configuration.md).
- `--table`, `--table-template`, table option pairing, and generic template behavior: read [references/table-templates.md](references/table-templates.md).
- Failures and recovery checks: read [references/troubleshooting.md](references/troubleshooting.md).

## Boundaries and handoffs

- Backend-specific visual extraction, model loading, and document pre/post-processing details belong to [../document-extraction/SKILL.md](../document-extraction/SKILL.md).
- OCR service behavior belongs to [../ocr-service/SKILL.md](../ocr-service/SKILL.md).
- UI clients, dashboards, Docker/runtime deployment, and browser-side API callers belong to [../ui-and-deployment/SKILL.md](../ui-and-deployment/SKILL.md).
- Agents REST workflows and multi-step orchestration belong to [../agent-workflows/SKILL.md](../agent-workflows/SKILL.md).

## Safe bundled helpers

These scripts are offline by default and are safe to run for fixture checks or request construction:

- `python scripts/sparrow_cli_request.py --help` builds CLI or curl requests, including curl-to-CLI translation.
- `python scripts/json_validation_smoke.py --help` validates Sparrow-style JSON example schemas against candidate JSON.
- `python scripts/table_template_smoke.py --help` exercises the generic table-template mapping against an embedded HTML table fixture.

## Operating checklist

1. Identify the surface: CLI, document API, or instruction API.
2. Normalize options: repeated `--options` for CLI; comma-separated `options=` for API.
3. Choose the pipeline: `sparrow-parse` for document/schema work, `sparrow-instructor` for instruction/payload text work.
4. Check query mode before blaming the model: `*`, `--instruction`, `--validation`, `--markdown`, `--page-type`, and `--table` change both prompts and validation behavior.
5. If the API is protected, confirm the `sparrow_key` route: config-key validation when database use is disabled, database validation when enabled.
6. For table requests, confirm whether the request is using the generic table template and whether it supplied the second backend/model pair required by the table OCR pass.
