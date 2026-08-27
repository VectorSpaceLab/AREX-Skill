---
name: ai-data-science-team
description: "Operate the ai-data-science-team package for AI-assisted data
  loading, EDA, pandas transformations, SQL analysis, H2O/MLflow modeling,
  multi-agent teams, and Streamlit app workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AI Data Science Team repo skill

Use this repo skill when a task names `ai-data-science-team`, `ai_data_science_team`, AI Data Science Team, AI Pipeline Studio, or asks for AI-assisted data-science agents that load data, clean/wrangle/visualize DataFrames, query SQL databases, run H2O AutoML/MLflow tools, or compose data-science agent teams.

This skill is self-contained: read the bundled references and scripts here instead of reopening the original repository checkout, notebooks, or app source.

## Quick package context

- Distribution name: `ai-data-science-team`.
- Import package: `ai_data_science_team`.
- Verified version baseline: `0.0.0.9017`.
- Public install floor from package metadata: Python 3.9+; Python 3.10+ is recommended for app workflows.
- Common LLM backends: OpenAI chat models through `langchain_openai.ChatOpenAI`, or local Ollama models through `langchain_ollama.ChatOllama` when an Ollama service/model is available.
- Optional extras: `machine_learning` installs `h2o` and `mlflow`; `data_science` installs `pytimetk`, `missingno`, and `sweetviz`; D-Tale report support needs `dtale` separately.

Minimal import check:

```python
from ai_data_science_team import DataCleaningAgent, SQLDatabaseAgent, PandasDataAnalyst
```

If that import fails with `ModuleNotFoundError: IPython`, install `ipython`; the source imports `IPython.display` but the package metadata may not declare it.

## Route by task

| Task signal | Read |
| --- | --- |
| Discover files, load CSV/Excel/JSON/Parquet, summarize DataFrames, use file tools, run basic EDA summaries, or opt into Sweetviz/D-Tale/missingno/correlation-funnel reports | [`sub-skills/data-access-and-eda/SKILL.md`](sub-skills/data-access-and-eda/SKILL.md) |
| Use `DataCleaningAgent`, `DataWranglingAgent`, `DataVisualizationAgent`, or `FeatureEngineeringAgent`; retrieve generated code/functions; handle retries/logs/human review | [`sub-skills/dataframe-code-agents/SKILL.md`](sub-skills/dataframe-code-agents/SKILL.md) |
| Query SQL databases, inspect database metadata, protect read-only SQL, use `SQLDatabaseAgent`, or troubleshoot schema/token pressure | [`sub-skills/sql-analysis/SKILL.md`](sub-skills/sql-analysis/SKILL.md) |
| Train or inspect H2O AutoML workflows, evaluate models, manage MLflow experiments/runs/artifacts/UI/registry, or check optional ML dependencies | [`sub-skills/modeling-and-mlflow/SKILL.md`](sub-skills/modeling-and-mlflow/SKILL.md) |
| Compose agents with `PandasDataAnalyst`, `SQLDataAnalyst`, `SupervisorDSTeam`, `WorkflowPlannerAgent`, or understand AI Pipeline Studio / Streamlit app patterns | [`sub-skills/multiagent-and-app-workflows/SKILL.md`](sub-skills/multiagent-and-app-workflows/SKILL.md) |

## First actions for future agents

1. Identify whether the user wants deterministic helper functions, LLM-backed agents, optional report/model services, or Streamlit apps.
2. Check installed prerequisites before invoking agents. Use [`scripts/check_env.py`](scripts/check_env.py) for package import/signature and optional dependency visibility.
3. For deterministic data/SQL helper tasks, prefer bundled smoke scripts from the owning sub-skill before any LLM call.
4. For LLM-backed agents, confirm the user has configured a LangChain-compatible model object and any provider credentials/service.
5. For optional H2O/MLflow/EDA reports or app workflows, read the owning troubleshooting reference before installing extras, launching services, or starting long-running training/UI processes.

## Shared references and helpers

- [`references/package-overview.md`](references/package-overview.md) explains package modules, public objects, optional dependency groups, and common response/getter patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install/import, model-provider, optional dependency, service, generated-code, and app issues.
- [`references/repo-provenance.md`](references/repo-provenance.md) records the source baseline used to create this skill; read it before deciding whether to refresh the skill.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) is structured metadata for managed repo-skill routing.
- [`scripts/check_env.py`](scripts/check_env.py) is a safe no-credential environment/import checker.

## Safety and verification boundaries

- Do not run notebook workflows, LLM-backed agents, H2O training, MLflow UI, or Streamlit apps unless the user explicitly wants that side effect and has provided credentials/services/budget.
- Treat generated code from cleaning/wrangling/visualization/feature-engineering agents as code to review, log, and validate on small data before using on production data.
- Keep `SQLDatabaseAgent(safe_mode=True)` unless the user intentionally authorizes non-read-only SQL. The bundled SQL sub-skill describes what the validator does and does not guarantee.
- Optional extras are not required for base imports. Install only the extra needed by the selected workflow, not `all` by default.
- Runtime guidance here must remain independent of the original checkout; if you need an example, use the bundled references/scripts.
