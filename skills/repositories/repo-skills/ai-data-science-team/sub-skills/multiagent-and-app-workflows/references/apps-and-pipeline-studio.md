# Streamlit Apps And AI Pipeline Studio

The package includes Streamlit app patterns that wrap the same agents documented in this skill. Treat apps as interactive services: they can keep session state, call an LLM provider during chat, open UI ports, and write project or cache files when persistence is enabled. Do not launch an app unless the user asks for an interactive session.

## Safe App Launch Planning

Use this order before any app launch:

1. Verify the Python environment imports `ai_data_science_team` and `streamlit`.
2. Ask which app file to launch if the caller has not provided one. This skill intentionally does not point to repository app paths.
3. Confirm the working directory where the app may create temporary files, saved projects, caches, plots, logs, or MLflow artifacts.
4. Confirm the LLM provider is configured outside this skill.
5. Launch with a placeholder path supplied by the user or host environment:

```bash
python -m streamlit run <app_file.py>
```

Use the bundled API inspection script for a no-service check:

```bash
python scripts/inspect_multiagent_api.py --format json
```

## App Catalog

| App pattern | Primary agent(s) | User-facing purpose | Notes |
| --- | --- | --- | --- |
| Pandas Data Analyst app | `PandasDataAnalyst`, `DataWranglingAgent`, `DataVisualizationAgent` | Upload CSV/Excel, ask natural-language questions, return a table or Plotly chart. | Stores generated tables/charts in Streamlit session state and uses chat history. |
| SQL Database app | `SQLDatabaseAgent` | Connect to a configured SQLAlchemy database and ask natural-language database questions. | Displays generated SQL and result tables. Detailed SQL safety belongs to `../sql-analysis/SKILL.md`. |
| Exploratory Copilot app | `EDAToolsAgent` | Upload or select data, run EDA-style questions, display reports, charts, and summaries. | Optional report renderers may require extra packages; see `../data-access-and-eda/SKILL.md`. |
| AI Pipeline Studio | `make_supervisor_ds_team` plus all worker agents | Pipeline-first workspace for loading, cleaning, EDA, visualization, feature engineering, model/evaluation, MLflow, and project saves. | Most complex app; see the Pipeline Studio sections below. Optional H2O/MLflow details belong to `../modeling-and-mlflow/SKILL.md`. |

## Pandas Data Analyst App Pattern

Core flow:

1. Configure model provider and model name in the sidebar.
2. Upload a CSV or Excel file.
3. Create a `PandasDataAnalyst` with `DataWranglingAgent` and `DataVisualizationAgent`.
4. On chat input, invoke the analyst with the current DataFrame.
5. If `routing_preprocessor_decision == "chart"` and a Plotly graph is returned, show the chart.
6. Otherwise, show the wrangled table.

Implementation cues:

- The app stores chart/table references in Streamlit session state so chat history can re-render them.
- It uses higher `n_samples` on component agents than many notebook examples; lower this for very wide data.
- If charting fails, return the table fallback and inspect `plotly_error`.

## SQL Database App Pattern

Core flow:

1. Pick a named SQLAlchemy database URL from app configuration.
2. Create an engine/connection and a `SQLDatabaseAgent`.
3. On chat input, invoke the SQL agent.
4. Display generated SQL and the returned table.

Implementation cues:

- Use a fresh or safely reused SQL connection appropriate for the UI runtime.
- The app pattern is direct SQL-agent usage, not `SQLDataAnalyst`; add `SQLDataAnalyst` only when the app also needs chart routing.
- Treat unsafe SQL, schema size, and metadata sampling as `sql-analysis` concerns.

## Exploratory Copilot App Pattern

Core flow:

1. Upload/select a dataset.
2. Create an `EDAToolsAgent`.
3. On chat input, run EDA-related tool calls.
4. Render summaries, Plotly objects, matplotlib images, and HTML reports when available.

Implementation cues:

- Optional EDA report libraries are not part of the minimum verified environment.
- If a requested report renderer is missing, fall back to basic describe/correlation/missingness guidance and route optional dependency details to `data-access-and-eda`.

## AI Pipeline Studio: Mental Model

AI Pipeline Studio is a supervisor-team app centered around a visual pipeline and dataset lineage rather than one-off chat results.

Major concepts:

