# Conversational API Reference

## Purpose

Use this reference for verified PandasAI chat, agent, configuration, and response
surface details. Recipes are in `workflows.md`; failure recovery is in
`troubleshooting.md`.

## Global configuration

PandasAI v3 uses a global config manager exposed as `pai.config`.

```python
import pandasai as pai

pai.config.set({
    "llm": llm,
    "save_logs": True,
    "verbose": False,
    "max_retries": 3,
})

config = pai.config.get()
pai.config.update({"verbose": True})
```

Verified config fields:

| Field | Type/meaning | Default |
| --- | --- | --- |
| `llm` | LLM object implementing PandasAI's LLM interface | `None` |
| `save_logs` | Save logs to a `pandasai.log` file near the project root | `True` |
| `verbose` | Print log messages to stdout | `False` |
| `max_retries` | Retry budget for generated-code repair | `3` |
| `file_manager` | Local dataset file manager used by semantic layer | default local file manager |

## Main chat APIs

```python
import pandasai as pai
from pandasai import Agent, DataFrame
```

| API | Verified signature | Notes |
| --- | --- | --- |
| `pai.chat` | `chat(query: str, *dataframes: DataFrame, sandbox: Optional[Sandbox] = None)` | Starts a global chat over one or more DataFrames and stores the current agent for `pai.follow_up`. Raises if no dataframes are provided. |
| `pai.follow_up` | `follow_up(query: str)` | Continues the previous global `pai.chat` conversation. Raises if no global chat exists. |
| `DataFrame.chat` | `chat(self, prompt: str, sandbox: Optional[Sandbox] = None) -> BaseResponse` | Creates an internal `Agent([self], sandbox=sandbox)` on first use and reuses it for later calls. |
| `DataFrame.follow_up` | `follow_up(self, query: str, output_type: Optional[str] = None)` | Requires that `DataFrame.chat` was called first; otherwise raises `ValueError`. |
| `Agent` | `Agent(dfs, config=None, memory_size=10, vectorstore=None, description=None, sandbox=None)` | Wraps one or more `DataFrame`/`VirtualDataFrame` objects, memory, generated code, response parsing, optional vectorstore, and optional sandbox. |
| `Agent.chat` | `chat(self, query: str, output_type: Optional[str] = None)` | Clears conversation memory, sets optional output type hint, and processes one query. |
| `Agent.follow_up` | `follow_up(self, query: str, output_type: Optional[str] = None)` | Continues memory without clearing it. |

### Dataframe conversion

`Agent` converts raw pandas DataFrames into PandasAI `DataFrame` objects. When a
list of dataframes is supplied, their data sources must be compatible if they
represent virtual/semantic data sources.

## LLM interface

PandasAI expects an LLM object with a `call(...)` implementation. Most users get
this object from an extension package, such as `pandasai-litellm` or
`pandasai-openai`.

The bundled `FakeLLM` is useful for deterministic tests:

```python
from pandasai.llm.fake import FakeLLM

fake = FakeLLM("df = execute_sql_query('SELECT COUNT(*) AS total FROM table_a')\n"
               "result = {'type': 'number', 'value': int(df['total'].iloc[0])}")
pai.config.set({"llm": fake})
```

The generated code must pass validation. In v3.0.0, the code validator requires
an `execute_sql_query(...)` call before it will execute generated code.

## Agent-generated code path

Key facts for debugging:

1. `Agent.generate_code` adds the user query to memory and asks the configured
   LLM for code.
2. The code generator validates required calls and cleans code before execution.
3. `Agent.execute_code` provides a Python environment with `pd`, `np`, `plt`,
   `execute_sql_query`, and registered custom skills.
4. `Agent._execute_sql_query` registers local DataFrames with DuckDB, rewrites
   table/column names for virtual dataframes, and returns a pandas DataFrame.
5. `Agent.execute_with_retries` retries code execution up to `max_retries` by
   asking the LLM to repair failures.
6. `ResponseParser.parse` turns `result` dictionaries into response objects.

## Response properties

Every successful response object exposes:

- `value`: the result payload.
- `type`: response type such as `number`, `string`, `dataframe`, `chart`, or
  `error`.
- `last_code_executed`: cleaned generated code used for the result.
- `to_dict()` and `to_json()` for base response serialization.

Chart responses additionally support `save(path)`, `show()`, and
`get_base64_image()`.

## Legacy compatibility wrappers

`SmartDataframe` and `SmartDatalake` still exist for compatibility but emit
`DeprecationWarning`. Prefer these replacements:

| Legacy | Preferred v3 pattern |
| --- | --- |
| `SmartDataframe(df, config=...)` | `pai.config.set(...); df = pai.DataFrame(df); df.chat(...)` |
| `SmartDatalake([df1, df2], config=...)` | `pai.config.set(...); pai.chat(query, df1, df2)` or `Agent([df1, df2])` |
| Per-wrapper config dict | Global `pai.config.set(...)` |

When maintaining old code, keep warnings visible and avoid building new examples
around deprecated wrappers unless the task is explicitly a migration.
