# Multiagent API Reference

This reference covers the public multi-agent and app-facing orchestration APIs in `ai_data_science_team` version `0.0.0.9017`. These objects build LangGraph workflows around single-purpose agents; they are not pure data helpers and can call an LLM when invoked.

## Imports

```python
from ai_data_science_team import PandasDataAnalyst
from ai_data_science_team.multiagents import SQLDataAnalyst
from ai_data_science_team.multiagents.supervisor_ds_team import SupervisorDSTeam, make_supervisor_ds_team
from ai_data_science_team.agents import WorkflowPlannerAgent
```

The root package also exports `DataWranglingAgent`, `DataVisualizationAgent`, `DataCleaningAgent`, `DataLoaderToolsAgent`, `SQLDatabaseAgent`, and `FeatureEngineeringAgent`. Detailed single-agent parameters belong to sibling sub-skills.

## Composition Classes And Factories

| Object | Signature | Role |
| --- | --- | --- |
| `PandasDataAnalyst` | `(model, data_wrangling_agent, data_visualization_agent, checkpointer=None)` | Wraps a wrangling graph plus visualization graph. Routes a user prompt to a table result by default or to chart generation when the prompt asks for a chart. |
| `make_pandas_data_analyst` | `(model, data_wrangling_agent, data_visualization_agent, checkpointer=None)` | Factory returning the compiled LangGraph for the Pandas analyst. The two sub-agent arguments are compiled state graphs. |
| `SQLDataAnalyst` | `(model, sql_database_agent, data_visualization_agent, checkpointer=None)` | Wraps a SQL database graph plus visualization graph. Routes a user prompt to SQL-only table output by default or to chart generation when requested. |
| `make_sql_data_analyst` | `(model, sql_database_agent, data_visualization_agent, checkpointer=None)` | Factory returning the compiled LangGraph for the SQL analyst. The two sub-agent arguments are compiled state graphs. |
| `WorkflowPlannerAgent` | `(model, log=False)` | Produces a structured plan for the supervisor-led team. It records `steps`, `target_variable`, `questions`, and `notes`; it does not execute data tasks. |
| `SupervisorDSTeam` | `(model, data_loader_agent, data_wrangling_agent, data_cleaning_agent, eda_tools_agent, data_visualization_agent, sql_database_agent, feature_engineering_agent, h2o_ml_agent, mlflow_tools_agent, model_evaluation_agent, workflow_planner_agent=None, checkpointer=None, temperature=1.0)` | OO wrapper around the supervisor-led data-science team graph. Holds response state and convenience methods. |
| `make_supervisor_ds_team` | same arguments as `SupervisorDSTeam` | Factory returning the compiled supervisor graph. Use when a compiled graph is needed directly. |

## `PandasDataAnalyst`

### Construction

```python
pandas_agent = PandasDataAnalyst(
    model=llm,
    data_wrangling_agent=data_wrangling_agent,
    data_visualization_agent=data_visualization_agent,
    checkpointer=checkpointer,
)
```

Important behavior:

- The constructor stores the supplied sub-agent instances and builds a compiled graph from their internal compiled graphs.
- `update_params(**kwargs)` replaces stored parameters and rebuilds the graph.
- `data_raw` may be a `pandas.DataFrame`, a `dict`, or a list of DataFrames/dicts. DataFrames are converted to dictionaries before graph invocation.
- The routing preprocessor returns `routing_preprocessor_decision`. If routing fails, the graph falls back to a table route.

### Invocation And Outputs

| Method | Signature | Use |
| --- | --- | --- |
| `invoke_agent` | `(user_instructions, data_raw, max_retries=3, retry_count=0, **kwargs)` | Synchronous run. Stores the graph response on `.response`. |
| `ainvoke_agent` | `(user_instructions, data_raw, max_retries=3, retry_count=0, **kwargs)` | Async run. Stores `.response`. |
| `invoke_messages` | `(messages, data_raw, max_retries=3, retry_count=0, **kwargs)` | Message-list run, useful inside larger teams. Derives `user_instructions` from the last human/user message if omitted. |
| `ainvoke_messages` | async version | Async message-list run. |
| `get_data_wrangled()` | no arguments | Returns a DataFrame from `response["data_wrangled"]` when present. |
| `get_plotly_graph()` | no arguments | Converts `response["plotly_graph"]` into a Plotly object when present. |
| `get_data_wrangler_function(markdown=False)` | optional Markdown wrapper | Returns generated wrangling function code. |
| `get_data_visualization_function(markdown=False)` | optional Markdown wrapper | Returns generated visualization function code. |
| `get_workflow_summary(markdown=False)` | optional Markdown wrapper | Summarizes the wrangling/visualization agent messages. |

Common response keys: `messages`, `routing_preprocessor_decision`, `data_wrangled`, `data_wrangler_function`, `data_visualization_function`, `plotly_graph`, `plotly_error`, `max_retries`, `retry_count`.

## `SQLDataAnalyst`

### Construction

```python
sql_agent = SQLDataAnalyst(
    model=llm,
    sql_database_agent=sql_database_agent,
    data_visualization_agent=data_visualization_agent,
    checkpointer=checkpointer,
)
```

