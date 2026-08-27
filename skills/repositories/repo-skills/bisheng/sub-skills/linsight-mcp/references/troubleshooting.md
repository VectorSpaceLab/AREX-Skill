# Linsight and MCP Troubleshooting

## Task never starts

Likely causes:
- Linsight worker process is not running.
- Redis queue/config differs between API and worker.
- Node heartbeat or task owner key is stale.
- Session version is already terminal.

Recovery:
- Verify the Linsight worker process, not Celery.
- Check Redis queue and owner keys with the same `config` env as the API.
- Confirm session version status in DB/Redis before requeueing.

## Task pauses and never resumes

Likely causes:
- `NeedUserInput` event was emitted but frontend did not submit a matching response.
- User input completed state did not persist.
- Agent `continue_task` did not map the input to the waiting task.

Recovery:
- Trace execute task status transitions.
- Inspect event payload and frontend mapper compatibility.
- Add focused tests around user-input coercion and state persistence.

## Tool calls loop or fail silently

Likely causes:
- Tool schema lacks required `call_reason` injection.
- Tool history exceeded buffer and summary path failed.
- Code interpreter output path or workspace copy-in/out mismatched.
- LLM provider returned malformed JSON for task decomposition.

Recovery:
- Check tests around tool-loop middleware, call reason, workspace backend, truncation guard, and final result selection.
- Do not hide tool exceptions; preserve visible task failure or retry semantics.

## MCP connection fails

Symptoms:
- Tool list returns empty.
- Stdio command never starts.
- SSE or streamable HTTP call times out.

Likely causes:
- MCP config type misdetected.
- `command` path or args invalid for stdio.
- URL unreachable from backend worker host.
- Tool input schema contains values needing type coercion.

Recovery:
- Inspect `ClientManager.parse_mcp_client_type` behavior.
- Validate config shape without credentials in committed files.
- Test LangChain wrapper behavior with mocks before using real MCP servers.

## SOP to Skill migration issues

Symptoms:
- Migrated skill missing display name or description.
- Duplicate skills after rerun.
- Object storage write fails.

Recovery:
- Dry-run first and review JSON summary.
- Ensure app context and object storage are initialized.
- Idempotency should use `metadata.sop-id` rather than name-only matching.
- Route operational sequencing to `deployment-maintenance`.

## Menu or model config missing after upgrade

Likely cause:
- Startup backfills failed or did not run, or tenant-specific model config is missing.

Recovery:
- Route permission/menu/model isolation behavior to `identity-permissions-tenancy`.
- Use manual backfill scripts only after reading deployment-maintenance guidance.
