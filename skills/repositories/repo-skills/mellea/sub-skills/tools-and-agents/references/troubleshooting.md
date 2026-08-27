# Tools and agents troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModelOption.TOOLS` is rejected | A plain callable, malformed mapping, or wrong tool class was supplied | Wrap with `@tool`/`MelleaTool.from_callable`; ensure a list or `dict[str, AbstractMelleaTool]`. |
| The model mentions a tool but nothing runs | Generation APIs return calls; they do not execute them | Inspect `result.tool_calls`, then use an approved `call_tools()`/`acall_tools()` boundary or use `react()` knowingly. |
| No tool call is generated | Backend/model does not support tool calling, prompt does not require it, or the model chose not to call | Verify provider capability in the backend route, set `tool_calls=True`, use `uses_tool`, and keep the tool schema concise. Do not assume a supplied tool is mandatory. |
| `parse_tools()` returns no calls | Output is not JSON or uses a shape without `name` plus mapping `arguments`/`args`/`parameters` | Prefer native backend tool calls; otherwise require a bounded JSON contract and reject malformed output rather than guessing. |
| Strict argument validation raises `ValidationError` | Missing required field, wrong type, extra field, unresolved/unsupported schema, or malformed union | Show only field-level errors, repair/regenerate, and validate again. Do not fall back to lenient original arguments for side-effecting tools. |
| A schema looks valid but the provider rejects it | Nested `$ref`/`oneOf`/discriminator or provider-specific JSON Schema subset | Run the static checker, simplify the public schema, use explicit object/enum fields, and test with the target backend. MCP schemas pass through more directly than callable schemas. |
| LangChain adapter import fails | `langchain-core`/community package is absent | Install the narrow required extra/package, then import `BaseTool`; the adapter does not install it automatically. |
| LangChain tool errors on positional input | The adapter intentionally invokes `tool.run(tool_input={kwargs})` | Let Mellea's model call use keyword arguments; call the adapted tool with named fields. |
| smolagents adapter rejects an object | It is not an instance of smolagents `Tool`, or the optional package is absent | Install `mellea[tools]`/smolagents and pass the actual `Tool` instance. The wrapper calls `forward(**kwargs)`. |
| `mellea.stdlib.tools.mcp` raises `ImportError` | `mcp` or `httpx` is missing | Install `mellea[tools]`; do not catch this as a server outage until the import prerequisite is proved. |
| MCP discovery times out or returns no tools | Wrong transport/URL, unavailable server, TLS/auth issue, or server failed initialization | Check the exact transport config, bounded connect/read timeout, origin, credentials, and server health. Do not retry blindly with broader credentials. |
| MCP call returns `[tool error] ...` | The server reported `isError`, or a resource link could not be read | Treat it as failed output, inspect server-side logs safely, and decide whether retry is allowed. Never feed the error string into an approval shortcut. |
| MCP stdio server does not start | Executable/args not on PATH, bad environment, protocol noise, or missing server dependency | Run the pinned command manually in a controlled shell, pass minimal required `env`, and ensure stdout is reserved for MCP protocol. Each call starts a new subprocess. |
| Tool hook never fires | Plugin framework/`cpex` is not installed, plugin is not registered, or no handler matches | Install the hooks extra, register a scoped plugin before execution, and use `has_plugins`/a payload-level test. |
| `@hook` raises a type error | Handler is a normal `def` | Define the handler with `async def`; select an explicit `PluginMode` and priority when policy order matters. |
| A blocked call raises `PluginViolationError` | A hook returned `block(...)` | Treat denial as the intended result, surface a safe reason, and do not bypass the hook by invoking the wrapped callable directly. |
| ReAct exits with `RuntimeError` | No `final_answer` call before `loop_budget` | Increase the bounded budget only when justified, simplify tools/goal, inspect failed observations, or return a controlled incomplete result. |
| ReAct finalizer behaves strangely | A user tool was named `final_answer`, or finalizer was returned with another tool | Rename the business tool; the framework overrides that name and requires final answer to be the only tool in its turn. |
| ReAct loses its goal after compaction | The initiator was evicted | Use `pin_react_initiator` with `WindowCompactor`, `ThresholdCompactor`, or the summarizer's `pin_predicate`. |
| `ChatContext(compactor=...)` rejects a compactor | The object is not an `InlineCompactor` | Use `WindowCompactor`/`ThresholdCompactor`, implement the marker for a backend-free inline strategy, or run a general compactor via `react(compactor=...)`. |
| Summarizer calls a backend on every append or silently keeps growing | `LLMSummarizeCompactor` was attached directly or its backend call failed | Move it to the ReAct per-turn argument or threshold wrapper; inspect warnings and keep a verbatim fallback window. |
| Python result is skipped or times out | Static/import rejection, invalid working directory, policy timeout, failed package install, or Docker unavailable | Read `skipped`, `skip_message`, `timed_out`, `stderr`, and `execution_mode`; fix the specific prerequisite instead of rerunning unbounded code. |
| Declared local policy did not stop network/subprocess/env access | Local policy fields are declarative-only in this version | Use a real container/VM/network policy or replace the tool with a narrow wrapper. Never advertise the declaration as enforcement. |
| Docker artifacts are empty | `artifact_dir` was set without `artifact_export_paths`, code failed, or the path is a container path not written | Configure export paths in the policy, check success, and distinguish host destination from container path. |
| Shell command is skipped | Denylist found an operator, wrapper, dangerous command, system path, or malformed quote | Inspect `skip_message`; rewrite as one simple argv-friendly command in an approved workspace, or use a fixed Python wrapper. Do not evade the checker with encoding/indirection. |
| Shell command passed but is still unsafe | Denylists are incomplete and script files/network clients retain host power | Do not execute untrusted input locally; use static inspection plus real isolation and explicit network/credential controls. |

## A safe diagnosis order

1. Run `python scripts/audit_tool_request.py --help`, then audit a redacted
   serialized request; never paste credentials into the checker output.
2. Inspect tool name/schema/arguments without invoking the callable.
3. Check optional imports and backend/provider capability separately from policy.
4. Reproduce with a harmless fake callable or scripted backend.
5. Re-run the smallest native operation only after approval and with bounded
   time/output. Keep a failed `ExecutionResult` as evidence; do not convert a
   denial into a success by stringifying it.
