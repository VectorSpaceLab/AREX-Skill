# Prompt and Output Parsing

## When to Read

Read this when an agent selects the wrong tool, a prompt variable is missing, or
an LLM response cannot be parsed into SuperAGI's action schema.

## Verified Prompt Helpers

`AgentPromptBuilder` provides these tested/static methods:

- `add_list_items_to_string(items)`
- `add_tools_to_prompt(tools, add_finish=True)`
- `_generate_tool_string(tool)`
- `clean_prompt(prompt)`
- `replace_main_variables(super_agi_prompt, goals, instructions, constraints,
  tools, add_finish_tool=True)`
- `replace_task_based_variables(super_agi_prompt, current_task, last_task,
  last_task_result, pending_tasks, completed_tasks, token_limit)`

The prompt builder formats goals, instructions, constraints, tool descriptions,
and task history into the final SuperAGI prompt text.

## Output Parsers

`AgentSchemaOutputParser.parse(response: str) -> AgentGPTAction`

- Accepts a text response that may be wrapped in triple backticks.
- Uses `JsonCleaner.extract_json_section` and boolean cleaning before applying
  `ast.literal_eval`.
- Expects a structure with `tool.name` and optional `tool.args`.

`AgentSchemaToolOutputParser.parse(response: str) -> AgentGPTAction`

- Similar to the main parser but expects a top-level `name` and optional `args`.

## Tool and Finish Formatting

- Tool strings are rendered as `"<tool name>": <description>, args json schema: ...`.
- The finish tool is always named `finish` and advertises a final response
  string.
- Tool names are normalized later by lowercasing and removing spaces during
  execution.

## Common Failure Shapes

- A response that is not JSON-like or not parseable after cleanup will raise an
  exception.
- A parsed tool name that does not match a registered tool will later become an
  unknown-tool error in `ToolExecutor`.
- Token-count logic can shorten task history or alter what the prompt carries
  forward if the token budget is tight.
