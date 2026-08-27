# Tools, Skills, and MCP

This reference covers how Kiln task execution exposes tools to models or runs a task through an MCP tool. It focuses on tool IDs, routing, interfaces, and session behavior. Deep RAG indexing, server endpoints, UI forms, and persisted project file operations route to sibling sub-skills.

## Tool ID formats

Kiln validates every `ToolsRunConfig.tools` entry as a `ToolId` string.

| Tool family | Format | Runtime owner |
|---|---|---|
| Built-in demo/API tools | `kiln_tool::add_numbers`, `kiln_tool::subtract_numbers`, `kiln_tool::multiply_numbers`, `kiln_tool::divide_numbers`, `kiln_tool::call_kiln_api` | Tool registry resolves directly. |
| Remote MCP tool | `mcp::remote::<server_id>::<tool_name>` | Project external tool server plus `MCPServerTool`. |
| Local MCP tool | `mcp::local::<server_id>::<tool_name>` | Project external tool server plus local MCP subprocess/session. |
| RAG tool | `kiln_tool::rag::<rag_config_id>` | Ready project RAG config; indexing/setup routes to rag-documents-data. |
| Kiln task as tool | `kiln_task::<server_id>` | Project external tool server of type `kiln_task`. |
| Skill tool | `kiln_tool::skill::<skill_id>` | Adapter resolves skills and exposes one combined `skill` function. |
| SDK unmanaged tool | `kiln_unmanaged::<slug>` | Supplied directly through `AdapterConfig.unmanaged_tools`; not resolved by `tool_from_id`. |

Helper functions in the datamodel include `build_rag_tool_id`, `build_kiln_task_tool_id`, `build_skill_tool_id`, `build_kiln_unmanaged_tool_id`, `mcp_server_and_tool_name_from_id`, `rag_config_id_from_id`, `skill_id_from_tool_id`, and `kiln_task_server_id_from_tool_id`.

## Tool registry routing

`tool_from_id(tool_id, task=None)` resolves tool IDs for a task execution.

- Built-in math and API tools resolve without a project except `call_kiln_api`, which requires `Config.shared().kiln_local_api_base_url()`.
- MCP and Kiln task tools require a `Task` with a parent project and matching `ExternalToolServer` in that project.
- RAG tools require a parent project and matching `RagConfig`.
- Skill tool IDs intentionally do not resolve via `tool_from_id`; the adapter handles them by loading skills and creating a single `SkillTool`.
- Unmanaged tool IDs are valid IDs but are not registry-resolved; supply corresponding `KilnToolInterface` objects through `AdapterConfig.unmanaged_tools`.

`tool_definitions_from_ids(tool_ids, task)` calls `tool_from_id` for each ID and returns OpenAI-compatible tool definitions. Failures are wrapped with the tool ID that failed.

## `KilnToolInterface`

Every executable tool implements:

```python
class KilnToolInterface:
    async def run(self, context=None, **kwargs): ...
    async def toolcall_definition(self): ...
    async def id(self): ...
    async def name(self): ...
    async def description(self): ...
```

`toolcall_definition()` returns an OpenAI-compatible function definition:

```python
{
    "type": "function",
    "function": {
        "name": "lookup_customer",
        "description": "Look up customer details.",
        "parameters": {"type": "object", "properties": {...}},
    },
}
```

`run(...)` returns `ToolCallResult(output: str, is_error=False, error_message=None)`. MCP application-level errors are returned to the model with `is_error=True`; schema/connection/programming errors raise.

`ToolCallContext` currently carries `allow_saving`, used by Kiln task tools so nested task calls honor the caller's saving policy.

## Built-in tools

Built-in IDs and function names:

| ID | Function name | Behavior |
|---|---|---|
| `kiln_tool::add_numbers` | `add` | Add `a + b`. |
| `kiln_tool::subtract_numbers` | `subtract` | Subtract `b` from `a`. |
| `kiln_tool::multiply_numbers` | `multiply` | Multiply `a * b`. |
| `kiln_tool::divide_numbers` | `divide` | Divide `a / b`; raises on zero divisor. |
| `kiln_tool::call_kiln_api` | `call_kiln_api` | Call the configured local Kiln REST API. Endpoint schemas and UI/server details route to server-desktop-web-api. |

