# Python SDK workflows

Use this reference to choose the smallest useful edit-and-verify path for a Python SDK task.

## General approach

1. Read only the bundled references that match the task.
2. Open the exact file you intend to edit and the smallest relevant test module.
3. Prefer existing fixtures and the narrowest focused test run.
4. Treat provider-backed, live-network, and AWS-backed flows as optional unless the task explicitly needs them.
5. After an edit, run the bundled script first; widen to pytest only when the task needs deeper confirmation.

## Task-to-workflow map

| Task type | Read first | Typical verification |
| --- | --- | --- |
| Agent loop / invocation / checkpointing | `api-reference.md`, `testing-and-maintenance.md` | `python-core-check.sh`, then a focused `tests/strands/agent/test_agent.py` slice |
| Tools / `@tool` / `ToolContext` / schema generation | `api-reference.md`, `testing-and-maintenance.md` | `python-core-check.sh`, then `tests/strands/tools/test_decorator.py` |
| Model provider changes | `api-reference.md`, `testing-and-maintenance.md`, `troubleshooting.md` | provider-specific test file plus the bundled script |
| MCP client / tasks / tool loading | `api-reference.md`, `troubleshooting.md` | `tests/strands/tools/mcp/test_mcp_client.py` or `test_mcp_client_tasks.py` |
| Conversation manager / context management | `api-reference.md`, `testing-and-maintenance.md` | `tests/strands/agent/test_agent.py` plus the relevant conversation-manager tests |
| Memory manager / extraction / injection | `api-reference.md`, `testing-and-maintenance.md` | `tests/strands/memory/test_memory_manager.py` |
| Sessions / snapshots / checkpoints | `api-reference.md`, `testing-and-maintenance.md` | `tests/strands/session/*` and checkpoint-focused agent tests |
| Hooks / interventions / plugins | `api-reference.md`, `testing-and-maintenance.md`, `troubleshooting.md` | the hook or plugin test module nearest the change |
| Sandbox / telemetry / tracing | `api-reference.md`, `testing-and-maintenance.md` | the specific sandbox or telemetry unit module |
| Multi-agent graph / swarm / A2A | `api-reference.md`, `testing-and-maintenance.md` | the relevant `tests/strands/multiagent/*` slice |

## Common implementation patterns

### Agent loop changes

- Edit `strands-py/src/strands/agent/agent.py` and the nearest unit tests in `tests/strands/agent/test_agent.py`.
- Keep sync wrappers thin and let the async path own the real logic.
- If the change affects context management, also check the conversation-manager tests and the memory/session interaction path.
- If you add a new public option, update the constructor docstring, type annotations, and the `Agent` signature facts in `api-reference.md` only if the public contract changes.

### Tool decorator changes

- Edit `strands-py/src/strands/tools/decorator.py` and `tests/strands/tools/test_decorator.py`.
- Re-run the schema, context-injection, async-generator, and error-path tests for the changed behavior.
- If the tool result shape changes, update the tests that assert whole-event equality.
- Preserve the existing `tool_spec` shape and the runtime `tool_name` identity unless the task explicitly changes the contract.

### Model provider changes

- Follow the existing provider pattern: validate config keys, store a typed config object, implement `update_config`, `get_config`, `stream`, and `structured_output`, and add `count_tokens` only when the provider has a real implementation.
- Update the provider module, its unit tests, and `strands.models.__getattr__` / `__all__` if the public export set changes.
- If the provider needs an optional dependency, add or adjust the matching extra in `pyproject.toml` in the same change.
- Translate vendor throttling and context-overflow failures to the SDK's typed exceptions.

### MCP client changes

- Keep `MCPClient` context-manager semantics intact; initialization should remain tied to `with MCPClient(...) as client:`.
- Check config parsing, transport selection, cancellation, progress callbacks, and task-augmented execution separately.
- Use the basic client tests for session-lifecycle changes and `test_mcp_client_tasks.py` for task flow changes.
- Be explicit about optional failure modes such as `continue_on_error`, malformed config, and transport-specific startup errors.

### Memory changes

- Use `tests/strands/memory/test_memory_manager.py` and the existing fake store helpers before adding new test scaffolding.
- Preserve the distinction between search tools, add tools, extraction, and injection.
- Treat AWS-backed or provider-backed memory stores as optional verification surfaces unless the task explicitly asks for them.

### Sessions and checkpoints

- Use `FileSessionManager` for local persistence behavior, `S3SessionManager` only with credentials, and `SnapshotSessionManager` when the task is about single-agent snapshot restore.
- Checkpointing is not conversation persistence; if the task needs durability across processes, keep a session manager in the design.

### Hooks, interventions, plugins

- Read `docs/HOOKS.md` before changing event names or pairings.
- Keep before/after event pairs balanced and preserve reverse-order execution for after hooks.
- Prefer Protocols for extensible callback shapes and keep `InterventionHandler` methods small and explicit.

### Sandbox, telemetry, and multi-agent

- For sandbox changes, verify timeout, cwd, and env handling in the concrete backend, not just the abstract base.
- For telemetry, confirm redaction and span lifecycle on success and error paths.
- For multi-agent changes, validate node ordering, handoff, serialization, and result accumulation separately.

## Safe check commands

From a Strands Agents checkout:

- `scripts/python-core-check.sh`
- `scripts/python-core-check.sh --pytest`
- `cd strands-py && pytest tests/strands/tools/test_decorator.py -q`
- `cd strands-py && pytest tests/strands/agent/test_agent.py -q`
- `cd strands-py && pytest tests/strands/memory/test_memory_manager.py -q`
- `cd strands-py && pytest tests/strands/tools/mcp/test_mcp_client_tasks.py -q`

## What not to widen by default

- Do not jump to `tests_integ/` unless the task is explicitly provider-backed or credential-bound.
- Do not bring in `test-infra/` unless the task is about that infrastructure.
- Do not widen to all providers or all extras when one focused provider test is enough to prove the change.
