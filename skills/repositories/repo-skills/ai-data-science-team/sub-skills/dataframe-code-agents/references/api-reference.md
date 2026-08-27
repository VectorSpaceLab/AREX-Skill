# API reference: dataframe code agents

Use these APIs after data is already loaded. For file loading and EDA-only summaries, route to `../../data-access-and-eda/SKILL.md`.

## Imports

```python
from ai_data_science_team.agents import (
    DataCleaningAgent,
    DataWranglingAgent,
    DataVisualizationAgent,
    FeatureEngineeringAgent,
)
```

Lower-level graph factories are also public:

```python
from ai_data_science_team.agents import (
    make_data_cleaning_agent,
    make_data_wrangling_agent,
    make_data_visualization_agent,
    make_feature_engineering_agent,
)
```

## Class wrappers

| Class | Constructor signature | Main use |
|---|---|---|
| `DataCleaningAgent` | `(model, n_samples=30, log=False, log_path=None, file_name='data_cleaner.py', function_name='data_cleaner', overwrite=True, human_in_the_loop=False, bypass_recommended_steps=False, bypass_explain_code=False, checkpointer=None)` | Generate, run, fix, and report a pandas cleaning function for one DataFrame. |
| `DataWranglingAgent` | `(model, n_samples=30, log=False, log_path=None, file_name='data_wrangler.py', function_name='data_wrangler', overwrite=True, human_in_the_loop=False, bypass_recommended_steps=False, bypass_explain_code=False, checkpointer=None)` | Generate, run, fix, and report a pandas wrangling function for one or more DataFrames. |
| `DataVisualizationAgent` | `(model, n_samples=30, log=False, log_path=None, file_name='data_visualization.py', function_name='data_visualization', overwrite=True, human_in_the_loop=False, bypass_recommended_steps=False, bypass_explain_code=False, checkpointer=None)` | Generate, run, fix, validate, and report a Plotly figure function for one DataFrame. |
| `FeatureEngineeringAgent` | `(model, n_samples=30, log=False, log_path=None, file_name='feature_engineer.py', function_name='feature_engineer', overwrite=True, human_in_the_loop=False, bypass_recommended_steps=False, bypass_explain_code=False, checkpointer=None)` | Generate, run, fix, and report a generic feature-engineering function for one DataFrame with optional target column. |

The `make_*_agent(...)` factories accept the same constructor parameters and return the compiled LangGraph state graph directly. Prefer the class wrappers for normal use because they store `response` and provide retrieval helpers.

## Common constructor parameters

| Parameter | Applies to | Meaning and operational guidance |
|---|---|---|
| `model` | All | A caller-supplied LangChain-compatible model object. Invoking an agent will call this object. |
| `n_samples` | All | Number of sample rows used in prompt summaries. Lower this for wide tables or token pressure. Some internal summaries cap columns and characters. |
| `log` | All | When `True`, generated functions and error logs can be written under `log_path`. Keep `False` for no generated-code files. |
| `log_path` | All | Directory for generated function/error files. Use an explicit relative path chosen by the caller. |
| `file_name` | All | Name for the logged generated function file. Defaults differ by agent. |
| `function_name` | All | Name that generated code must define and the sandbox will call. Defaults differ by agent. |
| `overwrite` | All | With `log=True`, overwrite the generated function file if `True`; create a unique suffix if `False`. |
| `human_in_the_loop` | All | Add a human review interrupt after generated code execution. Requires a checkpointer; the package creates an in-memory one if omitted. |
| `bypass_recommended_steps` | All | Skip the model-generated recommendation step and go directly to code generation using defaults/instructions. If human review is enabled, the package forces this back to `False`. |
| `bypass_explain_code` | All | Skip the final deterministic report node after execution/review. |
| `checkpointer` | All | LangGraph checkpointer used for resumable human review. |

## Invocation methods

| Method | Agents | Inputs |
|---|---|---|
| `invoke_agent(...)` | All | Synchronous convenience wrapper. Returns `None` and stores the state dict in `agent.response`. |
| `ainvoke_agent(...)` | All | Async convenience wrapper. Returns `None` and stores the state dict in `agent.response`. |
| `invoke_messages(messages=..., ...)` | All | Supervisor/team-friendly wrapper that accepts an explicit message sequence and extracts the latest user text if `user_instructions` is not supplied. |
| `ainvoke_messages(messages=..., ...)` | All | Async version of `invoke_messages`. |
| `invoke(input=..., config=..., **kwargs)` | All via `BaseAgent` | Delegates to the compiled graph and stores the returned state dict in `response`. Useful for `Command(resume=...)` during human review. |
| `ainvoke`, `stream`, `astream` | All via `BaseAgent` | Delegated graph methods for async or streaming graph operation. |

### Agent-specific invocation signatures

```python
DataCleaningAgent.invoke_agent(
    data_raw: pandas.DataFrame,
    user_instructions: str | None = None,
    max_retries: int = 3,
    retry_count: int = 0,
    **kwargs,
)

DataWranglingAgent.invoke_agent(
    data_raw: pandas.DataFrame | dict | list,
    user_instructions: str | None = None,
    max_retries: int = 3,
    retry_count: int = 0,
    **kwargs,
)

DataVisualizationAgent.invoke_agent(
    data_raw: pandas.DataFrame,
    user_instructions: str | None = None,
    max_retries: int = 3,
    retry_count: int = 0,
    **kwargs,
)

FeatureEngineeringAgent.invoke_agent(
    data_raw: pandas.DataFrame,
    user_instructions: str | None = None,
    target_variable: str | None = None,
    max_retries: int = 3,
    retry_count: int = 0,
    **kwargs,
)
```

