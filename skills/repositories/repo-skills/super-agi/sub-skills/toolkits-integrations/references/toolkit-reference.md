# SuperAGI Toolkit Reference

## When to Read

Read this when you need to understand how a SuperAGI tool becomes an executable
object, how toolkit config keys are loaded, or why tool execution fails.

## Key Runtime Contracts

### `BaseTool`

- `name: str`
- `description: str`
- `args_schema: Type[BaseModel] | None`
- `permission_required: bool`
- `toolkit_config: BaseToolkitConfiguration`
- `execute(tool_input, **kwargs)` parses input, calls `_execute`, and returns
  the observation.

### `BaseToolkit`

A toolkit must provide:

- `name: str`
- `description: str`
- `get_tools() -> List[BaseTool]`
- `get_env_keys() -> List[str]`

### `ToolConfiguration`

Represents a toolkit config key and whether it is required, secret, and/or a
special key type.

### `DBToolkitConfiguration`

`ToolBuilder` uses this subclass to read toolkit config values from the database
and decrypt them when needed.

### `ToolBuilder`

Loads a `Tool` record, imports the backing Python module dynamically from the
`superagi/tools`, `superagi/tools/external_tools`, or
`superagi/tools/marketplace_tools` tree, instantiates the tool class, and injects
DB-backed config.

### `ToolExecutor`

Normalizes tool names by lowercasing and removing spaces, then:

- returns a completion response for `finish` or an empty tool name,
- executes the matching tool and reports success or validation error,
- returns a retryable unknown-tool error otherwise.

## Useful Behaviors

- Tool names are normalized by lowercasing and removing spaces, so `Read File`
  and `readfile` are treated similarly during execution.
- Toolkit config values can be stored encrypted. Missing or malformed values can
  therefore cause either a secret-decryption failure or a fallback to file-based
  config loading.
- `create_function_schema` derives parameter schemas from function signatures,
  so the tool's callable signature and its public JSON schema need to stay in
  sync.

## Where to Look Next

- `builtin-tools.md` for the inventory of built-in toolkit families.
- `custom-and-marketplace-tools.md` for download/registration behavior.
- `troubleshooting.md` for missing dependencies, config, and import failures.
