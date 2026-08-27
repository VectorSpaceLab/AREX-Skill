# Custom Tools and Publishing

CrewAI supports custom tools through `BaseTool`, the `@tool` decorator, and `CrewStructuredTool`. Use this reference when creating project-local tools or packaging a reusable tool library.

## Choose an Interface

| Use case | Recommended interface | Notes |
| --- | --- | --- |
| Reusable class with validation, env vars, max usage, or typed output | `BaseTool` | Best default for production and publishing. |
| Small function with a clear docstring and type annotations | `@tool` | Good for simple local tools. Requires a docstring. |
| Wrapping an existing callable or converting toward LangChain-style structured tools | `CrewStructuredTool.from_function` | Requires a callable and docstring or explicit description. |
| Published package on PyPI | `BaseTool` with explicit schemas | Export from package `__init__.py`; declare `crewai` dependency. |

## BaseTool Pattern

```python
from crewai.tools import BaseTool, EnvVar
from pydantic import BaseModel, Field

class LookupInput(BaseModel):
    sku: str = Field(..., description="Product SKU to inspect.")

class LookupResult(BaseModel):
    sku: str
    quantity: int
    needs_reorder: bool

class InventoryLookupTool(BaseTool):
    name: str = "inventory_lookup"
    description: str = "Checks local inventory for one SKU and reports reorder status."
    args_schema: type[BaseModel] = LookupInput
    result_schema: type[BaseModel] = LookupResult
    env_vars: list[EnvVar] = []
    max_usage_count: int | None = 5

    def _run(self, sku: str) -> LookupResult:
        quantity = {"SKU-123": 14, "SKU-456": 0}.get(sku, 0)
        return LookupResult(
            sku=sku,
            quantity=quantity,
            needs_reorder=quantity < 5,
        )
```

Important behavior:

- `BaseTool.run(...)` validates keyword arguments through `args_schema` before `_run` executes.
- If `args_schema` is omitted, CrewAI infers fields from `_run` and then `_arun` signatures.
- If `_run` returns a Pydantic model, CrewAI can infer `result_schema` and serialize agent-facing output as JSON.
- Direct Python calls receive the raw return value. Agent-facing formatting goes through `format_output_for_agent`.
- `max_usage_count` must be a positive integer when set; after exhaustion, tool execution returns a usage-limit message.

## Agent-Facing Output Formatting

Use `result_schema` for machine-readable outputs. Override `format_output_for_agent` when the model should see a short summary instead of JSON.

```python
class InventoryLookupTool(BaseTool):
    name: str = "inventory_lookup"
    description: str = "Checks local inventory for one SKU."
    result_schema: type[BaseModel] = LookupResult

    def _run(self, sku: str) -> LookupResult:
        return LookupResult(sku=sku, quantity=0, needs_reorder=True)

    def format_output_for_agent(self, raw_result: object) -> str:
        result = LookupResult.model_validate(raw_result)
        return f"{result.sku}: {result.quantity} units; reorder={result.needs_reorder}"
```

## Decorator Pattern

```python
from crewai.tools import tool

@tool("multiply_numbers")
def multiply_numbers(first_number: int, second_number: int) -> str:
    """Multiply two integers and return the product."""
    return str(first_number * second_number)
```

Requirements:

- Provide a docstring; it becomes part of the tool description.
- Type every parameter and return value.
- Keep side effects explicit in the description so agents know when not to use the tool.

## Async Tools

Use `_arun` for I/O-bound tools. CrewAI supports async tools in normal crews and flows.

```python
class AsyncStatusTool(BaseTool):
    name: str = "async_status"
    description: str = "Returns a status string from an async-safe source."

    async def _arun(self, query: str = "") -> str:
        return f"status for {query}"

    def _run(self, query: str = "") -> str:
        return f"status for {query}"
```

Include a synchronous `_run` when direct synchronous use is expected. Avoid hidden network calls unless the user approves credentials and side effects.

## Cache Control

Tools cache by default because `BaseTool.cache_function` defaults to a function that returns `True`.

```python
def cache_only_even(args, result):
    return int(result) % 2 == 0

multiply_numbers.cache_function = cache_only_even
```

Use custom cache functions when results depend on freshness, credentials, user identity, or mutable external state.

## Environment Variables and Credentials

Declare required variables with `EnvVar` so users and generated tool specs can discover them.

```python
from crewai.tools import EnvVar

env_vars: list[EnvVar] = [
    EnvVar(
        name="GEOCODING_API_KEY",
        description="API key for the approved geocoding provider.",
        required=True,
    ),
]
```

Credential rules:

- Do not hardcode real keys in source, descriptions, examples, or logs.
- Prefer constructor arguments or environment variables over global mutable state.
- Fail early with clear messages when required credentials are missing.
- Offer a local no-network fallback when possible.

## Safe File and URL Handling

CrewAI tools include safety utilities that validate file paths and URLs. For custom tools that read paths or fetch URLs, follow the same model:

- Resolve local paths against an allowed base directory.
- Reject path traversal and symlink escapes for writes.
- Reject `file://` URLs and unsafe schemes for fetches.
- Treat local/private network URLs as sensitive and require explicit approval.
- Keep display paths relative or redacted so errors do not leak machine-specific directories.

## Publishable Tool Package

Recommended package shape:

```text
crewai-geolocate/
├── pyproject.toml
├── README.md
└── src/
    └── crewai_geolocate/
        ├── __init__.py
        └── tools.py
```

`pyproject.toml` should declare `crewai` as a dependency and use a normal Python build backend.

```toml
[project]
name = "crewai-geolocate"
version = "0.1.0"
description = "CrewAI-compatible geolocation tools."
requires-python = ">=3.10"
dependencies = ["crewai"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Package conventions:

- Package name: prefix with `crewai-` when publishing to make discovery easier.
- Module name: use underscores, for example `crewai_geolocate`.
- Tool class name: use PascalCase ending in `Tool`.
- `__init__.py`: re-export public tools and define `__all__`.

```python
from crewai_geolocate.tools import GeolocateTool

__all__ = ["GeolocateTool"]
```

Before publishing, test the tool both directly and inside a minimal `Agent`/`Task`/`Crew`. Publishing commands such as `uv build` and `uv publish` require user approval because they create artifacts and may upload to PyPI.

## CrewStructuredTool

Use `CrewStructuredTool.from_function` when wrapping a normal function and keeping schema inference.

```python
from crewai.tools.structured_tool import CrewStructuredTool


def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

tool = CrewStructuredTool.from_function(add_numbers)
```

Behavior to remember:

- Missing docstring without an explicit description raises `ValueError`.
- `args_schema` is inferred from the function signature when `infer_schema=True`.
- `result_schema` is inferred from a Pydantic return annotation, not from arbitrary dict returns.
- Runtime arguments are parsed from dicts or JSON strings and validated against the schema.

## Common Mistakes

- Forgetting a docstring on a `@tool` or `CrewStructuredTool.from_function` callable.
- Missing type annotations, causing weak schemas and poor agent behavior.
- Returning dictionaries without `result_schema` when agents need stable JSON fields.
- Letting tool descriptions hide side effects such as writes, network calls, or paid API calls.
- Importing a custom tool from a module path that is not installed or not on `PYTHONPATH`.
- Publishing a package without re-exporting the tool from `__init__.py`.

## Source Evidence Notes

The tool repository template was not copied into this runtime skill. Its reusable guidance is distilled here as package layout, import/export conventions, and publish/test commands. This keeps the runtime skill self-contained and avoids depending on source templates.
