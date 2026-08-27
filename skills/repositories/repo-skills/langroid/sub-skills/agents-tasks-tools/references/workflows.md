# Workflows

This file turns the API surface into repeatable flows.
Use the smallest workflow that solves the problem.

## 1. Choose the right primitive

| Need | Use | Why |
| --- | --- | --- |
| LLM should request a local method on the same agent | `ToolMessage` + `enable_message` | Fastest path for tool use |
| LLM should send to another agent | `RecipientTool`, `ForwardTool`, or `SendTool` | Explicit routing |
| LLM should spawn a helper agent | `TaskTool` | Isolated delegation with its own task |
| Task should stop with a string result | `DoneTool` | Simple termination |
| Task should stop with structured data | `ResultTool` or `FinalResultTool` | Preserve typed payloads |
| Task should stop after a specific event pattern | `done_sequences` | Precise termination logic |
| Need exact code or whitespace preservation | `XMLToolMessage` | XML plus verbatim fields |
| Need deterministic tests | `MockLM` | No provider keys, no network |
| Need many items processed in parallel | Batch helpers | Reuse one agent or task across inputs |

## 2. Single-agent tool flow

Use this when a single agent can answer with a tool and then continue normally.

1. Define a `ToolMessage` subclass.
2. Add an agent method with the same name as the tool `request`, or define `handle()` / `response()` on the tool.
3. Call `agent.enable_message(MyTool)`.
4. Wrap the agent in a `Task`.
5. For tests, point `MockLMConfig.response_dict` at the tool JSON.

Minimal shape:

```python
class LookupTool(ToolMessage):
    request = "lookup"
    purpose = "Look up a value"
    key: str

class MyAgent(ChatAgent):
    def lookup(self, msg: LookupTool) -> str:
        return f"value={msg.key}"
```

Common checks:

- the tool `request` matches the handler name
- `enable_message` was called before `Task(...)`
- the response is valid JSON or XML for the selected tool mode

## 3. Stateless tool flow

Use this when the tool does not need agent state.

1. Put the logic in `ToolMessage.handle()`.
2. Call `agent.enable_message(MyTool, handle=True)`.
3. Keep the agent thin; do not duplicate handler logic.

This is the shortest path for pure transformations or small utility tools.

## 4. Stateful tool flow

Use this when the tool needs agent memory, counters, or stored context.

1. Define the tool schema.
2. Add a matching method on a `ChatAgent` subclass.
3. Enable the tool on the agent.
4. Use `Task` to drive the conversation.

This is the preferred pattern for agent state that should stay outside the tool class.

## 5. Routing flow

Use routing tools when the model must choose a recipient explicitly.

### Recommended routing flow

1. Enable `RecipientTool`.
2. Keep `recognize_recipient_in_content=True` only if text routing is intended.
3. Use `require_recipient=True` if a recipient is mandatory.
4. Prefer tool-based routing over raw text routing when debugging.

### Text routing fallback

- `TO[recipient]: content` and JSON recipient hints can be parsed from text.
- `recognize_recipient_in_content=False` disables that parsing.
- `TaskConfig.recognize_string_signals=False` disables `DONE` / `PASS` / similar text signals.

If the flow is hard to debug, switch to explicit orchestration tools instead of text parsing.

## 6. Termination flow

Use the lightest termination rule that matches the task.

### Simple cases

- `single_round=True` for one exchange
- `done_if_tool=True` when any tool should end the task
- `DoneTool` when the LLM or handler should end the task explicitly

### Precise cases

- use `done_sequences` when termination must depend on a pattern of events
- prefer `T[ToolClass], A` when the exact tool matters
- use `ResultTool` / `FinalResultTool` when the result should carry structured payloads

### Example: tool then handler

```python
config = TaskConfig(done_sequences=["T[MyTool], A"])
```

### Example: nested result

```python
class AnswerTool(FinalResultTool):
    answer: int
```

Use `FinalResultTool` when parent tasks should also terminate.
Use `ResultTool` when only the current task should terminate.

## 7. Task delegation flow

Use `TaskTool` when the main agent should delegate a sub-problem to a helper task.

Recommended sequence:

1. Keep the parent agent aware of every tool the helper might need.
2. Enable those tools on the parent even if the parent should not use them directly.
3. Enable `TaskTool` on the parent.
4. Give the child a clear `system_message`, `prompt`, and tool list.
5. Keep the child non-interactive.

Good defaults:

- `tools=["ALL"]` when the helper may use any parent-known allowed tool
- `tools=["NONE"]` when the helper should be isolated
- `agent_name` when logs need a readable name

Remember that the child can only use tools already known to the parent.

## 8. Structured-output flow

Use this when you want a typed answer rather than free-form text.

### Pattern A: strict copy

```python
strict_agent = agent[MyType]
response = strict_agent.llm_response_forget(prompt)
value = agent.from_ChatDocument(response, MyType)
```

### Pattern B: explicit output format

```python
agent.set_output_format(MyType)
```

Use this pattern when the output must remain typed across steps or when the model should emit a structured payload instead of prose.

## 9. XML tool flow

Use XML tools when JSON escaping is painful, especially for code.

1. Subclass `XMLToolMessage`.
2. Mark code or raw text fields as verbatim.
3. Keep `use_tools=True` and `use_functions_api=False`.
4. Use native tools mode.

This is a strong fit for code generation, file-writing payloads, or any field that should preserve whitespace exactly.

## 10. Batch flow

Use batch helpers when the same agent or task should run on many items.

### Task batches

- `run_batch_tasks(task, items, ...)` clones the task for each item.
- use `output_map` to convert `ChatDocument` objects into caller-friendly values.
- `stop_on_first_result=True` returns the first non-`None` mapped result and cancels the rest.

### Agent-method batches

- `run_batch_agent_method(agent, method, items, ...)` is the general async helper.
- `llm_response_batch` and `agent_response_batch` are convenience wrappers.

### Pure-function batches

- `run_batch_function` is for deterministic functions with no agent state.

## 11. MockLM testing flow

Use `MockLM` when the test should be repeatable.

Recommended pattern:

1. Build the tool JSON with `response_dict`.
2. Use `default_response` as the fallback.
3. Keep `use_tools=True` and `use_functions_api=False` for native tools.
4. Set `interactive=False`.
5. Disable logging when the test should stay clean.

MockLM is the best first stop when a tool path or termination path misbehaves.

## 12. Debugging flow

When something fails, debug in this order:

1. Is the tool name / request correct?
2. Was the tool enabled on the agent?
3. Is the handler on the agent or on the tool class?
4. Is the tool JSON / XML valid?
5. Is the task stopping for the right reason?
6. Is routing explicit, or are you relying on text parsing?
7. Does the test need MockLM instead of a provider-backed model?

If the issue smells like provider setup, move to the provider skill instead of continuing here.
