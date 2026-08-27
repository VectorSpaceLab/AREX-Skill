---
name: data-access-and-eda
description: "Use ai-data-science-team data/file loading helpers, direct
  DataFrame summaries, DataLoaderToolsAgent, EDAToolsAgent, and optional EDA
  report tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-access-and-eda

Use this sub-skill when the task is about discovering local data files, loading tabular files, summarizing DataFrames, or using the package's tool-calling data loader / EDA agents.

## Best-fit tasks

- List, search, or inspect files and folders before analysis.
- Load CSV, TSV, Excel, JSON/JSONL/NDJSON, Parquet, or explicitly trusted pickle files into pandas.
- Summarize one or more pandas DataFrames without asking an LLM to write pandas code.
- Use `DataLoaderToolsAgent` to let a chat model choose data-loader tools.
- Use `EDAToolsAgent` for explain/describe/missingness/correlation/report tool selection.
- Decide whether optional EDA report tooling is appropriate for a safe, bounded run.

## Route away from this sub-skill

- Cleaning, wrangling, feature engineering, or visualization code generation: use `dataframe-code-agents`.
- SQL database metadata, query generation, or SQL safety: use `sql-analysis`.
- Streamlit apps, Pipeline Studio, supervisor workflows, or multi-agent orchestration: use `multiagent-and-app-workflows`.
- H2O AutoML, model evaluation, MLflow tools, or ML service troubleshooting: use `modeling-and-mlflow`.

## Fast operating path

1. For deterministic data loading and summaries, prefer direct tool functions and DataFrame helpers from [references/api-reference.md](references/api-reference.md).
2. For user-facing file discovery or EDA requests that genuinely need model-based tool selection, use the agent workflows in [references/workflows.md](references/workflows.md). These require a LangChain-compatible model and may call that model when invoked.
3. Treat optional EDA report tools as opt-in. Check [references/optional-eda-reports.md](references/optional-eda-reports.md) before using `missingno`, `pytimetk`, `sweetviz`, or `dtale` features.
4. If a symptom appears, use [references/troubleshooting.md](references/troubleshooting.md) before retrying.
5. For a no-network, no-LLM smoke check, run [`scripts/smoke_data_access.py`](scripts/smoke_data_access.py) in the target Python environment.

## Safety defaults

- Do not call external LLM providers unless the user explicitly provides a model configuration and expects agent invocation.
- Use listing/search tools before loading file contents when the user only asks what files exist.
- Do not load pickle files from untrusted sources. Pickle loading is disabled by default and requires an explicit `ALLOW_UNSAFE_PICKLE` opt-in in the process environment.
- Use small sample sizes for summaries of wide or large DataFrames.
- Optional report tools may write HTML files or launch local services; get explicit approval before browser, service, or long-running report workflows.