Math tools are safe local demonstrations. `call_kiln_api` can trigger real server operations, including long SSE flows; use only after loading the endpoint-specific server guidance.

## Tools in LiteLLM adapter runs

For `kiln_agent` runs, `LiteLlmAdapter`:

1. Resolves registry tools from `ToolsRunConfig.tools`, excluding skill IDs.
2. Resolves skill IDs through `AdapterConfig(skills=...)` and appends one combined `SkillTool` if any are present.
3. Appends `AdapterConfig.unmanaged_tools` definitions.
4. Verifies all tool function names are unique.
5. Sends tool definitions as LiteLLM `tools` with `tool_choice="auto"`.
6. Executes requested normal tool calls internally unless `AdapterConfig.return_on_tool_call=True`.
7. Validates tool-call arguments against each tool's JSON schema before calling `run(...)`.
8. Adds tool results back into the model trace and continues until the model returns final content, requests a `task_response` structured-output tool, or exceeds guardrails.

Guardrails:

- Maximum top-level turns per run: 10.
- Maximum tool-call iterations per turn: 30.
- A model cannot return `task_response` and normal tool calls in the same turn; the adapter raises because that would both end the turn and require continuing it.

Structured output mode caveat: `function_calling` and `function_calling_weak` use the same OpenAI `tools` field to force `task_response`. If normal tools are also enabled, choose another structured output mode such as `json_schema`, `json_mode`, or `json_instructions`.

## Skills as tools

Skill tool flow:

- Put skill IDs in `ToolsRunConfig` as `kiln_tool::skill::<skill_id>`.
- Call `load_skills_for_task(task, run_config)` once at orchestration time.
- Pass the result into `AdapterConfig(skills=skills)`.
- The adapter appends a system prompt section listing available skills and exposes a single `skill` function to load instructions/resources.

The combined skill function:

- Is named `skill`.
- Requires `name` and optional `resource` arguments.
- Enforces progressive disclosure: call `skill(name)` first; only request resources that the skill instructions list.
- Allows resources only under `references/` or `assets/` within the loaded skill.
- Rejects missing skills, invalid resource prefixes, missing filenames, path traversal, and absent resources with readable errors.

Common error: `Run config references skills but no skills dict was provided via AdapterConfig(skills=...).` Recovery: preload with `load_skills_for_task` and pass the dict into `AdapterConfig`.

## `KilnTaskTool` routing

A Kiln task tool wraps one task as a function. The external tool server of type `kiln_task` stores:

- `task_id`
- `run_config_id`
- tool `name`
- tool `description`
- archive flag

Tool ID format is `kiln_task::<server_id>`.

At call time, `KilnTaskTool`:

1. Resolves the project by ID.
2. Loads the target task and saved run config.
3. Converts tool arguments into task input:
   - If the target task has `input_json_schema`, kwargs are passed as structured input.
   - Otherwise, it expects an `input` string argument.
4. Preloads skills for the target run config.
5. Calls `adapter_for_task` for the target task with `AdapterConfig(default_tags=["tool_call"], allow_saving=context.allow_saving, skills=..., task_run_config_id=...)`.
6. Returns the nested run output plus `kiln_task_tool_data` tracing project/tool/task/run IDs.

Use project-datamodel for creating/saving the external tool server and target task. Use this sub-skill when diagnosing run-time nested task invocation, tool arguments, or adapter selection.

## RAG tool routing level

RAG tool ID format is `kiln_tool::rag::<rag_config_id>`.

`RagTool` exposes a `query` string parameter to search an already configured vector store and return formatted chunks. It may use an embedding adapter and reranker depending on the project RAG config and vector store type.

This sub-skill covers only how the ready RAG tool is added to `ToolsRunConfig` and resolved by `tool_from_id`. Route these details to rag-documents-data:

- document ingestion and extraction
- chunking strategy
- embedding config creation
- LanceDB/vector-store setup
- reranker config and provider setup
- fixing missing indexed content
- content search quality

Gotcha: LanceDB-backed imports can require `pandas` through vector-store dependencies. That is an environment/troubleshooting concern for RAG workflows, not a reason to change tool IDs.

