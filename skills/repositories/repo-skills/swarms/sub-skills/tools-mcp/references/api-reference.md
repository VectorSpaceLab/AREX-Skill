# Tools and MCP API reference

## Tool schema helpers

### `BaseTool`

Commonly used methods:

- `func_to_dict(function=...)`
- `base_model_to_dict(...)`
- `detect_tool_input_type(...)`
- `execute_tool_by_name(...)`
- `check_str_for_functions_valid(...)`
- `convert_funcs_into_tools(...)`
- `load_params_from_func_for_pybasemodel(...)`

The tests and source show that `BaseTool` is the main local tool coordinator: it converts callables, validates tool-like payloads, and executes named functions from JSON payloads.

### Schema conversion helpers

- `get_openai_function_schema_from_func(...)`
- `convert_multiple_functions_to_openai_function_schema(...)`
- `load_basemodels_if_needed(...)`
- `get_parameters(...)`
- `get_required_params(...)`
- `base_model_to_openai_function(...)`
- `multi_base_model_to_openai_function(...)`

Use these when you need an OpenAI-compatible schema rather than a raw Python callable.

## MCP config objects

### `MCPConnection`

Relevant fields:

- `url`
- `name`
- `authorization_token`
- `api_key`
- `api_key_header`
- `api_key_prefix`
- `auth_type`
- `oauth`
- `transport`
- `headers`
- `timeout`
- `sse_read_timeout`
- `tool_timeout`
- `command`, `args`, `env` for `stdio`

### `MCPOAuthConfig`

Relevant fields:

- `grant_type`
- `client_id`
- `client_secret`
- `scopes`
- `redirect_uri`
- `client_name`
- `client_uri`
- `authorization_url`
- `token_url`
- `access_token`
- `refresh_token`
- `token_storage_path`
- `use_token_cache`
- `open_browser`
- `callback_timeout`

## `MCPManager`

Verified constructor signature summary:

```python
MCPManager(
    mcp_url=None,
    mcp_urls=None,
    mcp_config=None,
    mcp_configs=None,
    api_key=None,
    authorization_token=None,
    oauth=None,
    headers=None,
    transport=None,
    timeout=None,
    agent_name="agent",
    verbose=False,
    retry_attempts=3,
)
```

Main methods:

- `get_tools()` and `aget_tools()` return OpenAI-formatted tool schemas by default.
- `list_tool_names()` returns the names of the loaded tools.
- `execute_tool_calls(response, output_type="dict")` and `aexecute_tool_calls(...)` route each tool call back to the server that owns it.

## How routing works

- A single connection can be given as a URL, dict, or `MCPConnection`.
- Several connections can be merged via `mcp_urls` or `mcp_configs`.
- Duplicate tool names are deduplicated at load time.
- The manager resolves auth and transport per connection, not only globally.

## Agent integration

An `Agent` can be connected to MCP by passing `mcp_url`, `mcp_urls`, `mcp_config`, or `mcp_configs` in its constructor.

Use `tools-mcp` when the task is about the tool path itself; use `single-agent` only when MCP is just one of several agent knobs.
