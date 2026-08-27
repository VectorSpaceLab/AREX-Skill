---
name: multiagent-and-app-workflows
description: "Compose ai-data-science-team multi-agent workflows and understand
  the package's Streamlit application patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Multiagent And App Workflows

Use this sub-skill when the task is about composing multiple `ai_data_science_team` agents, selecting a team workflow, inspecting multi-agent outputs, or understanding the packaged Streamlit app patterns including AI Pipeline Studio.

## Best Fit

Use this sub-skill for:

- `PandasDataAnalyst`: data wrangling followed by optional Plotly visualization.
- `SQLDataAnalyst`: SQL querying followed by optional Plotly visualization.
- `SupervisorDSTeam` / `make_supervisor_ds_team`: supervisor-led routing across data loading, wrangling, cleaning, EDA, visualization, SQL, feature engineering, model evaluation, H2O, and MLflow workers.
- `WorkflowPlannerAgent`: structured plans for the supervisor-led team.
- Streamlit app workflow understanding, safe launch planning, and AI Pipeline Studio project/pipeline behavior.
- Multi-turn artifacts and active-dataset handoff between team calls.

## Route Elsewhere

- For detailed parameters of `DataCleaningAgent`, `DataWranglingAgent`, `DataVisualizationAgent`, or `FeatureEngineeringAgent`, read `../dataframe-code-agents/SKILL.md`.
- For direct data loading, file discovery, EDA-only tools, or optional EDA reports, read `../data-access-and-eda/SKILL.md`.
- For SQL safe mode, SQL metadata, schema sampling, and direct `SQLDatabaseAgent` use, read `../sql-analysis/SKILL.md`.
- For H2O AutoML, deterministic model evaluation internals, MLflow tools, and optional ML dependencies, read `../modeling-and-mlflow/SKILL.md`.

## Required Reading

1. Read `references/api-reference.md` for constructors, factories, methods, and response getters.
2. Read `references/workflows.md` for composition patterns and artifact handoff.
3. Read `references/apps-and-pipeline-studio.md` before advising on any Streamlit app or AI Pipeline Studio behavior.
4. Read `references/troubleshooting.md` when imports, routing, app startup, state handoff, visualization, or optional services fail.

## Operating Rules

- Treat every `model` argument as a potentially external LLM-backed runtime dependency. Do not invoke agents unless the user explicitly asks to run them and the runtime is configured.
- Do not launch Streamlit apps or other long-running UI services unless the user explicitly asks for an app launch. Prefer explaining setup and verifying imports first.
- Do not place provider settings, local environment names, or user-specific paths in generated code or saved notes.
- Reuse artifacts between team calls: pass `team.get_artifacts()` into the next `team.invoke_agent(..., artifacts=artifacts)` when the second request depends on previous data.
- Prefer the smallest composition that satisfies the request. Use `PandasDataAnalyst` or `SQLDataAnalyst` for two-step workflows; use `SupervisorDSTeam` for broad, multi-step, cross-capability tasks.
- For read-only inspection without an LLM call, run `scripts/inspect_multiagent_api.py`.

## Quick Selection

| User intent | Start here | Notes |
| --- | --- | --- |
| "Wrangle this DataFrame and maybe chart it" | `PandasDataAnalyst` | Requires prebuilt wrangling and visualization agents. |
| "Query this database and maybe chart results" | `SQLDataAnalyst` | Requires prebuilt SQL and visualization agents. SQL safety details belong to `sql-analysis`. |
| "Run a data-science team over uploaded data" | `SupervisorDSTeam` | Build all worker agents; pass artifacts across turns. |
| "Plan the steps before running" | `WorkflowPlannerAgent` | Produces a JSON-like plan; it does not execute work. |
| "Use Pipeline Studio / Streamlit app" | `references/apps-and-pipeline-studio.md` | Treat app launch as an interactive service operation. |
