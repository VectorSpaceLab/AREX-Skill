# API reference for SQL analysis

This reference covers the SQL portion of `ai-data-science-team` version `0.0.0.9017`. It is intended for runtime operation from an installed package; it does not require access to the source checkout.

## Imports

```python
from ai_data_science_team.agents import SQLDatabaseAgent, make_sql_database_agent
from ai_data_science_team.tools.sql import get_database_metadata, build_query
```

For safety diagnostics only, the package also exposes the implementation helper:

```python
from ai_data_science_team.agents.sql_database_agent import _validate_sql
```

`_validate_sql` is a private helper by naming convention. Use it for verification and troubleshooting, but prefer `SQLDatabaseAgent(..., safe_mode=True)` during normal agent operation.

## Public signatures

| Object | Signature | Use |
| --- | --- | --- |
| `SQLDatabaseAgent` | `(self, model, connection, n_samples=1, log=False, log_path=None, file_name='sql_database.py', function_name='sql_database_pipeline', overwrite=True, human_in_the_loop=False, bypass_recommended_steps=False, bypass_explain_code=False, checkpointer=None, smart_schema_pruning=False, safe_mode=True)` | Object-oriented wrapper around the SQL LangGraph workflow. Stores the latest response on the instance. |
| `make_sql_database_agent` | `(model, connection, n_samples=1, log=False, log_path=None, file_name='sql_database.py', function_name='sql_database_pipeline', overwrite=True, human_in_the_loop=False, bypass_recommended_steps=False, bypass_explain_code=False, checkpointer=None, smart_schema_pruning=False, safe_mode=True)` | Factory returning the compiled graph directly. Use when the caller wants to manage graph invocation and state manually. |
| `get_database_metadata` | `(connection, n_samples=10) -> dict` | SQLAlchemy metadata and sample-value summarization without an LLM call. |
| `build_query` | `(col_name_quoted: str, table_name_quoted: str, n: int, dialect_name: str) -> str` | Internal-style helper used by metadata sampling to build dialect-aware column sample queries. |
| `_validate_sql` | `(sql_text: str, safe_mode: bool = True)` | Basic read-only check. Returns an error string when rejected, otherwise `None`. |

## `SQLDatabaseAgent` parameters

| Parameter | Default | Operating note |
| --- | --- | --- |
| `model` | required | A LangChain-compatible chat model. Provider setup is outside this skill. |
| `connection` | required | SQLAlchemy `Engine` or `Connection`. Engines are opened as needed; explicit connections should be managed and closed by the caller. |
| `n_samples` | `1` | Number of sample values per column included in metadata. Keep low for large, sensitive, or token-heavy databases. |
| `log` | `False` | When `True`, generated Python functions and errors may be written to the requested log directory. Keep `False` unless the user wants files. |
| `log_path` | `None` | Used only when `log=True`. Do not expose machine-local paths in user-facing reports. |
| `file_name` | `'sql_database.py'` | Generated function filename used for logging. |
| `function_name` | `'sql_database_pipeline'` | Name of the generated Python function that calls `pandas.read_sql`. Empty values are reset to the default. |
| `overwrite` | `True` | Controls generated log-file overwrite behavior when logging is enabled. |
| `human_in_the_loop` | `False` | Adds a review step over recommended SQL steps. Requires a checkpointer; the implementation can fill in an in-memory saver if none is supplied. |
| `bypass_recommended_steps` | `False` | Skips the separate recommended-steps generation phase. If `human_in_the_loop=True`, the implementation forces this back to `False`. |
| `bypass_explain_code` | `False` | Skips final explanatory reporting and can reduce latency. |
| `checkpointer` | `None` | LangGraph checkpoint saver for human review or externally managed state. |
| `smart_schema_pruning` | `False` | Uses an additional LLM step to filter large metadata to relevant schema pieces. Helpful for large schemas, but adds model latency/cost. |
| `safe_mode` | `True` | Enforces a conservative SELECT-only check before executing generated SQL. Keep enabled by default. |

## Invocation methods and getters

| Method | Signature / behavior | Notes |
| --- | --- | --- |
| `invoke_agent` | `(user_instructions: str = None, max_retries=3, retry_count=0, **kwargs)` | Synchronous object wrapper. Returns `None`; read outputs via getters. |
| `ainvoke_agent` | Async equivalent of `invoke_agent` | Use in async UI/service contexts. |
| `invoke_messages` | `(messages: Sequence[BaseMessage], **kwargs)` | Uses explicit chat messages, deriving `user_instructions` from the last user message if not supplied. Useful inside teams. |
| `ainvoke_messages` | Async equivalent of `invoke_messages` | Async team/UI use. |
| `update_params` | `(**kwargs)` | Updates parameters and rebuilds the compiled graph; the previous response is reset. |
| `get_response` | inherited from the base agent | Returns the full graph response dictionary after an invocation. |
| `get_sql_query_code(markdown=False)` | Returns generated SQL or Markdown-wrapped SQL | Use this to audit the exact query. |
| `get_data_sql()` | Returns query result dict or `None` | Convert with `pandas.DataFrame(result)` when a table is needed. |
| `get_sql_database_function(markdown=False)` | Returns generated Python function code | Helpful for audit/logging; do not execute manually unless reviewed. |
| `get_recommended_sql_steps(markdown=False)` | Returns recommended steps | Only present when the steps phase was not bypassed. |
| `get_workflow_summary(markdown=False)` | Summarizes final agent messages | Depends on response messages. |
| `get_log_summary(markdown=False)` | Summarizes logged output paths | Only meaningful when logging is enabled. |
| `show()` | Renders the graph diagram in notebook contexts | Optional visualization aid, not required for operation. |

## Response keys to check

The compiled graph uses a response dictionary. Common keys include:

- `recommended_steps`: recommended SQL steps, when generated.
- `all_sql_database_summary`: metadata summary used in prompts.
- `sql_query_code`: generated SQL text.
- `sql_database_function`: generated Python function that executes `pandas.read_sql`.
- `sql_database_function_path`, `sql_database_function_file_name`, `sql_database_function_name`: logging-related fields when generated code is saved.
- `data_sql`: query result after post-processing; usually a dictionary suitable for `pandas.DataFrame`.
- `sql_database_error`: validation or execution error string.
- `sql_database_error_log_path`: logging-related error path when `log=True`.
- `messages`: final report messages emitted by the graph.

Always inspect `sql_database_error` before trusting `data_sql`. A `None` result can mean validation was blocked, query execution failed, or the graph was not invoked.