## MCP tool IDs and sessions

MCP tool IDs encode server type, server ID, and tool name:

```text
mcp::remote::<server_id>::<tool_name>
mcp::local::<server_id>::<tool_name>
```

`MCPServerTool` behavior:

- Builds the ID as remote MCP for server-backed tools it wraps.
- Loads tool properties from the MCP server's `list_tools()` result.
- Uses the MCP tool's `inputSchema` as OpenAI function parameters, defaulting to an empty object schema if absent.
- Returns structured MCP content as JSON text when `structuredContent` is a dict.
- Returns single text content blocks directly.
- Converts MCP application errors into `ToolCallResult(is_error=True)` so the model can recover.
- Raises if a tool is missing, structured content is invalid, content is empty, the first content block is not text, or multiple content blocks are returned where one text block is expected.

### Remote MCP server properties

Remote MCP external tool servers require:

- `server_url` beginning with `http://` or `https://`.
- Optional `headers`.
- Optional `secret_header_keys`; secret values are saved separately in `Config` under `mcp_secrets`.

At session time, regular headers and retrieved secret headers are merged. Missing or invalid `server_url` fails before connection.

### Local MCP server properties

Local MCP external tool servers require:

- `command` as a non-empty string.
- Optional `args` list.
- Optional `env_vars` dict with valid environment variable names.
- Optional `secret_env_var_keys`; secret values are saved separately in `Config` under `mcp_secrets`.

Local sessions run through stdio with a working cache directory managed by Kiln. If no `PATH` is supplied in `env_vars`, Kiln builds one from `CUSTOM_MCP_PATH`/`custom_mcp_path` or the user's shell PATH. Use `CUSTOM_MCP_PATH` when local MCP commands such as `npx` are not found.

### Session cache

`MCPSessionManager` caches sessions by:

```text
<server_id>::<agent_run_session_id>
```

- Root adapter invocations create an agent run ID when none exists.
- MCP tool calls reuse cached sessions during that agent run.
- Root invocation cleanup closes all sessions for that run ID in safe order.
- Direct `McpRunConfigProperties` execution also creates a run context while invoking the tool, then cleans it up.

An MCP tool call outside an agent run context is considered a bug for actual calls. Property inspection can use a temporary client without cached run context.

## MCP direct task execution vs MCP as an agent tool

| Pattern | Run config | Model provider call? | Conversation? | Use when |
|---|---|---|---|---|
| MCP as agent tool | `KilnAgentRunConfigProperties(tools_config=...)` | Yes | Model can decide when/how to call tool. | The model should reason with tool results. |
| MCP direct task | `McpRunConfigProperties(tool_reference=...)` | No | Single tool call with synthetic user/assistant trace. | The task is exactly a wrapper around one MCP tool. |

## Unmanaged SDK tools

Use `UnmanagedKilnTool` or another `KilnToolInterface` object when a caller wants to inject tool definitions directly into an adapter without storing them in the project registry.

Rules:

- Tool ID format is `kiln_unmanaged::<slug>`.
- Slug must be non-empty and cannot contain `::`.
- Provide the actual tool object via `AdapterConfig.unmanaged_tools`.
- Names must not collide with registry tools or the combined `skill` tool.
- If `return_on_tool_call=True`, the adapter returns pending tool calls and the caller must execute tools and resume with prior trace.
- If `return_on_tool_call=False`, the adapter expects executable `run(...)` implementations.

## Evidence notes

Repo-relative source evidence: `libs/core/kiln_ai/datamodel/tool_id.py`, `libs/core/kiln_ai/datamodel/external_tool_server.py`, `libs/core/kiln_ai/tools/base_tool.py`, `libs/core/kiln_ai/tools/tool_registry.py`, `libs/core/kiln_ai/tools/kiln_task_tool.py`, `libs/core/kiln_ai/tools/skill_tool.py`, `libs/core/kiln_ai/tools/rag_tools.py`, `libs/core/kiln_ai/tools/mcp_server_tool.py`, `libs/core/kiln_ai/tools/mcp_session_manager.py`, built-in tool implementations, and tool tests.
