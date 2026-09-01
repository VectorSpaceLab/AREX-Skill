# Chat tools, schema, and provider fallback

## User Persona
A developer migrating an OpenAI-shaped chat workflow to hosted Hub inference,
with an emphasis on structured output and controlled tool execution.

## Scenario Coverage
- Skill area: `inference-and-endpoints`
- Capability: provider/task selection, chat tools, JSON schema, sync/async
  streaming, fallback, MCP optional dependency
- Difficulty: advanced
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/inference-and-endpoints/SKILL.md`,
  `sub-skills/inference-and-endpoints/references/task-types.md`,
  `sub-skills/inference-and-endpoints/references/providers-and-tasks.md`,
  `sub-skills/inference-and-endpoints/references/workflows.md`,
  `sub-skills/inference-and-endpoints/scripts/mock_chat_recovery.py`
- Trigger expectation: chat/tool/schema/provider language should select this
  route, not local model training or generic Hub operations.

## Expected Successful Behavior
The response should choose a model/provider explicitly, validate JSON schema and
function arguments independently of the model, explain `response_format`,
`tool_choice`, stream chunks and async cancellation/cleanup, use one bounded
fallback after a typed unsupported-task/provider error, and state that MCP
requires the `mcp` extra and a narrow allowlist. The mock must make no network
request.

## Failure Signals
Executing tools without argument validation, assuming every stream chunk has
content, retrying paid inference indefinitely, treating `torch` as required,
leaking tokens, or claiming provider support without checking the matrix would
fail this case.
