---
name: sdk-and-api-clients
description: "Integrate with Langflow through REST APIs, OpenAPI contracts,
  Python SDK clients, streaming runs, and flow/project push-pull workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SDK And API Clients

Use this sub-skill when the task is to call a Langflow server from application code, validate API examples, inspect OpenAPI contracts, normalize flow JSON for source control, or debug client-side API failures.

Route elsewhere when the user wants local flow execution with `lfx run` or `lfx serve` (`../executor-cli/SKILL.md`), backend route/service implementation (`../backend-runtime/SKILL.md`), flow JSON authoring semantics (`../flow-authoring/SKILL.md`), or deployment and server configuration (`../deployment-and-operations/SKILL.md`).

## Fast Start

1. Use `references/sdk-reference.md` for Python SDK construction, sync/async clients, CRUD, run/stream helpers, push/pull, environment config, and typed exceptions.
2. Use `references/api-contracts.md` for REST endpoint shapes, OpenAPI files, streaming event contracts, TypeScript client notes, and API example validation strategy.
3. Use `references/troubleshooting.md` for install/import errors, auth and HTTP failures, streaming edge cases, schema problems, normalization surprises, and backend-boundary signals.
4. Run `scripts/normalize_flow_file.py` when a flow JSON file must be made deterministic and safe for git before review or push.

## Common Workflows

- **Construct a Python client:** prefer `from langflow_sdk import Client, AsyncClient`; pass `base_url`, optional `api_key`, and optional `timeout`. Use context managers (`with Client(...) as client:` or `async with AsyncClient(...) as client:`) when the client owns its HTTP transport.
- **Run a flow:** call `client.run(flow_id_or_endpoint, input_value="...")` for the simple case, or `client.run_flow(flow_id_or_endpoint, RunRequest(...))` when setting `input_type`, `output_type`, `tweaks`, or `stream` explicitly.
- **Stream a flow:** iterate `client.stream(...)` or `async for chunk in client.stream(...)`; handle `chunk.is_token`, `chunk.is_end`, and `chunk.is_error`, and map `LangflowAuthError`/`LangflowHTTPError` separately from event-level failures.
- **Manage flows and projects:** use `list_flows`, `get_flow`, `create_flow`, `update_flow`, `upsert_flow`, `delete_flow`, `list_projects`, `download_project`, and `upload_project`; `push`/`pull` wrap file-based flow upsert and normalized download.
- **Normalize a flow file:** run `python scripts/normalize_flow_file.py flow.json --output flow.normalized.json --code-as-lines` to strip secrets and volatile UI/server fields with deterministic JSON output.

## Validation Checklist

- Verify the target server URL includes scheme and port, for example `http://localhost:7860`, and does not include trailing API path segments.
- Verify API keys are passed as `x-api-key` through SDK `api_key` or explicit HTTP headers; do not embed real keys in examples or committed TOML.
- For write operations, validate IDs and payloads with SDK models (`FlowCreate`, `FlowUpdate`, `ProjectCreate`, `RunRequest`) before sending.
- For streaming clients, assert non-2xx HTTP statuses raise typed SDK exceptions before parsing stream chunks, and assert final `end` chunks are optional in error paths.
- For OpenAPI or docs examples, prefer offline schema/example linting first; only run live examples against an intentionally started local or test Langflow instance.

## References And Helpers

- [SDK reference](references/sdk-reference.md)
- [API contracts](references/api-contracts.md)
- [Troubleshooting](references/troubleshooting.md)
- [Flow normalization helper](scripts/normalize_flow_file.py)
