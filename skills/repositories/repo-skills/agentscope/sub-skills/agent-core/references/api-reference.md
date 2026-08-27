# API Reference

## Purpose

Read this when you need the verified AgentScope SDK surface for agent construction, tool wiring, local skills, or reply/event handling.

## Verified public entry points

### Agent and config objects

| Symbol | Verified signature / note |
| --- | --- |
| `Agent` | `Agent(name, system_prompt, model, toolkit=None, middlewares=None, state=None, offloader=None, model_config=None, context_config=None, react_config=None, injection_config=None)` |
| `Agent.reply` | `reply(inputs=None, structured_schema=None) -> Msg` |
| `Agent.reply_stream` | `reply_stream(inputs=None, structured_schema=None, yield_final_msg=False) -> AsyncGenerator[...]` |
| `ContextConfig` | `ContextConfig(trigger_ratio=0.8, reserve_ratio=0.1, compression_prompt=..., summary_template=..., summary_schema={}, tool_result_limit=50000)` |
| `InjectionConfig` | `InjectionConfig(inject_runtime_state=True, timezone='UTC', time_format='%Y-%m-%dT%H:%M:%S', time_interval=0.5, context_buffer_ratio=0.2, template=..., injection_source=..., task_tool_names=[], extra_fields={}, emit_hint_event=True)` |
| `ModelConfig` | `ModelConfig(max_retries=0, fallback_model=None)` |
| `ReActConfig` | `ReActConfig(max_iters=20, structured_output_grace_iters=5, stop_on_reject=False, interruption_message=..., interruption_raise_cancelled_error=False)` |

### Toolkit and tool plumbing

| Symbol | Verified signature / note |
| --- | --- |
| `Toolkit` | `Toolkit(tools=None, skills_or_loaders=None, mcps=None, tool_groups=None, meta_tool_response_template=..., skill_instruction_template=...)` |
| `ToolGroup` | `ToolGroup(name, description=None, instructions=None, tools=None, skills_or_loaders=None, mcps=None)` |
| `FunctionTool` | Wraps a callable or async callable into a tool; accepts `name`, `description`, safety flags, and optional middlewares. |
| `MCPTool` | Wraps an MCP tool from a live client/session. |
| `ToolBase` | Base constructor takes only `middlewares=None`; concrete tools provide their own behavior. |
| `LocalBackend` | Zero-argument local filesystem/process backend for built-in tools. |

### Skill loading

| Symbol | Verified signature / note |
| --- | --- |
| `Skill` | `Skill(name, description, dir, markdown, updated_at)` |
| `SkillLoaderBase` | Abstract base for skill loaders. |
| `LocalSkillLoader` | `LocalSkillLoader(directory, scan_subdir=False)` |

### Built-in tools exported from `agentscope.tool`

`agentscope.tool.__all__` exports: `ToolChoice`, `Function`, `ToolBase`, `ParamsBase`, `ToolMiddlewareBase`, `MCPTool`, `FunctionTool`, `ToolGroup`, `Toolkit`, `ToolChunk`, `ToolResponse`, `RegisteredTool`, `BackendBase`, `LocalBackend`, `DirEntry`, `ExecResult`, `ResetTools`, `Bash`, `PowerShell`, `Edit`, `Glob`, `Grep`, `Read`, `Write`, `TaskUpdate`, `TaskGet`, `TaskList`, `TaskCreate`.

Important note: `SkillViewer` is not exported from `agentscope.tool`; use `Toolkit(..., skills_or_loaders=...)` and the skill-instruction flow instead.

### Message, event, permission, and state contracts

You usually do not need the full schemas to start using the SDK, but the verified constructors are:

- `Msg(name, content, role, id=<factory>, metadata={}, created_at=<factory>, usage=None, finished_at=None, finished_reason=None, structured_output=None, error=None)`
- `UserMsg(name, content, metadata=None, created_at=None, finished_at=None, finished_reason=None, id=None)`
- `AssistantMsg(name, content, metadata=None, created_at=None, finished_at=None, finished_reason=None, structured_output=None, id=None, usage=None)`
- `SystemMsg(name, content, metadata=None, created_at=None, finished_at=None, finished_reason=None, id=None)`
- `TextBlock`, `ThinkingBlock`, `HintBlock`, `ToolCallBlock`, `ToolResultBlock`, `DataBlock`, `Base64Source`, `URLSource`
- `AgentState`, `TaskContext`, `PermissionContext`, `PermissionDecision`, `PermissionEngine`, `PermissionRule`

## Practical notes

- `reply_stream` yields the event classes that the tests assert against, including reply start/end, model-call, text/data/thinking/hint, tool-call/result, and interruption/confirmation events.
- `ContextConfig` and `InjectionConfig` are the first places to check when a conversation compresses too aggressively or the injected runtime-state reminder appears at the wrong cadence.
- `Toolkit` can compose plain tools, tool groups, MCP clients, and skill loaders; use the smallest mix that covers the workflow.
- A local skill path should contain a valid `SKILL.md` with `name` and `description` frontmatter.

## Best fit

Use this reference when you need the verified API names and constructor defaults before writing or debugging an agent workflow. If the problem is really provider-, retrieval-, service-, or workspace-specific, switch to the matching sub-skill after checking the signatures here.
