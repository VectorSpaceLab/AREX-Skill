# Workflow Engine Troubleshooting

## Node registration failures

Symptoms:
- Workflow JSON contains a node type that fails to instantiate.
- Error indicates missing class map entry or unknown `NodeType`.

Fix:
- Confirm enum value in `workflow/common/node.py`.
- Confirm class import and `NODE_CLASS_MAP` entry in `workflow/nodes/node_manage.py`.
- Run `scripts/inspect_workflow_nodes.py` to compare enum values and registered map keys.

## Variables are missing downstream

Likely causes:
- Node `_run()` returned a key different from what downstream references expect.
- Variable reference string has the wrong `node_id` or indexed suffix.
- A branch did not execute before a fan-in node.

Fix:
- Inspect `GraphState` write/read logic.
- Verify node output keys in `parse_log()` and tests.
- For fan-in, check whether predecessors are mutually exclusive or parallel.

## Workflow never resumes after user input

Likely causes:
- INPUT/OUTPUT interruption was not registered in `interrupt_before`.
- `handle_input()` did not store the submitted value under expected keys.
- Stateful worker routing did not return to the worker holding in-memory workflow state.
- Redis input/status keys expired or use the wrong `unique_id`.

Fix:
- Trace Redis keys for `workflow:{unique_id}:data`, `status`, `event`, `input`, and `stop`.
- Check `continue_workflow` arguments and worker logs.
- Add a focused resume test for the affected node.

## Streaming output is incomplete

Likely causes:
- LLM callback handler did not emit `on_stream_over`.
- Error path bypassed final output event.
- Frontend expects a field missing from event schema.

Fix:
- Compare callback event classes in `workflow/callback/event.py` with frontend consumers.
- Use existing streaming tests before changing public event payloads.

## Celery task is queued but not processed

Likely causes:
- Worker is not listening to `workflow_celery`.
- Redis broker configuration differs between API and worker.
- Tenant context headers were not propagated.

Fix:
- Start workflow worker from `src/backend`: `uv run celery -A bisheng.worker.main worker -l info -c 100 -P threads -Q workflow_celery -n workflow@%h`.
- Check the same `config` env value across API and worker.
- Route tenant-specific behavior to `identity-permissions-tenancy`.

## LLM/tool calls fail inside workflow nodes

Route by failing surface:

- LLM provider/model config: `backend-core` or `identity-permissions-tenancy` when tenant model config is involved.
- RAG or knowledge retriever failures: `knowledge-rag`.
- MCP tool integration: `linsight-mcp` if using MCP wrapper behavior.
- Frontend node config serialization: `frontend-apps`.
