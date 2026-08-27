# Agent Construction Troubleshooting

Use this guide for ADK Python agent construction failures and behavior surprises.

## Constructor Raises On `generate_content_config`

Symptoms:

- `ValueError: All tools must be set via LlmAgent.tools.`
- `ValueError: System instruction must be set via LlmAgent.instruction.`
- `ValueError: Response schema must be set via LlmAgent.output_schema.`

Fix:

```python
from google.adk import Agent
from google.genai import types

root_agent = Agent(
    name="fixed_agent",
    instruction="System behavior goes here.",
    tools=[my_tool],
    output_schema=MyOutputSchema,
    generate_content_config=types.GenerateContentConfig(temperature=0),
)
```

Rules:

- Move `tools` out of `GenerateContentConfig` and into `Agent(tools=[...])`.
- Move system prompt text to `instruction` or `static_instruction`.
- Move final JSON/response structure to `output_schema`.
- Keep provider generation knobs such as temperature and safety settings in `generate_content_config`.

## Invalid Agent Name

Symptoms:

- Validation error saying an agent name must be a valid identifier.
- Validation error saying `user` is reserved.

Fix:

- Use names like `support_agent`, `order_collector`, or `researcher`.
- Avoid spaces, hyphens, leading digits, and `user`.
- Keep names stable because tools, delegation, state, and event authors refer to them.

## Root Agent Mode Error

Symptom:

- `ValueError: LlmAgent as root agent must have mode='chat'`.

Cause:

- A root `Agent` passed to `Runner` was set to `mode="task"` or `mode="single_turn"`.

Fix:

- Make the root a chat coordinator.
- Put `task` and `single_turn` agents under `sub_agents` so ADK exposes them as tools.

```python
helper = Agent(name="extractor", mode="single_turn", description="Extracts data.")
root_agent = Agent(name="coordinator", sub_agents=[helper])
```

## `output_schema` And Tool Calls Seem To Conflict

Symptoms:

- Model returns prose when JSON was expected.
- Structured output parsing fails.
- User expects the schema to be configured in `GenerateContentConfig`.

Facts:

- In ADK 2.3.0, `output_schema` and `tools` can be used together.
- Tools are available during the thought loop; final output is validated against `output_schema`.
- `generate_content_config.response_schema` is rejected for `LlmAgent`.
- With `output_key`, ADK parses structured final text before saving to session state.

Fixes:

- Put the schema on `Agent(output_schema=...)`.
- In the instruction, explicitly ask for final JSON matching the schema.
- Keep tool outputs as dictionaries with stable keys.
- If a final response is empty during streaming, do not treat it as a schema failure until the final non-empty response is known.

## Missing Model Or Provider Credentials

Symptoms:

- Construction succeeds but execution fails when the model is called.
- Errors mention API keys, OAuth, ADC, model provider credentials, or unavailable local model servers.

Fixes:

- Separate constructor validation from execution validation.
- Specify `model` explicitly for predictable provider selection.
- Ensure the selected provider's credentials/environment are configured before running the agent.
- For local providers, verify the local server is running and the model name matches that provider.
- Do not add credentials or machine-specific paths to reusable skill content or source files.

## Optional Extras Missing

Symptoms:

- Import errors mention optional packages such as database, extensions, MCP, or cloud libraries.
- Errors suggest installing extras like `google-adk[db]`, `google-adk[extensions]`, or `google-adk[mcp]`.

Fixes:

- Treat missing optional extras as environment facts, not agent-construction blockers.
- For toolsets/auth/MCP/cloud integrations, route to `tools-and-integrations`.
- For database sessions or persistent runtime services, route to `runtime-services`.
- Keep base agent definitions importable without optional integrations when possible.

## Sub-Agent Transfer Does Not Work

Symptoms:

- Parent cannot transfer to a child.
- A `single_turn` or `task` child appears only as a tool.
- Transfer target name is not found.

Facts:

- `chat` children are conversational delegation/transfer candidates.
- `single_turn` children are exposed as tools and are not direct transfer targets.
- `task` children are exposed as tools and must complete through `finish_task`.
- Child `description` fields guide parent delegation decisions.

Fixes:

