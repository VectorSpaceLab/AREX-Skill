# Custom Columns and MCP

Use this reference when plugin/extension work overlaps with in-process custom columns or MCP tool aliases. For general config authoring, route to `../../config-authoring/SKILL.md`; for full runtime generation and artifact behavior, route to `../../generation-runtime/SKILL.md`.

## In-process custom column surface

`@custom_column_generator(...)` marks a Python function as valid for `CustomColumnConfig(column_type="custom")`. It is not an entry-point plugin and does not create a new `DataDesignerColumnType` discriminator value.

Decorator metadata:

- `required_columns`: columns that must exist before the custom generator runs; used for DAG ordering and input validation.
- `side_effect_columns`: additional output columns that must be created and should be preserved.
- `model_aliases`: model aliases made available through the `models` dict and included in startup readiness checks.

Signature rules are strict. A generator function must have one to three positional parameters with these names by position:

1. `row` or `df`
2. `generator_params`
3. `models`

Runtime strategy decides the first parameter:

- `GenerationStrategy.CELL_BY_CELL` expects `row` and a per-row `dict`; the generator must return a `dict`.
- `GenerationStrategy.FULL_COLUMN` expects `df` and a DataFrame; the generator must return a DataFrame.

A three-argument generator receives a `models` mapping keyed by the decorator-declared aliases. In sync custom generation, model facades are bridged so user code can call `models[alias].generate(...)`; async row generators are also supported.

Minimal extension-focused pattern:

```python
from __future__ import annotations

from pydantic import BaseModel

import data_designer.config as dd

class EnrichParams(BaseModel):
    prefix: str = "Summarize"

@dd.custom_column_generator(
    required_columns=["source_text"],
    side_effect_columns=["summary_prompt"],
    model_aliases=["text-model"],
)
def summarize(row: dict, generator_params: EnrichParams, models: dict) -> dict:
    prompt = f"{generator_params.prefix}: {row['source_text']}"
    text, _ = models["text-model"].generate(prompt=prompt)
    row["summary"] = text
    row["summary_prompt"] = prompt
    return row

builder = dd.DataDesignerConfigBuilder(model_configs=[...])
builder.add_column(
    dd.CustomColumnConfig(
        name="summary",
        generator_function=summarize,
        generator_params=EnrichParams(),
    )
)
```

Output validation rules matter for side-effect preservation:

- The returned row/DataFrame must include the primary column named by `CustomColumnConfig.name`.
- Every declared `side_effect_columns` entry must be present in the result.
- Pre-existing columns may not be removed.
- Undeclared new columns are removed with a warning. Declare side-effect columns to keep them.
- Missing `required_columns`, wrong return type, missing primary output, missing side-effect outputs, or strategy/signature mismatch raise `CustomColumnGenerationError`.

Readiness uses `config.get_model_aliases()` for every column config, so custom column `model_aliases` are probed just like built-in model-generated column aliases. This is the key source-backed behavior for synthetic cases that combine plugin-provided column types with custom columns that need model aliases.

## Combining plugin-provided types with custom columns

Plugin-provided column types and `CustomColumnConfig` coexist in `ColumnConfigT` after import-time plugin injection. A good agent plan should:

1. Ensure the installable plugin package is visible to the same interpreter before importing `data_designer.config.column_types`.
2. Keep custom columns on the built-in `column_type="custom"`; do not package a plugin whose discriminator collides with `custom` or another built-in/plugin value.
3. Preserve custom side-effect columns with the decorator, because builder prompt/expression reference validation includes declared side effects.
4. Preserve custom model aliases with the decorator, because readiness gathers model aliases through `get_model_aliases()` rather than only reading a `model_alias` field.

## MCP config surface

MCP tool use is configured through provider configs and tool configs:

