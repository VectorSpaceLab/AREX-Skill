# Testing patterns

Use these patterns when writing or debugging tests for Langroid agent/task/tool flows.
All examples assume deterministic, no-network setup unless a provider-backed case is
explicitly needed.

## 1. Basic tool-handler test

Pattern:

1. Define a `ToolMessage` subclass.
2. Add a matching handler method on a `ChatAgent` subclass or a `handle()` method on the tool.
3. Build `MockLMConfig.response_dict` so the prompt maps to valid tool JSON.
4. Call `agent.enable_message(MyTool)`.
5. Run `Task(..., interactive=False)`.
6. Assert the final `ChatDocument.content` and the tool extraction result.

What to assert:

- the returned content is the handler result
- `agent.get_tool_messages(response)` finds the custom tool
- the tool `request` matches the handler name

## 2. Testing `handle_llm_no_tool`

Use this when the LLM emits plain text after tools are enabled.

Good checks:

- `handle_llm_no_tool="done"` ends the task
- `handle_llm_no_tool="user"` passes control back to the user
- callable fallback returns an `AgentDoneTool` or `ResultTool` when appropriate
- a plain string fallback is treated as a reminder to the LLM

Remember:

- this only applies to LLM messages that contain no usable tool
- specialized agents may override the fallback path, so the config knob may be ignored there

## 3. Testing `done_sequences`

Use `MockLM` and a fixed response sequence to exercise task termination.

Useful assertions:

- `TaskConfig.done_sequences` starts as `None`
- a DSL string such as `"T[MyTool], A"` parses into the expected events
- class-name tool references resolve correctly
- a matching sequence stops the task after the intended event chain
- a non-matching sequence leaves the task running until another rule fires

High-value cases:

- any tool followed by handler: `T, A`
- specific tool by request name: `T[lookup], A`
- specific tool by class name: `T[LookupTool], A`
- content match: `C[done|finished]`

## 4. Testing routing

Use routing tests when message direction matters.

Checks to include:

- `RecipientTool` sets `metadata.recipient`
- `recognize_recipient_in_content=False` keeps text routing disabled
- `TaskConfig.recognize_string_signals=False` stops `DONE` / `PASS` parsing
- `require_recipient=True` makes the recipient explicit

A good failure test is a message that omits the recipient and must trigger the
`AddRecipientTool` clarification path.

## 5. Testing `TaskTool`

Use `MockLM` to return a `TaskTool` JSON payload that spawns a child task.

Checks to include:

- the parent agent has every tool the child might need
- the child task is non-interactive
- `DoneTool` is available to the child
- the child result reaches the parent as a `ChatDocument`

A strong negative test is to omit a parent-known delegated tool and confirm the child
cannot use it.

## 6. Testing structured output

Use both typed-copy and explicit output-format tests.

Suggested assertions:

- `agent[MyType]` returns a typed copy
- `agent.from_ChatDocument(response, MyType)` reconstructs the expected value
- `set_output_format(MyType)` changes the emission shape as intended
- nested `BaseModel` values survive the round trip

For small values, simple types are valid targets too:

- `int`
- `float`
- `bool`
- `str`

## 7. Testing XML tools

Use XML tools when you need to preserve code or whitespace.

Good checks:

- the tool parses from XML rather than JSON
- verbatim fields keep indentation and line breaks
- `use_tools=True` and `use_functions_api=False` are set together
- the tool works with a representative code payload

A good regression test is a payload with quotes, indentation, and blank lines.

## 8. Testing batch helpers

Batch tests should check ordering, cancellation, and exception handling.

Useful assertions:

- `run_batch_tasks` returns a list with the same length as the input list
- `stop_on_first_result=True` cancels later tasks after the first non-`None` mapped result
- `output_map` controls whether a raw result counts as usable
- `ExceptionHandling.RETURN_NONE` keeps the batch going
- `ExceptionHandling.RETURN_EXCEPTION` surfaces the exception object in the result list

Useful edge case:

- a fast task whose mapped result is `None` should not cancel slower valid tasks

## 9. Testing `MockLMConfig`

Prefer these fields:

- `response_dict`
- `response_fn`
- `response_fn_async`
- `default_response`

Do **not** use a `response` field; it is not part of the config surface used here.

High-value assertions:

- `response_dict` wins when the prompt matches exactly
- `response_fn` / `response_fn_async` provide fallback behavior
- `default_response` is used when nothing else matches

## 10. What makes a good regression case?

A good regression case should combine at least two of the following:

- tool enabling
- tool handling
- termination logic
- routing
- structured output
- batch execution
- fallback behavior

If a case only checks that a method exists, it is usually too shallow.
