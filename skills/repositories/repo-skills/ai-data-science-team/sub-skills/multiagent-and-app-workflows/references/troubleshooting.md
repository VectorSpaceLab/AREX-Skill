# Multiagent And App Troubleshooting

Use this guide when multi-agent composition, supervisor routing, app startup, or Pipeline Studio behavior fails. Each row names the symptom, likely cause, and recovery steps.

## Import And Environment Symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'IPython'` during package import | The package imports notebook display helpers, but `ipython` may be absent from a minimal install. | Install `ipython` into the active environment, rerun `python scripts/inspect_multiagent_api.py --format text`, then retry imports. |
| `ModuleNotFoundError` for LangChain, LangGraph, SQLAlchemy, Plotly, or Streamlit | The active Python environment is not the package environment or base dependencies were not installed. | Reinstall the package with its base requirements in the active environment. Verify with the bundled inspection script before invoking agents or apps. |
| Streamlit command is unavailable | Streamlit is not installed or the wrong Python executable is running the command. | Run `python -m streamlit --version`. If unavailable, install Streamlit in the same environment as `ai_data_science_team`. |
| `langchain_ollama` is missing when selecting Ollama in an app | Ollama provider support is optional in the app path. | Install the optional provider package or switch to a provider already available in the environment. |

## Pandas And SQL Analyst Symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Pandas analyst returns a table when a chart was expected | The router did not classify the prompt as chart-producing, or chart generation failed. | Ask explicitly for a chart type and encoding. Inspect `response["routing_preprocessor_decision"]`, `response["plotly_error"]`, `get_data_wrangled()`, and `get_data_visualization_function()`. |
| `get_plotly_graph()` returns `None` | No Plotly graph was produced, SQL/Pandas data was empty, or visualization failed. | Inspect `plotly_error` and verify the intermediate table with `get_data_wrangled()` or `get_data_sql()`. Return the table fallback if the chart cannot be produced. |
| `get_data_wrangled()` or `get_data_sql()` returns `None` | The run did not complete, response state was overwritten, or the agent failed before producing data. | Check `.response`, `get_state_keys()`, and recent messages. Retry with a smaller sample or clearer instructions. |
| SQL analyst generates no chart because SQL returned no rows | The SQL query produced an empty result or the SQL database agent failed. | Inspect `get_sql_query_code()` and route SQL query/safety diagnosis to `../sql-analysis/SKILL.md`. |
| SQL connection works in a script but fails in Streamlit | Connection object is reused across UI reruns or threads. | Create the connection inside the app/session scope and use SQLAlchemy options appropriate for the database. For SQLite UI usage, allow cross-thread access only when safe for the app. |

## Supervisor Team Symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| The supervisor reloads data or asks for data again on a follow-up prompt | Previous artifacts were not passed into the next team call. | Save `artifacts = team.get_artifacts() or {}` after each run and pass `artifacts=artifacts` to dependent follow-up calls. |
| The wrong dataset is used for visualization or modeling | Multiple datasets exist and the active dataset is not the intended stage. | Ask the user to select the active dataset or state the stage explicitly, such as cleaned, SQL result, wrangled, or feature-engineered data. In Pipeline Studio, use the active dataset override. |
| The same worker appears to run repeatedly | The user prompt is broad or unresolved, worker output did not satisfy the route condition, or state was not updated as expected. | Inspect `last_worker`, `handled_steps`, `attempted_steps`, and artifacts. Split the prompt into narrower steps or use `WorkflowPlannerAgent` to make the intended sequence explicit. |
| The supervisor does not run H2O or MLflow steps | Optional ML dependencies or services are unavailable, or the prompt did not explicitly request those capabilities. | Confirm the task really needs H2O/MLflow. Route setup and optional dependency details to `../modeling-and-mlflow/SKILL.md`. |
| Modeling/evaluation is requested but the team asks a question instead | The target variable is missing. | Ask for the target column, then rerun the plan or supervisor request with the target included. |
| Planner returns questions and omits `model`/`evaluate` | This is intended behavior when dependent information is missing. | Answer the questions first; do not force the omitted steps until the required information is available. |

## Human Review And Interrupt Symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| A graph appears to pause or hang at a review step | A human-in-the-loop worker emitted a LangGraph interrupt. | Retrieve the graph state with the same thread configuration, display the interrupt value to the user, then resume with the user's review response. |
| Human review cannot resume | The checkpointer or thread configuration changed between pause and resume. | Reuse the same checkpointer and stable thread identifier. If the app cannot manage interrupts, rerun the relevant single-agent workflow directly. |
| A supervisor/app hides review as a generic failure | The UI path does not surface inner worker interrupts. | Detect interrupt state explicitly, tell the user review is pending, and route detailed single-agent recovery to `../dataframe-code-agents/SKILL.md`. |

## Streamlit App Symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| App stops before showing the main workspace | Required provider configuration is missing, optional provider package is missing, or import validation failed. | Verify package imports and Streamlit version. Configure the provider outside this skill, then restart the app. |
| App launches but chat input fails immediately | The model provider, database connection, or optional worker dependency is unavailable. | Start with a no-service import check, then isolate the failing area: provider setup, SQL connection, optional EDA report package, H2O, or MLflow. |
| Uploaded file is not reflected in Pipeline Studio | Session state was reset, upload parsing failed, or the dataset registry was not synchronized. | Re-upload the file, verify preview rows, enable sync from Pipeline Studio state to agents, and inspect the active dataset selection. |
| Pipeline Studio project reload is missing data | Metadata-only save requires source rehydration, or sources moved. | Use the rehydrate option when loading. If sources are gone, use a full-data save from a trusted origin or relink sources manually. |
| Pipeline Studio cache grows too large | Dataset cache persistence is enabled without pruning. | Reduce cache max item count or size, convert projects to metadata-only, or disable dataset cache. |
| Edited code node fails when rerun locally | Draft code depends on variables, columns, or imports not present in the selected node context. | Inspect node metadata and selected dataset columns. Add missing imports or select the correct parent node before rerunning. |
| App UI becomes confusing after many turns | Chat history, selected node, and active dataset diverged. | Clear chat or start a new project/session, then reload or select the intended dataset/node explicitly. |

## Optional Capability Boundaries

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Optional EDA report tools are unavailable | Extra EDA libraries were not installed in the minimum environment. | Use basic describe/correlation/missingness outputs or route optional report setup to `../data-access-and-eda/SKILL.md`. |
| H2O import, Java runtime, or training fails | H2O AutoML is optional and may require additional runtime support. | Route to `../modeling-and-mlflow/SKILL.md`; do not claim supervisor ML execution was verified if optional runtime is absent. |
| MLflow UI or run lookup fails | Tracking URI, artifact location, backend store, or UI service is not available. | Route to `../modeling-and-mlflow/SKILL.md`; verify tracking configuration before asking the supervisor to log or inspect runs. |

## Minimal Recovery Checklist

1. Run `python scripts/inspect_multiagent_api.py --format text`.
2. Confirm the task belongs to this sub-skill instead of a sibling sub-skill.
3. Choose the narrowest graph: Pandas analyst, SQL analyst, planner, supervisor, or app.
4. Verify the required data/connection/active dataset is present.
5. If continuing a supervisor conversation, pass previous artifacts forward.
6. If using an app, confirm the working directory and whether persistence/cache/project saves may write files.
7. Retry with a smaller, explicit prompt and inspect response keys before escalating to optional dependencies or service launches.
