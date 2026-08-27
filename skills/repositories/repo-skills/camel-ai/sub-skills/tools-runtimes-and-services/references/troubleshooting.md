# Troubleshooting Tools, Runtimes, and Services

## FunctionTool Schema Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Schema lacks useful parameter descriptions | Missing `Args:` docstring entries or unsupported docstring style | Add a docstring with one entry per parameter, or patch descriptions with `set_parameter_description()`. |
| `FunctionTool.validate_openai_tool_schema` raises `SchemaError` | Generated or manual schema is not valid JSON Schema | Inspect `get_openai_tool_schema()`, ensure `parameters.type == "object"`, `properties` is a dict, and required names exist in properties. |
| Nested Pydantic argument is accepted at runtime but schema is confusing | Model fields lack `Field(description=...)` or type hints are too broad | Add Pydantic field descriptions and concrete types; rerun `scripts/inspect_tool_schema.py`. |
| Tool call execution raises argument coercion error | Model supplied dict shape does not match the function's Pydantic type | Compare model/tool args with the schema, then call the `FunctionTool` locally with the same kwargs. |
| Async tool warns or blocks unexpectedly | Calling an async function through sync `tool(...)` path | Prefer `await tool.async_call(...)` or `await agent.astep(...)` in async applications. |
| Schema synthesis tries to create a default model | `synthesize_schema=True` without `synthesize_schema_model` | Prefer manual schema fixes for deterministic tools; only synthesize with an explicit model backend. |

## `external_tools` Shape Problems

Use `tools=[FunctionTool(...)]` for Python callables. Use `external_tools` only for provider-native tool declarations.

Checklist for OpenAI-style `external_tools`:

- Top-level object has `type: "function"`.
- `function.name` is stable, unique, and provider-compatible.
- `function.description` is present.
- `function.parameters` is valid JSON Schema with `type: "object"` and `properties`.
- The application has a separate path for executing provider-returned tool calls if CAMEL is not executing them locally.

The AgentOpenAPI service accepts `external_tools` in its request model, but source comments mark it as not fully supported in the service route. Prefer server-side `tool_registry` plus `tools_names` for service deployments.

## Optional Dependency Import Failures

Many toolkit modules import optional packages only when used. If construction or import fails:

1. Identify the toolkit family, not the whole repo.
2. Install the narrow extra or package, usually starting with `pip install 'camel-ai[tools]'`.
3. For browser tools, install browser binaries and OS dependencies required by the browser backend.
4. For Docker tools or runtimes, install the `docker` Python package and verify daemon access.
5. For OpenAPI parsing, ensure `prance` and `openapi-spec-validator` are installed.
6. For MCP, ensure the `mcp` package and configured server command are available.

Do not encode private environment paths or local interpreter locations into reusable skill content.

## API Credential Failures

Third-party toolkits often need API keys, OAuth tokens, workspace IDs, or base URLs. Keep credentials outside code and pass them through environment variables or runtime config. Before exposing a mutating toolkit to an agent:

- Scope tokens to read-only when possible.
- Start with a harmless listing/search method.
- Set `max_iteration` and tool timeouts.
- Confirm any write, send, delete, post, deploy, payment, or file mutation operation.

## MCP Startup and Robustness

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: At least one of clients, config_path, or config_dict must be provided` | Empty `MCPToolkit()` construction | Provide `config_path`, `config_dict`, or explicit `MCPClient` objects. |
| No valid clients created | Bad config shape | Use `{"mcpServers": {"name": {"command": ..., "args": [...]}}}` or URL server entries. |
| One server failure aborts startup | `skip_failed=False` or all servers failed | Use `skip_failed=True` for optional servers; keep mandatory servers separate. |
| Startup hangs | Server command blocks, wrong transport, or slow remote endpoint | Set `per_client_timeout`, reduce `max_retries`, and test the server command outside CAMEL. |
| Protected remote server returns auth errors | Missing `headers` config | Add `Authorization` or API-key headers in config from environment-managed values. |

Use `async with MCPToolkit(...) as toolkit:` to guarantee disconnect and cleanup.

## Docker, Browser, Runtime, and Interpreter Availability

- `DockerRuntime` and Docker-backed terminal/code execution require Docker daemon access, a pullable image, available ports, and cleanup permissions.
- Browser toolkits require browser binaries, display/headless configuration, and sometimes user-data directories or cookies.
- `RemoteHttpRuntime` requires a reachable host/port and a compatible runtime API process.
- `InternalPythonInterpreter` is safer than raw subprocess execution but still needs a narrow `action_space` and `import_white_list` for untrusted code.
- E2B, Daytona, and MicroSandbox examples require external services and credentials; treat them as deployment integrations rather than default local checks.

## Sandbox and Unsafe Code Risks

Never run untrusted model-generated code with `unsafe_mode=True` in the local process. For code execution tasks:

1. Prefer constrained tools over general code execution.
2. Use `internal_python` with an import whitelist for simple calculations.
3. Use Docker, MicroSandbox, E2B, or a remote runtime for broader code.
4. Keep `require_confirm=True` for subprocess/shell operations unless the command set is bounded.
5. Restrict working directories and environment variables.
6. Clean up containers, subprocesses, and runtime servers after use.

## OpenAPI Spec, Auth, and Security Config

- Specs must be OpenAPI `3.0.x` or `3.1.x`.
- Each non-deprecated operation needs a `summary` or `description`.
- Operation names can become long or collide; review generated tool names before handing to an agent.
- Request bodies should describe JSON payload shape clearly.
- API key security schemes usually map to environment variables through CAMEL's OpenAPI security config; missing keys surface as runtime request errors.
- Treat third-party specs as untrusted input: review base URLs, auth schemes, and mutating endpoints before agent exposure.

## Quick Local Diagnostic

Run the bundled inspector against a simple function before involving a model:

```bash
python sub-skills/tools-runtimes-and-services/scripts/inspect_tool_schema.py
```

The script validates schema generation locally and exits non-zero on import or schema failures.
