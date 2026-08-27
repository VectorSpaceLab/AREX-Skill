# Multiagent Workflow Patterns

This package has two lightweight analyst compositions and one broad supervisor-led team. Pick the narrowest graph that satisfies the user request.

## Selection Matrix

| Need | Use | Why |
| --- | --- | --- |
| One DataFrame or a list of DataFrames; ask for a transformed table or chart | `PandasDataAnalyst` | It combines wrangling and optional visualization. |
| One SQL connection; ask for a SQL result or chart | `SQLDataAnalyst` | It combines SQL generation/execution and optional visualization. |
| Multi-step data-science conversation with loading, EDA, cleaning, feature engineering, SQL, model/eval, or MLflow steps | `SupervisorDSTeam` | It maintains artifacts and routes across many workers. |
| Broad request that needs a proposed step list before execution | `WorkflowPlannerAgent` with the supervisor | It produces a plan and clarifying questions. |
| Interactive app or Pipeline Studio behavior | Streamlit app guidance | It is UI/service-oriented; read `apps-and-pipeline-studio.md`. |

## Pandas Analyst Composition

The Pandas analyst graph follows this sequence:

1. Normalize messages and user instructions.
2. Ask the model-backed router whether the task should produce a table or chart.
3. Always run the wrangling graph.
4. Run the visualization graph only when the route decision is `chart`.
5. Store a concise final message plus data/code/chart artifacts in `.response`.

Minimal pattern:

```python
from ai_data_science_team import PandasDataAnalyst, DataWranglingAgent, DataVisualizationAgent

wrangler = DataWranglingAgent(model=llm, bypass_recommended_steps=True)
visualizer = DataVisualizationAgent(model=llm, n_samples=10)
analyst = PandasDataAnalyst(
    model=llm,
    data_wrangling_agent=wrangler,
    data_visualization_agent=visualizer,
)

analyst.invoke_agent(
    user_instructions="Show the top 5 products by revenue as a bar chart.",
    data_raw=df,
)

result = analyst.get_response()
chart = analyst.get_plotly_graph()
table = analyst.get_data_wrangled()
```

Operational notes:

- For table-only tasks, inspect `get_data_wrangled()` and `get_data_wrangler_function()`.
- For chart tasks, inspect `get_plotly_graph()`, `get_data_visualization_function()`, and `response["plotly_error"]`.
- If the route decision is unclear or chart generation fails, return the table and explain the chart failure.
- Use `n_samples` on the component agents to limit prompt size for wide or large datasets.
- Detailed generated-code controls belong to `../dataframe-code-agents/SKILL.md`.

## SQL Analyst Composition

The SQL analyst graph follows this sequence:

1. Normalize messages and user instructions.
2. Route to table or chart.
3. Run the SQL database graph.
4. Run visualization only when the route decision is `chart` and SQL returned data.
5. Store SQL text, query data, optional chart, and generated code in `.response`.

Minimal pattern:

```python
from ai_data_science_team.multiagents import SQLDataAnalyst
from ai_data_science_team.agents import SQLDatabaseAgent, DataVisualizationAgent

sql_worker = SQLDatabaseAgent(model=llm, connection=connection, safe_mode=True)
visualizer = DataVisualizationAgent(model=llm, n_samples=10)
analyst = SQLDataAnalyst(
    model=llm,
    sql_database_agent=sql_worker,
    data_visualization_agent=visualizer,
)

analyst.invoke_agent("Aggregate sales by month and show a line chart.")
query = analyst.get_sql_query_code()
data = analyst.get_data_sql()
chart = analyst.get_plotly_graph()
```

Operational notes:

- Use `get_sql_query_code()` before trusting the data result.
- If a chart is missing, check whether SQL returned no rows or whether `plotly_error` was set.
- For database metadata, schema sampling, allowed SQL, and unsafe statement handling, read `../sql-analysis/SKILL.md`.

## Supervisor Team Composition

Use the supervisor when the task crosses multiple capabilities or requires conversation state across turns. Build all worker agents up front, even if some are optional in the immediate prompt, so the router has a complete worker map. If optional ML or MLflow dependencies are unavailable, route those details to `../modeling-and-mlflow/SKILL.md` and keep the supervisor run focused on available workers.

Minimal pattern:

```python
from ai_data_science_team.agents import (
    DataLoaderToolsAgent,
    DataWranglingAgent,
    DataCleaningAgent,
    DataVisualizationAgent,
    SQLDatabaseAgent,
    FeatureEngineeringAgent,
    WorkflowPlannerAgent,
)
from ai_data_science_team.ds_agents import EDAToolsAgent
from ai_data_science_team.ml_agents import H2OMLAgent, MLflowToolsAgent, ModelEvaluationAgent
from ai_data_science_team.multiagents.supervisor_ds_team import SupervisorDSTeam

team = SupervisorDSTeam(
    model=llm,
    workflow_planner_agent=WorkflowPlannerAgent(llm),
    data_loader_agent=DataLoaderToolsAgent(llm, invoke_react_agent_kwargs={"recursion_limit": 4}),
    data_wrangling_agent=DataWranglingAgent(llm),
    data_cleaning_agent=DataCleaningAgent(llm),
    eda_tools_agent=EDAToolsAgent(llm),
    data_visualization_agent=DataVisualizationAgent(llm),
    sql_database_agent=SQLDatabaseAgent(llm, connection=connection),
    feature_engineering_agent=FeatureEngineeringAgent(llm),
    h2o_ml_agent=H2OMLAgent(llm),
    mlflow_tools_agent=MLflowToolsAgent(llm),
    model_evaluation_agent=ModelEvaluationAgent(),
    checkpointer=checkpointer,
)

team.invoke_agent("Load the churn data, clean it, and summarize churn rate.")
artifacts = team.get_artifacts()

team.invoke_agent(
    "Using the cleaned dataset, plot churn rate by contract.",
    artifacts=artifacts,
)
```

### Supervisor Routing Rules

The supervisor combines a model-backed route decision with deterministic intent helpers. It routes only when the user asks for that capability and finishes once the request appears satisfied.

| Intent signal | Worker |
| --- | --- |
| load/import/read/list files | `Data_Loader_Tools_Agent` |
| merge/join/concat multiple loaded datasets | `Data_Merge_Agent` |
| wrangle/transform/reshape/rename | `Data_Wrangling_Agent` |
| clean/impute/fix anomalies | `Data_Cleaning_Agent` |
| describe/EDA/missingness/correlation/report | `EDA_Tools_Agent` |
| plot/chart/visualize | `Data_Visualization_Agent` |
| SQL/database/query/schema | `SQL_Database_Agent` |
| encode/scale/model-ready features | `Feature_Engineering_Agent` |
| train/AutoML/predict with H2O | `H2O_ML_Agent` |
| evaluate metrics/plots from a model | `Model_Evaluation_Agent` |
| log workflow artifacts to MLflow | `MLflow_Logging_Agent` |
| inspect MLflow runs/experiments/artifacts/UI | `MLflow_Tools_Agent` |

The supervisor also prevents many repeat routes by tracking `last_worker`, per-request handled steps, attempted steps, active dataset, and workflow plan state.

### Artifact Handoff

After any supervisor call:

```python
artifacts = team.get_artifacts() or {}
last_message = team.get_ai_message()
```

Pass `artifacts` back to the next call if the next prompt depends on loaded data, cleaned data, SQL data, charts, features, model information, evaluation outputs, or MLflow information. Important keys include:

- `data_loader`, `merge`, `data_wrangling`, `data_cleaning`, `eda`, `sql`, `data_visualization`, `feature_engineering`
- `h2o`, `eval`, `mlflow`, `mlflow_log`
- `config`, which can include app/supervisor switches such as `use_llm_intent_parser` or `proactive_workflow_mode`

If artifacts are not passed, the next call may behave like a fresh request and ask the loader to run again.

## Workflow Planner Pattern

Use the planner before a broad supervisor run when the user asks for an end-to-end workflow or when dependent modeling/evaluation steps need a target variable.

```python
from langchain_core.messages import HumanMessage
from ai_data_science_team.agents import WorkflowPlannerAgent

planner = WorkflowPlannerAgent(llm)
planner.invoke_messages(
    [HumanMessage(content="Plan a full churn analysis workflow.")],
    context={"proactive_workflow_mode": True},
)
plan = planner.get_plan()
```

If `plan["questions"]` is non-empty, ask those questions before executing dependent steps. Do not run `model` or `evaluate` steps without a target variable.

## Human Review And Interrupts

Human review is implemented by the underlying code-generating single agents through LangGraph interrupts. In a multi-agent or app setting:

- Use a checkpointer and stable thread configuration whenever an inner worker may pause.
- Surface the interrupt value to the user, then resume with the user's review response.
- If the UI cannot handle interrupts, run the relevant single-agent workflow directly and route detailed instructions to `../dataframe-code-agents/SKILL.md`.
- Do not hide a paused worker as a generic failure; tell the user the graph is waiting for review.

## Safe Verification Pattern

For inspection without running an LLM-backed workflow:

```bash
python scripts/inspect_multiagent_api.py --format text
```

For content-level validation, assert that the desired class imports, the expected signatures are present, and Streamlit imports. Do not treat that as proof that external providers, optional ML services, or full interactive apps were executed.
