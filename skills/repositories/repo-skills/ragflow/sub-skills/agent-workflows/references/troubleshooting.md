# Agent Workflow Troubleshooting

## Component References Fail

Symptoms:

- Prompt variables render as empty strings.
- Runtime raises `Can't find variable: '<component_id>@<output>'`.
- A downstream component silently waits or is removed from the current execution slice.

Checks:

- Use the exact component ID from `components`, not the display label from the visual graph.
- Confirm the output key exists in the upstream component's `params.outputs` or is set by that component at runtime.
- For nested paths such as `{agent@structured.answer}`, confirm the root output is valid JSON/dict-like and the path keys/indexes exist.
- In Iteration children, prefer `{item}`, `{index}`, and `{result}` aliases only inside the iteration scope.
- Ensure the referenced component appears earlier in the runtime `path` or is otherwise guaranteed to run before the consumer.

## Cycles, Path Order, and Branches

Symptoms:

- Workflow repeats unexpectedly.
- Nodes never run after a Switch/Categorize.
- Loop/Iteration exits at the wrong point.

Checks:

- Verify every `downstream` and `upstream` list points to existing components.
- For `Switch`, confirm condition `cpn_id` is non-empty and operator/value are supported; empty condition component IDs fall through to else.
- For `Categorize`, inspect the LLM classification prompt and branch labels.
- For `Iteration`, `items_ref` must resolve to an array; non-array input sets an error.
- For `Loop`, every loop variable needs `variable`, `input_mode`, `value`, and `type`; missing fields raise a completeness error.
- For `ExitLoop`, confirm it is inside a Loop; otherwise parent resolution is invalid.
- Avoid normal downstream edges that bypass required branch/loop control nodes.

## Async, Streaming, and Message Behavior

Symptoms:

- Tool or Agent output appears only after Message completes.
- `content` is a generator/partial before finalization.
- Trace and message events arrive in a different order than expected.

Checks:

- Components with async `_invoke_async` are awaited; sync components can run in a thread pool.
- An Agent with tools and a downstream Message can stream through a partial output; final `content` is set after streaming completes.
- Message consumes partial outputs and then emits `message_end` and delayed `node_finished` events.
- If structured output is enabled, Agent disables the normal streaming path and retries JSON formatting instead.
- Cancellation sets task state and components should check cancellation during long operations.

## Tool Credentials and Network Calls

Symptoms:

- Tool returns credential, timeout, DNS, or permission errors.
- Trace logs expose sensitive arguments.
- SSRF or unsafe-host checks reject URLs.

Checks:

- Do not assume credentials are configured just because the template includes a tool.
- Keep real API keys out of prompts, examples, logs, and returned traces.
- Confirm base URLs are intended and safe before live calls.
- For search/crawler/email/GitHub/SQL tools, ask the user before executing network or external-service operations.
- Use a minimal non-destructive probe before a full workflow run.

## Sandbox and Code Execution

Symptoms:

- CodeExec returns provider configuration errors.
- Docker/gVisor/seccomp errors appear.
- Code runs but output contract fails.
- Artifacts are missing or inaccessible.

Checks:

- Confirm sandbox provider or executor manager is configured and reachable before using CodeExec.
- Confirm the language is `python`/`python3` or `javascript`/`nodejs`.
- Ensure Python defines `main(...)`; JavaScript exports `main`.
- Ensure the function returns exactly one declared business output and uses supported top-level value types.
- Do not use reserved output names for business outputs.
- Save files under `artifacts/`; use non-interactive plotting backends.
- Treat seccomp failures as environment-policy issues, not workflow DSL bugs.

## Webhook Security and Payloads

Symptoms:

- Begin component does not receive webhook input.
- Unexpected payload fields become component outputs.
- Webhook-triggered runs expose sensitive request content.

Checks:

- Begin must be in Webhook mode for `webhook_payload` mapping.
- `webhook_payload.input` maps to Begin input `request`; other payload keys become Begin outputs.
- Validate webhook authentication, replay protection, and payload schema outside the canvas.
- Never log full webhook bodies when they may contain secrets or user data.

## Memory Configuration

Symptoms:

- Memory retrieval returns no relevant messages.
- Saved messages are attributed to the wrong user/session/agent.
- Memory reaches capacity or forgotten messages still seem visible.

Checks:

- Confirm memory has compatible embedding and LLM settings.
- Confirm Retrieval uses the intended `memory_ids` and the Message component saves to the same memory.
- Keep `agent_id`, `session_id`, and `user_id` filters consistent between save and search.
- Verify message status: manually forgotten messages should be excluded from later results.
- Review memory size and forgetting policy when old entries disappear.

## MCP Retrieval

Symptoms:

- MCP `list_tools` returns no tools or auth errors.
- `ragflow_retrieval` searches the wrong datasets.
- Host mode works for one client but fails for another.

Checks:

- In self-host mode, provide an API key with access to intended datasets.
- In host mode, ensure each client supplies an API key/header; do not rely on a shared host key unless intentionally configured.
- Keep base URL, API key, and transport endpoint separate in configuration.
- Use `dataset_ids` and `document_ids` when the question should be restricted.
- If `dataset_ids` is empty, RAGFlow resolves all datasets accessible to the key, which may be broader than expected.
- For host mode, verify transport support and flags; streamable HTTP may not be appropriate for every host-mode deployment.

## Template Import and Export

Symptoms:

- Imported template loses layout or component params.
- Round-trip export changes component IDs.
- Graph edges and `components` downstream lists diverge.

Checks:

- Preserve `components` as the source of runtime truth.
- Preserve `graph` or `_layout` only for visual layout unless intentionally regenerating UI metadata.
- Check both visual graph edges and component `upstream`/`downstream` lists after conversion.
- Ensure `component_name` values match real component/tool classes.
- Run `scripts/inspect_agent_template.py` before import to list components, references, edge mismatches, and likely missing keys.

## Install and Source-Inspection Caveat

If a source checkout fails editable installation because package metadata names a missing top-level package, continue with source-level inspection where possible. Treat that as environment/install troubleshooting, not as an agent workflow runtime behavior.