- `MCPProvider`: remote SSE or Streamable HTTP MCP server (`provider_type` defaults to `sse`, or set `streamable_http`). Fields: `name`, `endpoint`, optional `api_key` secret reference.
- `LocalStdioMCPProvider`: local subprocess MCP server (`provider_type="stdio"`). Fields: `name`, `command`, optional `args`, optional `env`.
- `ToolConfig`: alias used by model-generated columns. Fields: `tool_alias`, `providers`, optional `allow_tools`, `max_tool_call_turns` default `5`, optional `timeout_sec`.

Config builder entry points:

```python
import data_designer.config as dd
from data_designer.interface import DataDesigner

mcp_provider = dd.LocalStdioMCPProvider(
    name="docs-mcp",
    command="python",
    args=["-m", "my_docs_mcp_server"],
)

tool_config = dd.ToolConfig(
    tool_alias="docs-tools",
    providers=["docs-mcp"],
    allow_tools=["search_docs", "fetch_doc"],
    max_tool_call_turns=5,
    timeout_sec=30.0,
)

builder = dd.DataDesignerConfigBuilder(model_configs=[...], tool_configs=[tool_config])
builder.add_column(
    dd.LLMTextColumnConfig(
        name="answer",
        prompt="Use tools to answer: {{ question }}",
        model_alias="text-model",
        tool_alias="docs-tools",
    )
)

designer = DataDesigner(mcp_providers=[mcp_provider])
print(designer.list_mcp_tool_names("docs-mcp"))
designer.check_models(builder)
```

Name boundaries are a common source of errors:

- Provider `name` is used in `ToolConfig.providers` and `DataDesigner.list_mcp_tool_names(provider_name)`.
- `ToolConfig.tool_alias` is used in model-generated column configs as `tool_alias`.
- Tool function names come from the MCP server and may be restricted by `allow_tools`.

## MCP readiness and runtime behavior

Readiness is shared by `DataDesigner.check_models`, `preview`, and `create` startup:

1. Every column config contributes model aliases via `get_model_aliases()`.
2. Model aliases are probed first through `ModelRegistry.arun_health_check(...)`; `DATA_DESIGNER_SKIP_MODEL_HEALTH_CHECKS=1` skips only model probes.
3. For model-generated columns with a non-empty `tool_alias`, readiness collects unique sorted tool aliases.
4. If any tool alias is referenced but no `MCPRegistry` exists on the resource provider, readiness raises `DatasetGenerationError`.
5. `MCPRegistry.run_health_check(...)` validates each tool alias, provider reference, facade construction, tool schema discovery, and duplicate tool names.

`MCPFacade` then handles tool execution during model loops:

- `get_tool_schemas()` lists tools from every provider, rejects duplicate tool names across providers, then applies `allow_tools` filtering.
- Missing allowed tools raise `MCPConfigurationError`.
- Tool calls not permitted by `allow_tools` raise `MCPToolError`.
- Invalid tool argument JSON raises `MCPToolError`.
- Parallel tool calls in one completion are executed through MCP I/O and returned as tool messages.
- Tool-call turn limits are enforced by refusal messages instead of unbounded loops.
- Text and image/multimodal MCP results are preserved in provider-ready message content where possible.

## Evidence consulted

- `packages/data-designer-config/src/data_designer/config/custom_column.py`
- `packages/data-designer-config/src/data_designer/config/column_configs.py`
- `packages/data-designer-config/src/data_designer/config/config_builder.py`
- `packages/data-designer-config/src/data_designer/config/mcp.py`
- `packages/data-designer-engine/src/data_designer/engine/column_generators/generators/custom.py`
- `packages/data-designer-engine/src/data_designer/engine/readiness.py`
- `packages/data-designer-engine/src/data_designer/engine/mcp/registry.py`
- `packages/data-designer-engine/src/data_designer/engine/mcp/facade.py`
- `packages/data-designer-engine/tests/engine/test_readiness.py`
- `packages/data-designer-engine/tests/engine/mcp/test_mcp_registry.py`
- `packages/data-designer-engine/tests/engine/mcp/test_mcp_facade.py`
- `packages/data-designer-engine/tests/engine/column_generators/generators/test_custom.py`
- `architecture/mcp.md`