- **Supervisor team**: built with `make_supervisor_ds_team`, `WorkflowPlannerAgent`, data loader, wrangling, cleaning, EDA, visualization, SQL, feature engineering, H2O, MLflow, and evaluation agents.
- **Dataset registry**: tracks loaded and derived datasets, active dataset, stage, label, shape, provenance, and lineage.
- **Pipeline nodes**: represent raw, SQL, wrangled, cleaned, feature-engineered, visualization, model, evaluation, MLflow, manual, edited, and project-derived steps.
- **Chat-to-pipeline context**: optional sidebar controls append selected pipeline context and sometimes selected code snippets to chat prompts.
- **Manual plus AI nodes**: users can add nodes, edit generated code drafts, run drafts locally, compare nodes, hide/delete subgraphs, and inspect node metadata.
- **Project saves**: users can save metadata-only lineage or full-data snapshots, then load/relink/rehydrate later.
- **Dataset cache**: opt-in persistence stores datasets with pruning by max item count and max size.

## AI Pipeline Studio Controls

| Control area | What it changes | Operational impact |
| --- | --- | --- |
| LLM provider/model | Chooses OpenAI or Ollama style providers and model names. | Chat and agent calls depend on provider availability. |
| Short-term memory | Adds/removes a checkpointer for multi-turn context. | Enables stateful follow-up but can preserve stale context. |
| Proactive workflow mode | Allows broad requests to become multi-step plans. | May ask clarifying questions or run more steps than a narrow prompt. |
| LLM intent parsing | Uses an additional model call to classify intent. | Better ambiguous routing, higher latency/cost. |
| Data upload/sample | Creates initial raw dataset. | Updates active dataset and pipeline root nodes. |
| Active dataset override | Forces downstream steps to use a selected dataset. | Prevents the supervisor from choosing the wrong stage. |
| Pipeline persistence | Writes pipeline specs, repro scripts, SQL artifacts, or dataset cache files when enabled. | Useful for reproducibility; confirm the working directory first. |
| Chat-to-pipeline context | Sends selected node metadata/code context to the supervisor. | Good for targeted edits; can confuse unrelated prompts. |
| SQL options | Provides a SQLAlchemy URL for SQL workflows. | Connection failures should route to `sql-analysis`. |
| MLflow options | Controls tracking URI, artifact root, experiment, and logging in training. | Optional; route detailed failures to `modeling-and-mlflow`. |
| Debug options | Shows progress and logs in the app UI/terminal. | Use for diagnosing worker failures and missing artifacts. |

## Project Save Modes

| Mode | What is saved | Use when | Caveat |
| --- | --- | --- | --- |
| Metadata-only | Pipeline lineage, node metadata, transform descriptions, and source references. | You want a small project save and can rehydrate from original sources. | Rehydrate can fail if original sources moved or transforms depend on unavailable context. |
| Full-data | Metadata plus dataset snapshots, preferring Parquet and falling back to pickle. | You need reliable reload without re-running sources. | Larger storage footprint; never load project files from untrusted origins. |

Recommended guidance:

- Use metadata-only for routine handoff when the data source remains stable.
- Use full-data for short-lived local analysis sessions where reload reliability matters more than storage size.
- Convert full-data to metadata-only when project size becomes a problem.
- Keep dataset cache off unless the user needs session recovery or cross-session node inspection.

## AI Pipeline Studio Prompting Patterns

Good prompts:

- "Load the sample churn data and summarize churn rate."
- "Using the cleaned dataset, plot churn rate by contract."
- "Use the selected pipeline node and create a feature-engineered dataset for target Churn."
- "Compare this cleaned node with the raw node by missingness and changed columns."
- "Save this project metadata-only."

Avoid ambiguous prompts:

- "Run everything" without a target variable when modeling/evaluation is expected.
- "Model by product model" when the word "model" means a product attribute; clarify whether the user wants ML training.
- "Use that data" when the app has multiple pipeline nodes; select or name the active dataset first.

## App Troubleshooting Entry Points

- If app import fails before UI renders, run `scripts/inspect_multiagent_api.py` and read `references/troubleshooting.md`.
- If a provider or Ollama connection fails, fix provider configuration outside the skill, then rerun the app.
- If a Pipeline Studio node has the wrong parent or active dataset, set the active dataset override or select the intended node before chatting.
- If H2O, MLflow, optional EDA reports, or UI service behavior is involved, route to the owning sibling sub-skill for details.
