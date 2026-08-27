# Agents And Workflows Troubleshooting

Use this guide when an agent does not call tools, calls the wrong tool, loops, hands off incorrectly, fails streaming, or loses conversation context.

## LLM Does Not Support Function Calling

Symptoms:

- `ValueError: LLM must be a FunctionCallingLLM`.
- Tool schemas are ignored and the model writes plain text instead of tool calls.
- `FunctionAgent` works with one provider but not another.

Fixes:

1. Use an LLM integration whose metadata marks it as function-calling capable.
2. Switch to `ReActAgent` for text-only models that can follow the ReAct prompt format.
3. If the provider only fails during streaming tool calls, set `FunctionAgent(..., streaming=False)`.
4. Keep provider installation/configuration in the integrations sub-skill; do not bake provider keys into reusable agent code.

## Tool Is Not Selected

Symptoms:

- The agent answers from prior knowledge instead of using a tool.
- The wrong tool handles a request.
- Tool arguments are missing or too broad.

Fixes:

1. Rename the tool with a task-specific verb and noun, such as `search_policy_handbook` instead of `query`.
2. Add an explicit `description` that says when to use and when not to use the tool.
3. Add `Annotated` parameter descriptions or a Pydantic `fn_schema` for ambiguous fields.
4. Print `tool.metadata.get_parameters_dict()` and inspect what the model actually sees.
5. Put routing instructions in the agent `system_prompt`, not only in code comments.
6. For side-effectful tools, set `allow_parallel_tool_calls=False` on `FunctionAgent`.

## Tool Schema Or Description Is Too Vague

Symptoms:

- The model passes a dict where a string was expected.
- `QueryEngineTool` receives keyword blobs instead of a clean question.
- The same tool is called repeatedly with small variations.

Fixes:

- For `QueryEngineTool`, make the description say: "Input must be a complete natural-language question".
- Set `resolve_input_errors=False` during debugging so malformed inputs raise instead of being stringified.
- Split overloaded tools into smaller tools with mutually exclusive descriptions.
- Use `partial_params` to hide implementation-only arguments from schemas.
- Keep function return values concise and actionable; long raw dumps invite repeated calls.

## ReAct Scratchpad Or Reasoning Fails

Symptoms:

- Retry messages mention `Error while parsing the output`.
- Retry messages mention `FAILURE: Your previous response was empty`.
- The model emits malformed `Action Input` JSON.

Fixes:

1. Use `ReActAgent` only with models that can reliably follow text formats.
2. Add a system prompt reminding the model to use exactly `Thought`, `Action`, `Action Input`, or `Answer`.
3. Shorten tool descriptions so the ReAct prompt is not overwhelmed.
4. Disable streaming while debugging parser failures to inspect complete model outputs.
5. If custom ReAct parsing is needed, route that work to structured-output/customization guidance.

## Multi-Agent Handoff Goes To The Wrong Agent

Symptoms:

- A specialist answers an unrelated request.
- The root agent keeps handling tasks it should route.
- Handoff tool returns invalid-agent messages.

Fixes:

1. Check that each `FunctionAgent` has a unique exact `name`; handoff uses exact names.
2. Write agent `description` values as routing contracts: domain, inputs, exclusions.
3. Set `can_handoff_to` on every agent to remove invalid paths.
4. Make the root agent `system_prompt` list routing rules and examples.
5. Stream events and log `current_agent_name` to see where control changed.
6. If built-in handoff remains too autonomous, use an orchestrator agent with sub-agent tools instead.

Note: if `can_handoff_to` blocks a destination, the handoff tool returns an error-like message and control remains with the current agent. If the target name is unknown, the tool returns a string listing valid agents.

## Agent Loops Or Stops Too Early

Symptoms:

- `WorkflowRuntimeError: Max iterations of ... reached`.
- The same tool is called repeatedly.
- The answer is cut off before a final response.

Fixes:

1. Lower `max_iterations` during debugging so loops fail quickly.
2. Inspect `ToolCallResult.tool_output.is_error`; tool exceptions are converted into tool outputs and may trigger retries.
3. Use `early_stopping_method="generate"` to ask the active agent for a final answer instead of raising at the limit.
4. Make terminal tools `return_direct=True` only when their output is sufficient as the final answer.
5. Add system prompt rules for when to stop calling tools.

## Streaming Fails Or Produces No Tokens

Symptoms:

- Provider raises a streaming-related error.
- Final result exists but no `AgentStream` deltas appear.
- Chat engine stream history is incomplete because the stream was not consumed.

Fixes:

1. Set `streaming=False` on the agent if the LLM integration does not support streaming tool calls.
2. Always drain `async for event in handler.stream_events()` before awaiting `handler` in examples that demonstrate streaming.
3. For query engines, enable streaming when constructing the query engine; for chat engines, use `stream_chat()` and consume `response_gen`.
4. Print event class names while debugging; not every event has a text delta.
5. If a streaming response is empty, inspect the provider response and model capability before changing workflow logic.

## Memory Token Limits Or Lost Context

Symptoms:

- Earlier chat turns disappear.
- The model ignores memory facts.
- Context grows until provider token errors occur.

Fixes:

1. Pass an explicit `ChatMemoryBuffer.from_defaults(token_limit=...)` to `run()` for predictable tests.
2. Use `Memory(token_limit=..., token_flush_size=...)` for newer waterfall memory behavior.
3. Keep `token_flush_size` materially smaller than `token_limit`.
4. Summarize or index large tool outputs instead of storing them verbatim in chat history.
5. Use separate memory instances for separate user sessions.

## return_direct Surprises

Symptoms:

- The agent returns the raw tool output without synthesis.
- Handoff appears to stop the loop.
- The model never explains the tool result.

Fixes:

- `return_direct=True` ends the loop for successful non-handoff tools.
- The reserved `handoff` tool also uses direct-return mechanics internally, but `AgentWorkflow` continues after setting the next agent.
- Use `return_direct=False` when the agent should rewrite, compare, cite, or follow up after a tool call.
- If direct tool output is unsafe or too verbose, add a callback or wrapper tool that normalizes it first.

## Human-In-The-Loop Stalls

Symptoms:

- `handler` never completes.
- Stream shows an input-required event and then waits forever.

Fixes:

1. Watch `handler.stream_events()` for `InputRequiredEvent`.
2. Reply with `handler.ctx.send_event(HumanResponseEvent(...))` matching the expected requirements.
3. Use unique `waiter_id` values for independent waits.
4. Persist or serialize workflow context if human input may arrive much later.

## Safe Debug Checklist

- Confirm imports from `llama_index.core.agent.workflow`, `llama_index.core.tools`, `llama_index.core.memory`, and `llama_index.core.workflow`.
- Print tool metadata before running an agent.
- Run a tool directly before wrapping it in an agent.
- Run a query engine directly before converting it to `QueryEngineTool`.
- Temporarily set `streaming=False`, `allow_parallel_tool_calls=False`, and low `max_iterations` to isolate failures.
- Consume stream events and inspect `ToolCallResult` rather than relying only on the final response.
