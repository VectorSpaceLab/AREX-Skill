# Agents and AWEL troubleshooting

Use these checks in order: imports/signatures, construction, binding, local execution,
route registration, and only then service/provider execution. A successful import does
not prove that a model, remote connector, serving app, or GPU backend is usable.

## Agent construction and binding

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ProfileConfig` validation says name/role is missing | Plain `ConversableAgent` has no usable profile and no subclass profile | Supply `ProfileConfig(name=..., role=..., goal=...)`, or use a subclass with a class-level profile. |
| `Missing context in which agent is running` | `AgentContext` was not bound before `build()` | Bind `AgentContext(conv_id="...")`; check `agent.agent_context` before building. |
| `Model configuration is missing` / `LLM client is not initialized` | A normal non-human, non-team agent has no usable `LLMConfig.llm_client` | Configure a real provider in the models route, or use `UserProxyAgent`/a local non-model test that does not call `build()` as a model agent. Never replace the missing client with a fake success claim. |
| `missing action modules` | A non-human, non-team agent has no actions | Bind an action such as `ToolAction` or `BlankAction` where appropriate. A tool pack alone is not an action. |
| `Missing resources[ResourceType.Tool]` | An action declares a required resource but no matching pack is bound | Bind `ToolPack` before `build()` and verify `get_resource_by_type(ResourceType.Tool)`. |
| Skill is present but tools are unavailable | `Skill.required_tools` is descriptive and `bind(skill)` only sets prompt state | Resolve each exact tool name against the bound pack and fail with the missing names before generating a reply. |
| `GptsMemory is not supported! Please Use Agent Memory` | A conversation `GptsMemory` was bound directly | Wrap it in `AgentMemory`; use `GptsMemory` for conversation/plan records inside that wrapper. |
| Build performs unexpected I/O | `build()` preloads resources and recovers memory history | Use a pure construction check first; replace live resources with local fixtures and isolate the conversation ID/output directory. |
| Profile changes do not appear in the prompt | A cached/current profile or `bind_prompt` is overriding the expected template | Inspect `agent.current_profile`, `agent.bind_prompt`, `agent.language`, and call `build_prompt(...)`. Bind the intended `ProfileConfig`, `PromptTemplate`, or skill before building. |

Binding order is not a magical dependency resolver. The safe order is profile at
construction, then context, memory, resources, actions, skills/prompt, and LLM config,
followed by one awaited `build()`. `bind()` is synchronous; do not write
`await agent.bind(...)` unless the awaited expression is the final `build()` call:

```python
agent.bind(context).bind(tools).bind(ToolAction).bind(llm_config)
await agent.build()
```

## Tools, parser, and action errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `The description is required` | A decorated function has no docstring and no explicit description | Add a concise docstring or `@tool(description="...")`. |
| `args should be a dict of ToolParameter or dict` | Explicit tool arguments mix object and dict forms | Use all `ToolParameter` values or all mappings with `type`/description/default. |
| Tool schema has wrong type or no required list | Unclear annotations, `Annotated` handling, or a stale explicit schema | Inspect `function._tool.args` and `await function._tool.get_prompt(prompt_type="openai")`; make the pydantic `args_schema` and callable agree. |
| Sync tool raises `The function is asynchronous` | `execute()` was used for an async function | Use `await tool.async_execute(...)` or `await pack.async_execute(...)`. |
| Async tool raises `The function is synchronous` | `async_execute()` was called directly on a sync `FunctionTool` | Call `execute()` for the tool itself, or use `ToolPack.async_execute()` which supports both paths. |
| `No tool found for execution` | Tool name is not an exact key in the pack, often due to MCP prefixing | List pack resources and use the exact name, including `mcp__...` when ConnectorManager owns it. |
| Unexpected tool arguments disappear | `ToolPack` removes keys not present in `tl.args` | Validate argument keys before execution. Do not treat a successful call with filtered arguments as proof that the model supplied a correct schema. |
| `ToolExecutionException: Execution error` | Python function raised, required arg was absent, or pack selected the wrong execution path | Log the selected tool name and redacted argument keys, validate required fields, then reproduce with a tiny local call. |
| ToolAction returns a failed `ActionOutput` | Model output was not valid JSON for `ToolInput`, or fallback parsing did not find a safe expression | Preserve the failure and ask for structured `tool_name`/`args` JSON; do not interpret arbitrary text as code. |
| ReAct parser returns a string instead of an object | Action JSON is malformed | Fix the producer; `ReActOutputParser` intentionally keeps invalid JSON as raw text so the caller can report it. |

Do not use `eval`, shell expansion, or a remote tool to “repair” model arguments.
`FunctionTool.parse_execute_args` can implement a strict parser for a known input format;
raise a message naming the invalid field and expected type.

## Context and async behavior

| Symptom | Likely cause | Recovery |
|---|---|---|
| `DAGContext is not set` | An operator property was read outside a runner invocation | Read it inside `map`/`_do_run` or pass the context to `call(..., dag_ctx=...)`. |
| `This event loop is already running` | `_blocking_call()` was used from async code | Use `await leaf.call()`; reserve blocking helpers for synchronous debug entrypoints. |
| Coroutine is never awaited | A sync path directly called an async mapper/tool | Mark the caller async and await `call`, `map`, or `async_execute`; use the agent's blocking adapter for synchronous work. |
| Async generator is consumed twice or is empty | Streams are iterators, not reusable lists | Consume once, use `call_stream()`, or materialize intentionally in a bounded fixture. A reduce of an empty stream raises `ValueError("Stream is empty")`. |
| Event-loop-local DAGs interfere in concurrent tests | `DAGVar` uses thread/async-local stacks but system app/executor state can be shared | Use distinct DAG IDs, enter/exit each DAG with `with`, avoid mutable global nodes, and reset test process state when necessary. |
| Context is over budget | `used / (max_context_tokens - reserved_tokens)` reached a threshold | Lower prompt/memory/tool-result volume, increase a verified model budget, or enable context management with explicit thresholds. At warning it truncates/drops old rounds; at error it may summarize with an LLM; overflow can trigger reactive compaction. |
| Compaction status is absent | Context management is disabled or no callback was supplied | Set `enable_context_management`/call `init_context_management`, and provide an async status callback if live status is needed. |
| Compaction repeatedly fails | LLM summarizer unavailable or context too large | Preserve the failure, reduce messages, and inspect `circuit_breaker_tripped`; after the configured consecutive failures, do not claim further summarization. |

For deterministic tests use `ContextBudgetTracker` with a small explicit budget and
fake messages. Do not infer exact token counts from the rough four-character fallback.

## AWEL graph and execution

| Symptom | Likely cause | Recovery |
|---|---|---|
| Node has no ID / `Node id not set` | A node was created without a DAG/task ID and never attached, or was used before defaults applied | Construct inside `with DAG(...)` or pass `dag`/`task_id`; inspect `node.node_id`. |
| `Node name ... already exists` | Two nodes share `task_name` in one DAG | Give each node a unique stable name. Names are for lookup/serialization; IDs are separate. |
| `MapDAGNode expects single parent` | A map received multiple graph parents without a join | Insert `JoinOperator` or restructure the graph. An explicit end `call_data` is a separate input path, not a substitute for graph typing. |
| `ReduceStreamOperator expects stream data` | A normal value reached a stream reducer | Add a streamify operator or use a normal map/join. Ensure the upstream `TaskOutput.is_stream` is true. |
| `BranchDAGNode expects no stream data` | Branch predicate was applied to a stream | Reduce/materialize first or branch on a scalar. Set branch targets to named operators. |
| Shared join is skipped after a branch | Skip propagation or `can_skip_in_branch` was chosen incorrectly | Use a join that can remain active when one branch is skipped (`can_skip_in_branch=False` where required) and test both predicate outcomes. |
| Graph has no leaf or HTTP dispatch says multiple leaves | Nodes were not connected, or more than one terminal node exists | Inspect `dag.root_nodes`, `dag.leaf_nodes`, and `dag.trigger_nodes`; connect to one final operator or explicitly join outputs. HTTP trigger dispatch requires exactly one leaf. |
| Local leaf returns an unexpected type | Call data was wrapped and mapped according to operator input semantics | Inspect the mapper's input and call `await leaf.call(tiny_value)`; for HTTP, validate the pydantic body separately and then pass that body. |
| `check_serializable` rejects a callable | Closure, local object, client, or other value cannot cross a process boundary | Use a registered operator class and module-level callable with simple typed state. Keep closure examples local-only. |
| `after_dag_end` cleanup error | Hook is not idempotent or was called with the wrong event-loop task identity | Make cleanup tolerant of repeat calls and let the runner supply the event-loop identity. Avoid manually clearing internal context maps. |

`DAG.show(mermaid=True)` and `print_tree()` are safer graph diagnostics than starting
an application. `visualize_dag()` may require Graphviz and can write a file/open a
viewer; do not use it as a non-interactive verification gate.

## HTTP trigger and pydantic body errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `{dag_id}` endpoint cannot resolve | Trigger is not attached to a DAG | Create it inside the DAG context or pass `dag=dag`; inspect `_resolved_endpoint()` before mount. |
| `HttpTrigger does not support trigger directly` | Code attempted `await trigger.trigger(...)` | Call the single leaf locally or dispatch through the mounted HTTP route. |
| HTTP dispatch says only one leaf is supported | DAG has zero/multiple terminal nodes | Join outputs into one leaf or expose separate trigger DAGs. |
| GET/DELETE rejects a dict/string body | Query routes only support model fields or supported scalar forms | Use a pydantic model for query fields, or switch to POST for a JSON/dict body. |
| POST body arrives as a dict instead of model | `request_body` was not set to the pydantic class | Pass `request_body=MyBody`; use `http_trigger_body` only for a `BaseHttpBody` adapter. |
| HTTP 422 for missing field/type | Pydantic request validation is working | Check the model's required fields and types; fix the caller rather than bypassing validation. |
| Response model is not applied | `response_model`/`http_response_body` was omitted | Set the intended response type; remember that serialization is handled by FastAPI. |
| `add_api_route() got an unexpected keyword argument 'priority'` | A plain FastAPI app was passed to `mount_to_app`, which expects DB-GPT's priority router | Use `mount_to_router(APIRouter(), ...)` for portable tests, or mount through the supported DB-GPT app. |
| Stream never closes / cleanup does not run | Consumer did not exhaust the async stream or an exception interrupted it | Consume the response, use the returned background cleanup path, and make lifecycle hooks idempotent. Test non-streaming first. |
| A route appears registered but request fails | Registration is not server startup, and service prefix/dependencies may differ | Inspect route metadata and OpenAPI locally, then verify the running DB-GPT app/base URL in the APIs route. |

The standard DB-GPT application commonly adds `/api/v1/awel/trigger` before the
trigger endpoint. Keep that prefix out of reusable endpoint definitions unless the host
contract explicitly requires it.

## Skills and optional integrations

| Symptom | Likely cause | Recovery |
|---|---|---|
| File skill is skipped: no frontmatter | File does not begin with `---` and close a valid frontmatter block | Add YAML frontmatter with non-empty `name` and `description`, then keep instructions after it. |
| File skill loads but prompt is empty | JSON/YAML was loaded through the core loader, which currently emphasizes metadata/config | Use a complete `SKILL.md`, `SkillBuilder`, or verify the installed loader behavior before publication. |
| `load_skill_from_module` returns `None` | Module has no zero-argument `Skill` subclass | Export a constructible class named `Skill` and keep imports local/no-credential. |
| Duplicate skill registration fails | Same class/name key already exists | Choose a unique name, or use `ignore_duplicate=True` only when intentionally retaining the first registration. |
| Middleware lists no skills | Source directory is missing, not a directory, or skills are not immediate child `SKILL.md` files | Check each source and layout; use recursive `SkillLoader`/Claude registry if nested loading is intended. |
| Wrong skill wins | Later middleware source overrides an earlier same-name skill | Order sources deliberately and log the selected metadata/path. |
| Auto-match activates the wrong skill | Matching is description/name keyword substring matching | Disable auto-match for sensitive tasks and select by exact name after validating dependencies. |
| Skill script executes unexpectedly | Script helpers invoke code execution rather than metadata loading | Do not execute scripts during discovery; require trusted policy, inspect code, bound arguments, and a safe workspace. |
| MCP tools are absent or connection hangs | MCP server/network/TLS/header/transport is unavailable | Mark the workflow optional, verify server reachability and TLS/headers, and do not replace a missing remote tool with a fake local result. |
| MCP tool name is not found | ConnectorManager applied a namespace prefix | Inspect active pack names and use `mcp__<prefix>__<original_name>` exactly. |

## Verification boundary

For a CPU/no-network environment, the reliable required gate is:

1. import `DAG`, `HttpTrigger`, `MapOperator`, pydantic body classes, skill manager/
   builder/loader, tool classes, and context tracker;
2. inspect signatures and construct a two-node DAG with a pydantic body;
3. check roots/leaves/triggers, resolved endpoint, router metadata, and local leaf
   result;
4. check a tiny tool's schema and sync/async execution;
5. parse/register a tiny skill fixture without executing its scripts;
6. run focused native DAG/agent-context/skill-management tests when the integrated
   verifier selects them.

Provider calls, controller health, CUDA inference, external databases, graph/vector
services, MCP servers, sandbox services, and file-consuming end-to-end agents remain
optional until their prerequisites are explicitly provisioned and verified.