`DataWranglingAgent` accepts a single `DataFrame`, a single dict, a list of DataFrames, or a list of dicts. Internally it converts DataFrames to dicts and runs generated code with sandbox `data_format='dataframe_list'`.

## Retrieval helpers

| Agent | Result getters | Generated code getter | Recommendation getter | Other helpers |
|---|---|---|---|---|
| `DataCleaningAgent` | `get_data_cleaned()`, `get_data_raw()` | `get_data_cleaner_function(markdown=False)` | `get_recommended_cleaning_steps(markdown=False)` | `get_workflow_summary(markdown=False)`, `get_log_summary(markdown=False)`, `get_response()` |
| `DataWranglingAgent` | `get_data_wrangled()`, `get_data_raw()` | `get_data_wrangler_function(markdown=False)` | `get_recommended_wrangling_steps(markdown=False)` | `get_workflow_summary(markdown=False)`, `get_log_summary(markdown=False)`, `get_response()` |
| `DataVisualizationAgent` | `get_plotly_graph()`, `get_data_raw()` | `get_data_visualization_function(markdown=False)` | `get_recommended_visualization_steps(markdown=False)` | `run_smoke_tests(...)`, `get_workflow_summary(markdown=False)`, `get_log_summary(markdown=False)`, `get_response()` |
| `FeatureEngineeringAgent` | `get_data_engineered()`, `get_data_raw()` | `get_feature_engineer_function(markdown=False)` | `get_recommended_feature_engineering_steps(markdown=False)` | `get_workflow_summary(markdown=False)`, `get_log_summary(markdown=False)`, `get_response()` |

All class wrappers also expose `BaseAgent` graph inspection helpers such as `get_state_keys()`, `get_state_properties()`, `get_state(config)`, `get_state_history(config)`, `update_state(config, values, as_node=None)`, and `show()`.

## Response keys

The stored response is a dict. Keys vary by agent and by which nodes executed.

| Agent | Primary output keys | Generated function keys | Error/log keys | Summary/report keys |
|---|---|---|---|---|
| Cleaning | `data_raw`, `data_cleaned` | `data_cleaner_function`, `data_cleaner_function_path`, `data_cleaner_file_name`, `data_cleaner_function_name` | `data_cleaner_error`, `data_cleaner_error_log_path` | `recommended_steps`, `all_datasets_summary`, `data_cleaning_summary`, `messages`, `max_retries`, `retry_count` |
| Wrangling | `data_raw`, `data_wrangled` | `data_wrangler_function`, `data_wrangler_function_path`, `data_wrangler_file_name`, `data_wrangler_function_name` | `data_wrangler_error`, `data_wrangler_error_log_path` | `recommended_steps`, `all_datasets_summary`, `data_wrangling_summary`, `messages`, `max_retries`, `retry_count` |
| Visualization | `data_raw`, `plotly_graph` | `data_visualization_function`, `data_visualization_function_path`, `data_visualization_function_file_name`, `data_visualization_function_name` | `data_visualization_error`, `data_visualization_error_log_path`, `data_visualization_warning` | `recommended_steps`, `all_datasets_summary`, `data_visualization_summary`, `messages`, `max_retries`, `retry_count` |
| Feature engineering | `data_raw`, `data_engineered`, `target_variable` | `feature_engineer_function`, `feature_engineer_function_path`, `feature_engineer_file_name`, `feature_engineer_function_name` | `feature_engineer_error`, `feature_engineer_error_log_path` | `recommended_steps`, `all_datasets_summary`, `messages`, `max_retries`, `retry_count` |

## Generated function contracts

| Agent | Default generated function name | Input expected inside sandbox | Required return |
|---|---|---|---|
| Cleaning | `data_cleaner` | One pandas DataFrame | A pandas DataFrame or JSON-serializable DataFrame-like object with cleaned data. |
| Wrangling | `data_wrangler` | A list of pandas DataFrames, even when the caller supplied one DataFrame | A single pandas DataFrame. If a list is returned, the package attempts to concatenate it. |
| Visualization | `data_visualization` | One pandas DataFrame | A JSON-serializable Plotly figure dict. The package reconstructs it for validation and `get_plotly_graph()`. |
| Feature engineering | `feature_engineer` | One pandas DataFrame | A pandas DataFrame or JSON-serializable DataFrame-like object. If `target_variable` is supplied, output validation requires that column to remain present. |

## Shared graph behavior

All four agents use a common coding graph pattern:

1. Recommend steps or instructions unless `bypass_recommended_steps=True`.
2. Generate a Python function via the supplied model.
3. Normalize generated code by moving imports inside the function and adding an agent comment header.
4. Execute generated code in a subprocess sandbox.
5. If execution produced an error and `retry_count < max_retries`, ask the supplied model to repair the function and retry.
6. If `human_in_the_loop=True`, pause for review with an interrupt.
7. Report selected state keys into `messages` unless `bypass_explain_code=True`.

The report node does not call a model; it serializes selected state keys into an `AIMessage`.

## Sandbox and logging helpers

Relevant internal helpers:

| Helper | Signature | Behavior |
|---|---|---|
| `run_code_sandboxed_subprocess` | `(*, code_snippet, function_name, data, timeout=10, memory_limit_mb=512, data_format='dataframe')` | Runs generated code in a child Python process, blocks common filesystem/process/network imports, applies a timeout and best-effort memory cap, and returns `(result, error)`. |
| `log_ai_function` | `(response, file_name, log=True, log_path='./logs/', overwrite=True)` | Writes generated function text only when logging is enabled. |
| `log_ai_error` | `(error_message, file_name='errors.log', log=True, log_path='./logs/', overwrite=False)` | Appends or overwrites generated execution errors only when logging is enabled. |

Use the bundled no-model inspection probe to confirm imports, public signatures, and sandbox availability:

```bash
python scripts/inspect_dataframe_agents.py --json
```
