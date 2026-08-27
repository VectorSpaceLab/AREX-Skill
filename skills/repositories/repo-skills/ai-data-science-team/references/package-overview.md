# Package overview

Read this for shared package facts before choosing a sub-skill.

## Public package shape

`ai-data-science-team` provides AI-assisted data science agents and helper tools around pandas, SQLAlchemy, LangGraph/LangChain, Streamlit, H2O, and MLflow.

Top-level imports expose the most common classes:

```python
from ai_data_science_team import (
    DataCleaningAgent, DataLoaderToolsAgent, DataVisualizationAgent,
    SQLDatabaseAgent, DataWranglingAgent, FeatureEngineeringAgent,
    EDAToolsAgent, H2OMLAgent, MLflowToolsAgent,
    SQLDataAnalyst, PandasDataAnalyst,
)
```

Additional public objects live under these modules:

| Module family | Main objects | Owning sub-skill |
| --- | --- | --- |
| `ai_data_science_team.tools.data_loader` | `load_file`, `load_directory`, `auto_load_file`, `load_csv`, `load_excel`, `load_json`, `load_parquet`, `load_pickle`, file discovery helpers | `data-access-and-eda` |
| `ai_data_science_team.tools.dataframe`, `tools.eda` | `get_dataframe_summary`, `describe_dataset`, `visualize_missing`, `generate_correlation_funnel`, `generate_sweetviz_report`, `generate_dtale_report` | `data-access-and-eda` |
| `ai_data_science_team.agents` | data cleaning, wrangling, visualization, feature engineering, SQL, data loader, workflow planner classes/factories | `dataframe-code-agents`, `sql-analysis`, `multiagent-and-app-workflows` |
| `ai_data_science_team.ds_agents` | `EDAToolsAgent`, `make_eda_tools_agent` | `data-access-and-eda` |
| `ai_data_science_team.ml_agents` | `H2OMLAgent`, `MLflowToolsAgent`, `ModelEvaluationAgent` | `modeling-and-mlflow` |
| `ai_data_science_team.multiagents` | `PandasDataAnalyst`, `SQLDataAnalyst`; supervisor team objects in the supervisor module | `multiagent-and-app-workflows` |
| `ai_data_science_team.templates` | `BaseAgent`, graph/node helpers | support detail for code-agent and multi-agent workflows |

## Common constructor patterns

Most LLM-backed agents require a LangChain-compatible `model` object. The repository examples use OpenAI chat models, but local Ollama chat models are also supported when configured by the caller.

Common single-agent parameters:

- `n_samples`: how many rows/summary samples to include in prompts; reduce this for wide or large data.
- `log`, `log_path`, `file_name`, `function_name`, `overwrite`: generated-code and error logging controls.
- `human_in_the_loop`: enables LangGraph interrupt/resume review before generated code execution.
- `bypass_recommended_steps`: skip the planning/recommended-step node.
- `bypass_explain_code`: skip generated code explanation.
- `checkpointer`: LangGraph checkpointer for persistent state/resume workflows.
- `max_retries`, `retry_count`: passed to `invoke_agent`/`invoke_messages` to control repair loops.

Tool-calling agents such as `DataLoaderToolsAgent`, `EDAToolsAgent`, and `MLflowToolsAgent` commonly accept `create_react_agent_kwargs`, `invoke_react_agent_kwargs`, `checkpointer`, and `log_tool_calls`.

## Response and getter pattern

Most class wrappers store the last graph/tool response on `agent.response` and expose typed getters. Examples:

- Data cleaning: `get_data_cleaned()`, `get_data_cleaner_function()`, `get_recommended_cleaning_steps()`, `get_workflow_summary()`.
- Wrangling: `get_data_wrangled()`, `get_data_wrangler_function()`, `get_recommended_wrangling_steps()`.
- Visualization: `get_plotly_graph()`, `get_data_visualization_function()`, `run_smoke_tests()`.
- SQL: `get_data_sql()`, `get_sql_query_code()`, `get_sql_database_function()`, `get_recommended_sql_steps()`.
- Multi-agent analysts: getters expose component outputs such as wrangled data, SQL code, Plotly graph, component functions, and workflow summary.
- Tool-calling agents: `get_ai_message()`, `get_artifacts()`, and `get_tool_calls()` reveal natural-language output, structured artifacts, and called tools.

If a getter returns `None`, verify that an invocation completed, that the expected graph path ran, and that optional dependencies/services were available.

## Install and optional dependencies

Base install covers the package's core imports and app dependencies. For source checkouts, `pip install -e .` follows package metadata. For public package use, prefer:

```bash
pip install ai-data-science-team ipython
```

Install only the extra needed by the task:

```bash
pip install "ai-data-science-team[data_science]"   # missingno, pytimetk, sweetviz
pip install "ai-data-science-team[machine_learning]"  # h2o, mlflow
pip install dtale  # only for D-Tale report support
```

The package imports `IPython.display` in several modules; install `ipython` if the package imports fail with `ModuleNotFoundError: IPython`.

## Credential and service assumptions

LLM-backed agents do not create model clients themselves. Future agents must construct and pass a model, for example an OpenAI or Ollama chat model, and must ensure any provider credentials or local services are configured before invoking the package.

Optional services:

- Ollama requires the Ollama daemon and the requested local model.
- H2O AutoML requires the H2O Python package and a usable local H2O/Java runtime.
- MLflow workflows require the `mlflow` package and a tracking URI/store appropriate for the task.
- Streamlit apps launch long-running UI services; do not start them unless requested.

## Verification helpers

Use the root [`../scripts/check_env.py`](../scripts/check_env.py) for safe import/signature checks and optional dependency visibility. Use owning sub-skill scripts for more focused checks:

- Data/file/EDA helper smoke: `sub-skills/data-access-and-eda/scripts/smoke_data_access.py`.
- DataFrame code-agent signature inspection: `sub-skills/dataframe-code-agents/scripts/inspect_dataframe_agents.py`.
- SQL metadata and safety smoke: `sub-skills/sql-analysis/scripts/smoke_sql_safety.py`.
- Optional H2O/MLflow dependency check: `sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py`.
- Multi-agent and Streamlit import inspection: `sub-skills/multiagent-and-app-workflows/scripts/inspect_multiagent_api.py`.
