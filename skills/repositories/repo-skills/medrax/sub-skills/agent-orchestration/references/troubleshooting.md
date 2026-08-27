# Troubleshooting MedRAX orchestration

## Missing API key or endpoint URL

**Symptoms:** authentication errors on the first model invocation, a connection
failure, or requests being sent to the wrong provider.

1. Decide whether the endpoint is hosted or local. Set `OPENAI_API_KEY` for the
   selected provider; for a local compatible endpoint, use the non-secret
   placeholder its server expects.
2. If the endpoint is not the default OpenAI service, set `OPENAI_BASE_URL` to
   its complete compatible API root (commonly including `/v1`).
3. Build `openai_kwargs` only from variables that are present. Do not log the
   dictionary or place its values in a prompt, notebook output, or tool log.
4. Confirm the endpoint supports the configured chat model name and function/
   tool schemas. A generic chat completion can work while `bind_tools` or tool
   calls fail.

Use only utility tools while diagnosing transport. Endpoint troubleshooting does
not require downloading or importing optional chest-X-ray weights.

## Requested tools are silently omitted

**Symptoms:** `tools_dict` lacks a requested key, or no expected tool is bound.

The initializer tests every request against an internal registry and skips
nonmatching names without warning. Compare the requested set with
`set(tools_dict)` immediately after construction. Correct capitalization and
the `Tool` suffix using the registry in `api-reference.md`.

Do not call `initialize_agent` with `tools_to_use=[]` to mean “none.” The
implementation uses a falsy fallback, so that initializes all registry tools.
For a graph-only test, use the fake model workflow instead. For a real agent,
use the explicit nonempty utility pair `ImageVisualizerTool` and
`DicomProcessorTool`.

## Prompt file or section is missing

**Symptoms:** `FileNotFoundError`, `KeyError: 'MEDICAL_ASSISTANT'`, an empty
system prompt, or unexpectedly compact prompt text.

- Pass a readable prompt file with bracketed headers such as
  `[MEDICAL_ASSISTANT]`.
- `initialize_agent` accesses that exact section and therefore does not accept
  a prompt file containing only `[GENERAL_ASSISTANT]`.
- The parser strips lines and drops blank lines. Keep semantic paragraph breaks
  out of any logic that depends on exact whitespace.
- If using `load_system_prompt`, provide a known explicit section. Its missing
  section fallback is the literal text `GENERAL_ASSISTANT`, not the contents of
  that section.

Run `check_medrax_import.py --project-root . --json` to parse the project prompt
file and report discovered sections without initializing an agent.

## Checkpoint or `thread_id` error

**Symptoms:** LangGraph reports that a configurable key, thread ID, or
checkpoint identifier is missing; a later call has no remembered state.

Pass a configuration with a nonempty stable ID:

```python
config = {"configurable": {"thread_id": "case-004"}}
agent.workflow.invoke({"messages": messages}, config)
```

Reuse the same ID only for intentional continuation. Start a new ID for a fresh
case. `MemorySaver` only retains state in the running process; restarting the
program, changing process, or using an incompatible checkpointer loses that
state. For durable state, select and validate a persistent LangGraph
checkpointer separately.

## Model binding or tool-schema failure

**Symptoms:** failure during `Agent(...)`, an exception from `bind_tools`, the
provider rejects tool declarations, or the model emits malformed calls.

1. Reproduce the graph using the fake-model workflow; this distinguishes local
   Agent graph logic from provider compatibility.
2. Confirm that the model client supports LangChain's `bind_tools` and the
   endpoint accepts tool/function schemas.
3. Start with one simple utility tool. Do not import or construct GPU-oriented
   tools to debug a chat-model schema issue.
4. Validate exact selected names statically. If an AI response requests an
   unregistered name, the Agent returns `invalid tool, please retry` and sends
   that result back to the model; it does not execute arbitrary functions.
5. Ensure selected tools have unique `.name` values; the Agent's internal map
   uses name keys and later duplicates replace earlier entries.

For model-specific tool input/output schemas, route to `chest-xray-analysis`.

## Log directory cannot be written

**Symptoms:** `PermissionError`, `FileNotFoundError` for a nested folder, or no
expected tool log after an execution.

- Set `log_tools=False` for a no-filesystem synthetic smoke test.
- Otherwise choose a non-sensitive writable `log_dir`. The Agent calls
  `Path(log_dir or "logs").mkdir(exist_ok=True)` and does not create missing
  parents, so create a nested parent path yourself first.
- Logs are written only after the `execute` node, not after a pure text reply.
  A model response with no tool calls legitimately produces no tool-call JSON.
- Inspect the directory rather than assuming one timestamped filename. Two
  execution batches that finish in the same second can use the same filename.

Treat `args` and `content` as potentially sensitive data and protect or clean
operational logs according to the caller's data policy.

## Optional GPU tools must be excluded

**Symptoms:** an orchestration test tries to allocate GPU memory, import an
unavailable backend, look for weights, or start a download even though the task
only concerns agent plumbing.

Do not call the real initializer with `None`, `[]`, or an unfiltered tool list.
Validate the requested selection table before construction and choose only
`ImageVisualizerTool` plus `DicomProcessorTool` for a real no-weight smoke
case. For the strictest no-network/no-optional-import test, construct `Agent`
directly with the fake model and `StructuredTool` synthetic tool described in
`workflows.md`. This tests tool binding, state transitions, checkpoint config,
and logging without touching MedRAX tool constructors.
