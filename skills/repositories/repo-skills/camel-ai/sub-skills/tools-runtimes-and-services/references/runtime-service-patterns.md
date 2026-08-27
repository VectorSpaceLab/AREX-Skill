# Runtime, Interpreter, MCP, OpenAPI, and Service Patterns

This reference covers CAMEL surfaces that execute code, connect to external tool servers, convert OpenAPI specs into tools, or expose agents through services. These surfaces can have side effects; configure isolation, credentials, and lifecycle explicitly.

## MCPToolkit Client Pattern

`MCPToolkit(clients=None, config_path=None, config_dict=None, timeout=None, skip_failed=True, per_client_timeout=None, max_retries=2, retry_delay=3.0)` manages one or more MCP clients and aggregates their tools.

```python
from camel.agents import ChatAgent
from camel.toolkits import MCPToolkit

config = {
    "mcpServers": {
        "filesystem": {
            "command": "python",
            "args": ["mcp_server.py"],
        },
        "protected_remote": {
            "url": "https://example.invalid/mcp",
            "timeout": 30,
            "headers": {"Authorization": "Bearer ${TOKEN}"},
        },
    }
}

async with MCPToolkit(
    config_dict=config,
    skip_failed=True,
    per_client_timeout=10,
    max_retries=2,
) as toolkit:
    agent = ChatAgent(tools=toolkit.get_tools())
```

Use `skip_failed=True` when one flaky server should not prevent agent startup. Set `skip_failed=False` when all servers are mandatory. Always disconnect explicitly or use `async with`.

## Exposing Toolkits as MCP Servers

Any `BaseToolkit` can run its `FastMCP` server with:

```python
toolkit.run_mcp_server(mode="stdio")
```

Supported modes in source are `stdio`, `sse`, and `streamable-http`. Use this for language-agnostic remote tool access. Document the server command, arguments, environment variables, and timeout separately from client code.

CAMEL also includes a service-oriented MCP server for agents. Treat that pattern as deployment guidance rather than a bundled script because service launch depends on model credentials, network ports, and process management.

## OpenAPIToolkit Pattern

`OpenAPIToolkit` parses OpenAPI 3.0/3.1 specs, converts operations to OpenAI tool schemas, and decorates request functions. Key behavior from source:

- `parse_openapi_file(openapi_spec_path)` returns `None` if `prance` is unavailable.
- OpenAPI specs must include an `openapi` version starting with `3.0` or `3.1`.
- Each operation needs a `description` or `summary`; deprecated operations are skipped.
- Generated function names use the API name plus `operationId` when available.
- Security schemes can inject API keys from environment variables through CAMEL's OpenAPI security config.

Use OpenAPI tools only with trusted specs. Review auth requirements and generated operation names before exposing them to an agent.

## CodeExecutionToolkit Pattern

`CodeExecutionToolkit(sandbox="subprocess", verbose=False, unsafe_mode=False, import_white_list=None, require_confirm=None, timeout=None, microsandbox_config=None)` returns `execute_code` and `execute_command` tools.

Supported sandbox values in source are:

- `internal_python`: controlled AST-style interpreter with optional import whitelist and action space.
- `jupyter`: Jupyter kernel execution.
- `docker`: Docker interpreter backend.
- `subprocess`: local subprocess backend; requires confirmation by default when `require_confirm` is `None`.
- `e2b`: E2B remote sandbox backend.
- `microsandbox`: MicroSandbox backend using `server_url`, `api_key`, `namespace`, `sandbox_name`, and `timeout` config.

Use `require_confirm=True` for shell/subprocess paths unless automation is bounded and trusted. Use `import_white_list` for `internal_python`. Avoid `unsafe_mode=True` for model-generated code outside an external sandbox.

## TerminalToolkit Pattern

`TerminalToolkit(timeout=20.0, working_directory=None, use_docker_backend=False, docker_container_name=None, session_logs_dir=None, safe_mode=True, allowed_commands=None, clone_current_env=False, install_dependencies=None, enable_other_runtimes=None)` provides terminal session tools.

Important behavior:

- Local backend treats `working_directory` as the security sandbox.
- Docker backend requires the `docker` Python package, Docker daemon access, and `docker_container_name`.
- `safe_mode=True` applies command safety rules; `allowed_commands` can narrow execution.
- `clone_current_env` and `install_dependencies` can mutate a workspace environment; avoid in public examples unless explicitly desired.
- `enable_other_runtimes` supports additional runtimes such as Go and Java in source examples.

## Runtimes

`camel.runtimes.BaseRuntime` defines `add()`, `reset()`, `cleanup()`, `stop()`, context-manager teardown, and `get_tools()`.

### DockerRuntime

`DockerRuntime(image, port=8000, remove=True, **kwargs)` wraps functions to execute in a Docker container.

Typical lifecycle:

```python
from camel.runtimes import DockerRuntime
from camel.toolkits import FunctionTool

with DockerRuntime("python:3.11-slim", port=8000) as runtime:
    runtime.add(FunctionTool(my_function), entrypoint="module:function")
    runtime.build()
    agent = ChatAgent(tools=runtime.get_tools())
```

Source behavior pulls a missing image, creates a container, copies CAMEL runtime API code into `/home`, starts an API process, and uses HTTP calls to invoke functions. It requires Docker access and cleanup.

### RemoteHttpRuntime

`RemoteHttpRuntime(host, port=8000, python_exec="python3")` starts or connects to a remote HTTP API wrapper for runtime functions. It exposes `ok`, `wait(timeout=10)`, `docs`, `build()`, `reset()`, and `stop()`.

Use it only when the API server lifecycle and network path are controlled. Do not hard-code local interpreter paths in reusable skill content.

## Interpreters

`InternalPythonInterpreter(action_space=None, import_white_list=None, unsafe_mode=False, raise_error=False, allow_builtins=True)` executes Python code with controlled builtins and optional import whitelist. It supports `python`, `py`, `python3`, and `python2` code type labels.

Use `InternalPythonInterpreter` for constrained Python expressions and known helper functions. Use Docker/Jupyter/subprocess/E2B/MicroSandbox interpreters only when their runtime dependencies are available and the risk is acceptable.

## AgentOpenAPI Server Pattern

`camel.services.agent_openapi_server.ChatAgentOpenAPIServer` builds a FastAPI app with routes under `/v1/agents`:

- `POST /init`: create an agent by `agent_id`, model fields, `tools_names`, `external_tools`, system message, memory window, token limit, output language, and `max_iteration`.
- `POST /step/{agent_id}` and `POST /astep/{agent_id}`: send messages.
- `GET /list_agent_ids`: list active agents.
- `POST /delete/{agent_id}`: delete an agent.
- `POST /reset/{agent_id}` and `GET /history/{agent_id}`: manage memory/history.

Register server-side tools through `tool_registry` and initialize agents with `tools_names` for safer service operation. Treat `external_tools` as provider-native schema input, not a way to upload executable Python.

## Bundled Script Decision

The bundled `scripts/inspect_tool_schema.py` is a safe local schema inspection utility adapted from CAMEL function-tool patterns. It does not call a model or run an agent loop. Docker, Daytona, MicroSandbox, browser, MCP server, and AgentOpenAPI examples remain prose-only guidance because they require external services, daemon/browser/network availability, or credentials.
