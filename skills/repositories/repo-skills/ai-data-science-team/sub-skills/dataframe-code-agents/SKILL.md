---
name: dataframe-code-agents
description: "Use ai-data-science-team single-agent pandas code generators for
  cleaning, wrangling, visualization, and feature engineering workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: ai-data-science-team
  import: ai_data_science_team
  version: 0.0.0.9017
license: MIT
---

# dataframe-code-agents

Use this sub-skill when the task is to run or explain **one ai-data-science-team pandas code-generation agent** over already-loaded pandas data: cleaning, wrangling, Plotly visualization, or feature engineering.

The package agents call the caller-provided LangChain-compatible model when invoked. This operating skill does not provide or configure that model and its bundled inspection script performs no model calls.

## Route first

| User intent | Use here? | Target |
|---|---:|---|
| Load local CSV/Excel/JSON/Parquet/Pickle files, discover files, or summarize a DataFrame without code generation | No | `../data-access-and-eda/SKILL.md` |
| Clean one DataFrame with generated pandas code | Yes | `DataCleaningAgent` |
| Wrangle, join, reshape, aggregate, or transform one or more DataFrames with generated pandas code | Yes | `DataWranglingAgent` |
| Generate a Plotly chart from one DataFrame with generated code | Yes | `DataVisualizationAgent` |
| Produce a model-ready feature table with generic encodings and optional target preservation | Yes | `FeatureEngineeringAgent` |
| Query a SQL database or reason about SQL safety | No | `../sql-analysis/SKILL.md` |
| Compose multiple agents, use analyst teams, supervisors, or Streamlit apps | No | `../multiagent-and-app-workflows/SKILL.md` |
| Train H2O models or inspect MLflow tools | No | `../modeling-and-mlflow/SKILL.md` |

## Minimum runtime assumptions

- `ai_data_science_team` imports successfully in the current Python environment.
- The caller already has data in memory as a pandas `DataFrame`, a dict convertible to a DataFrame, or for wrangling a list of DataFrames/dicts.
- The caller supplies a LangChain-compatible chat model object as `model=llm` before invoking an agent.
- Data loading, EDA-only reporting, SQL access, app launching, model training, and service orchestration are delegated to sibling sub-skills.

## Operating checklist

1. Identify the single-agent task: cleaning, wrangling, visualization, or feature engineering.
2. Verify the data shape is compatible with the selected agent.
3. Choose conservative execution settings:
   - `n_samples` low enough for wide data.
   - `max_retries` bounded, usually `1` to `3`.
   - `log=True` only when the user wants generated code/error files, with a user-selected relative `log_path`.
   - `human_in_the_loop=True` only when a review/resume interaction is acceptable.
4. Invoke through the class wrapper (`DataCleaningAgent`, `DataWranglingAgent`, `DataVisualizationAgent`, or `FeatureEngineeringAgent`) unless the caller specifically needs the lower-level `make_*_agent` graph.
5. Retrieve results through getters or `get_response()`; inspect generated code before reusing it outside the package workflow.
6. If generated code fails, use the returned error key, bounded retries, logs, and the troubleshooting table rather than rerunning blindly.

## Fast reference map

- API signatures, response keys, getters, and shared graph behavior: [`references/api-reference.md`](references/api-reference.md)
- End-to-end cleaning, wrangling, visualization, and feature engineering patterns: [`references/workflows.md`](references/workflows.md)
- Human review, checkpointers, resume commands, and generated-code logging: [`references/human-in-the-loop-and-logging.md`](references/human-in-the-loop-and-logging.md)
- Symptom-based fixes for token pressure, sandbox errors, malformed outputs, and Plotly warnings: [`references/troubleshooting.md`](references/troubleshooting.md)
- Safe import/signature/sandbox probe with no model call: [`scripts/inspect_dataframe_agents.py`](scripts/inspect_dataframe_agents.py)

## Key safety facts

- Generated pandas/Plotly code is executed by the package through a subprocess sandbox with a timeout, a memory limit, and blocked imports for common filesystem, process, and network modules.
- The sandbox is a guardrail, not a proof of correctness. Tell the user to review generated functions, especially before copying them into production notebooks or pipelines.
- The default report node is deterministic: it packages selected state keys into an `AIMessage` without another model explanation call.
- Human-in-the-loop review pauses after code execution when enabled, so use a checkpointer and stable `thread_id` if the run must be resumed.