Important behavior:

- The constructor stores a SQL database agent and a visualization agent, then builds a compiled graph from their internal compiled graphs.
- SQL details, read-only safety, schema sampling, and database connection setup are owned by `../sql-analysis/SKILL.md`.
- The graph routes to table output by default. It calls the visualization graph only when the route decision is `chart`.
- If SQL returns no data, visualization is skipped with a `plotly_error` message.

### Invocation And Outputs

| Method | Signature | Use |
| --- | --- | --- |
| `invoke_agent` | `(user_instructions, max_retries=3, retry_count=0, **kwargs)` | Synchronous SQL analyst run. |
| `ainvoke_agent` | async version | Async SQL analyst run. |
| `invoke_messages` | `(messages, max_retries=3, retry_count=0, **kwargs)` | Message-list run for teams/supervisors. |
| `ainvoke_messages` | async version | Async message-list run. |
| `get_data_sql()` | no arguments | Returns a DataFrame from `response["data_sql"]` when present. |
| `get_plotly_graph()` | no arguments | Converts `response["plotly_graph"]` into a Plotly object when present. |
| `get_sql_query_code(markdown=False)` | optional Markdown wrapper | Returns generated SQL text. |
| `get_sql_database_function(markdown=False)` | optional Markdown wrapper | Returns generated Python SQL execution function. |
| `get_data_visualization_function(markdown=False)` | optional Markdown wrapper | Returns generated visualization function code. |
| `get_workflow_summary(markdown=False)` | optional Markdown wrapper | Summarizes SQL and visualization agent messages. |

Common response keys: `messages`, `routing_preprocessor_decision`, `sql_query_code`, `sql_database_function`, `data_sql`, `data_visualization_function`, `plotly_graph`, `plotly_error`, `max_retries`, `retry_count`.

## `WorkflowPlannerAgent`

`WorkflowPlannerAgent` is a planner, not an executor. Use it before a supervisor-led run when the user asks for a broad pipeline or when dependent steps need clarification.

| Method | Signature | Use |
| --- | --- | --- |
| `invoke_messages` | `(messages, *, context=None, user_instructions=None, **kwargs)` | Produces a normalized plan from a message list and optional context. |
| `get_plan()` | no arguments | Returns the last plan dictionary. |
| `update_params(**kwargs)` | keyword updates | Replaces `model` or `log`. |

Plan shape:

```python
{
    "steps": ["load", "clean", "eda", "viz"],
    "target_variable": None,
    "questions": [],
    "notes": [],
}
```

Allowed step IDs are `list_files`, `load`, `merge`, `sql`, `wrangle`, `clean`, `eda`, `viz`, `feature`, `model`, `evaluate`, `mlflow_log`, and `mlflow_tools`. If `model` or `evaluate` is requested without a target variable, the planner removes those dependent steps and asks for the target.

## `SupervisorDSTeam`

The supervisor graph routes between these worker node names:

- `Data_Loader_Tools_Agent`
- `Data_Merge_Agent`
- `Data_Wrangling_Agent`
- `Data_Cleaning_Agent`
- `EDA_Tools_Agent`
- `Data_Visualization_Agent`
- `SQL_Database_Agent`
- `Feature_Engineering_Agent`
- `H2O_ML_Agent`
- `Model_Evaluation_Agent`
- `MLflow_Logging_Agent`
- `MLflow_Tools_Agent`

The supervisor tracks messages, current/active datasets, stage outputs, and an aggregated `artifacts` dictionary. After each worker, control returns to the supervisor; the supervisor then selects another worker or `FINISH`.

| Method | Signature | Use |
| --- | --- | --- |
| `invoke_messages` | `(messages, artifacts=None, **kwargs)` | Recommended message-list invocation. |
| `ainvoke_messages` | async version | Async message-list invocation. |
| `invoke_agent` | `(user_instructions, artifacts=None, **kwargs)` | Convenience wrapper for one user prompt. |
| `ainvoke_agent` | async version | Async one-prompt wrapper. |
| `invoke` | `(input, **kwargs)` | Direct compiled-graph passthrough. |
| `ainvoke` | async version | Async direct passthrough. |
| `get_ai_message(markdown=False)` | optional Markdown wrapper | Returns the last assistant/AI message from `.response`. |
| `get_artifacts()` | no arguments | Returns the aggregated artifacts dictionary from `.response`. |
| `show(xray=0)` | optional xray | Displays the supervisor graph in notebook environments when graph rendering is available. |

Important artifact keys include `data_loader`, `merge`, `data_wrangling`, `data_cleaning`, `eda`, `sql`, `data_visualization`, `feature_engineering`, `h2o`, `eval`, `mlflow`, `mlflow_log`, and `config`. The team also stores dataset registry metadata under `datasets`, `active_dataset_id`, and `active_data_key` in state.

## Inspection Script

Run the bundled script for no-call API inspection:

```bash
python scripts/inspect_multiagent_api.py --format json --fail-on-error
```

The script imports classes/factories, records signatures, reads installed distribution metadata, checks whether Streamlit imports, and performs no LLM calls, app launches, network access, downloads, training, or file writes.