- Use `mode="chat"` for child agents that should hold ongoing conversation.
- Use `mode="single_turn"` for helper calls that return immediately.
- Use `mode="task"` for delegated jobs with explicit completion.
- Check name spelling and case.
- Make descriptions concrete: "Collects payment details" is better than "Helper".

## Child Agent Lacks Context

Symptoms:

- A child says it does not know facts discussed with the parent.
- A `single_turn` helper ignores earlier turns.
- A task child receives a vague `request` and misses constraints.

Facts:

- Sub-agent execution uses branch isolation.
- `single_turn` agents in sub-agent/tool contexts normally operate on immediate input and no prior history.
- A sub-branch may read parent events when configured for history, but the parent cannot read child internal chatter as normal parent history.

Fixes:

- Pass required facts explicitly through `input_schema` fields such as `request`, `constraints`, and `known_context`.
- Set `include_contents="default"` only when the child truly needs parent conversation history.
- Update the parent instruction to pass relevant context when calling the child tool.
- Use `output_key` or explicit tool results when parent/child coordination depends on structured state.

## Callback Order Is Surprising

Symptoms:

- Agent callback does not run.
- A plugin callback overrides an agent callback.
- A callback list stops earlier than expected.

Facts:

- Plugin callbacks run before agent callbacks for agent, model, and tool phases.
- Callback lists run in list order.
- The first callback that returns a non-`None` override ends that phase's callback chain.
- Returning an empty dict can be falsy in some before/after tool handling paths; return a non-empty dict for intentional override.

Fixes:

- Return `None` to continue.
- Return `LlmResponse` from model callbacks only when replacing/skipping the model call.
- Return `types.Content` from agent callbacks only when skipping/appending agent output.
- Return a non-empty dict from tool callbacks to replace a tool response.
- Log or add temporary state markers when debugging callback order in local tests.

## Tool Error Callback Does Not Catch A Failure

Symptoms:

- A tool exception propagates despite `on_tool_error_callback`.
- The model sees a generic tool failure.
- A callback returns a string and the function response is malformed.

Fixes:

- Use the exact callback shape:

```python
def on_tool_error_callback(tool, args, tool_context, error):
  return {"error": f"{tool.name} failed: {error}"}
```

- Return a dict, not a bare string.
- Return `None` only when the original exception should propagate.
- Remember plugin `on_tool_error_callback` runs before agent callbacks.
- Missing tool names can also invoke error callbacks; include the `tool.name` in diagnostic responses.

## Task Agent Never Finishes

Symptoms:

- Parent remains suspended after calling a task child.
- Task agent asks repeated questions or keeps using tools.
- No final structured result reaches the parent.

Facts:

- `mode="task"` adds the built-in `finish_task` tool.
- The task agent must call `finish_task` when the job is complete.
- If `output_schema` is set, `finish_task` validates the output and lets the model retry on validation errors.

Fixes:

- Put explicit completion criteria in the task agent instruction.
- Mention `finish_task` in the instruction for final output.
- Add an `output_schema` that matches the expected parent input.
- Keep `input_schema` narrow so the parent passes complete, valid task inputs.

## `output_key` Not Written

Symptoms:

- Expected session state key is absent.
- A transferred sub-agent generated text, but the current agent did not save it.
- Final event contained only function calls/responses.

Facts:

- `output_key` is written only for final responses authored by that agent.
- ADK skips saves for events authored by another agent.
- ADK skips function-response-only events with no text parts.
- With `output_schema`, final text must parse successfully before state is saved.

Fixes:

- Put `output_key` on the agent that authors the final response.
- Ensure the final response contains text, not only a tool function response.
- Use a parent `after_tool_callback` or explicit state updates if the parent must store a child tool result.
- For structured output, make the final response JSON-only and schema-conformant.

## Safe Debugging Procedure

1. Run `scripts/inspect_agent_api.py` to confirm installed signatures.
2. Construct the agent object without a runner or model call.
3. Confirm imports do not require optional extras unless the feature truly needs them.
4. Check constructor field placement: `tools`, `instruction`, and `output_schema` must be agent fields.
5. Check mode placement: root chat, child task/single-turn helpers.
6. Check callback return types and order.
7. Only then run a local in-memory or mock-model execution path; route runtime services and evals to their sub-skills.
