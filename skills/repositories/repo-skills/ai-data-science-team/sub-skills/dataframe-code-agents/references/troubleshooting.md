# Troubleshooting dataframe code agents

Use this table after selecting the correct single-agent workflow. For file-loading, SQL, app, model-training, or multiagent failures, route to the owning sibling sub-skill first.

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| Import fails for `ai_data_science_team` or a core dependency. | The package or its base dependencies are not installed in the active Python environment. | Run the parent environment check if available, then install the base package dependencies. Do not continue to agent invocation until imports pass. |
| Agent construction succeeds, but invocation fails immediately when the model is called. | The caller-supplied `model` object is missing, incompatible, or cannot complete chat invocations. | Confirm the object supports LangChain-style invocation. Use the bundled inspection script to separate package import problems from model-client problems. |
| The run fails with model context/token length errors. | The DataFrame is wide, contains long string columns, or `n_samples` is too high. | Lower `n_samples`; preselect relevant columns; sample rows before invocation; ask for a narrower task; use EDA-only summaries from `../../data-access-and-eda/SKILL.md` before code generation. |
| Getter returns `None` and `agent.response` is empty. | The agent was not invoked, failed before storing response, or is paused at a human-review interrupt. | Inspect `agent.response`; if human review is enabled, call `agent.get_state(config=...)` with the same `thread_id` and resume or disable human review for unattended runs. |
| `get_response()` raises because `response` is `None`. | The inherited `BaseAgent.get_response()` expects a populated response dict. | Call `invoke_agent(...)` first. For failed construction/invocation, inspect the raised exception rather than calling getters. |
| Error contains `Import of 'os' is blocked`, `Import of 'subprocess' is blocked`, or another blocked import. | Generated code attempted filesystem, process, network, or other disallowed operations in the sandbox. | Add explicit instructions: return an in-memory DataFrame or Plotly dict only; do not read/write files; do not call external services. Rerun with bounded retries. |
| Error says `Sandbox timed out after ... seconds`. | Generated code is too slow, loops unexpectedly, or processes too much data in the sandbox. | Reduce rows/columns, simplify instructions, lower requested operations, or pre-aggregate with wrangling before visualization/feature engineering. |
| Error says `Sandbox exited with code ...` or `Sandbox returned non-JSON output`. | Generated code crashed the child process or returned output that cannot be serialized. | Inspect the generated function; require a simple pandas DataFrame or Plotly figure dict return; rerun with clearer return instructions. |
| Cleaning output is missing or `data_cleaner_error` says output is not a valid table. | The generated cleaning function returned the wrong type or failed after sandbox execution. | Inspect `data_cleaner_function`; clarify that `data_cleaner(data_raw)` must return one pandas DataFrame; set `max_retries` to a small positive value. |
| Cleaning drops important columns or too many rows. | Default cleaning steps can remove high-missing columns, duplicates, remaining missing rows, or extreme outliers unless instructed otherwise. | Add preservation constraints: name columns that must remain, ask to impute rather than drop, or ask not to remove outliers. |
| Wrangling raises a list/dict/DataFrame input error. | `DataWranglingAgent` accepts DataFrame, dict, list of DataFrames, or list of dicts; another type was supplied. | Convert inputs before invocation. For multiple datasets, pass `[df1, df2, ...]` and state the desired join keys/output grain. |
| Wrangling creates too many rows after a merge. | Join keys were ambiguous or the generated code produced a many-to-many/Cartesian join. | Explicitly name join keys, expected row grain, duplicate-key handling, and aggregation rules. Inspect `data_wrangling_summary` for row-count changes. |
| Wrangling returns multiple tables or a list. | The generated function did not follow the single-output contract. | Tell the agent to return one pandas DataFrame only. If a list was returned, the package may concatenate it, but that is only a fallback. |
| Visualization error says Plotly reconstruction failed or the figure could not be reconstructed. | Generated code did not return a JSON-serializable Plotly figure dict. | Instruct the agent to build a Plotly figure, serialize it with `plotly.io.to_json`, parse with `json.loads`, and return the dict. |
| Visualization returns a fallback chart instead of the requested chart. | Generated code failed validation, so the package used a simple detected-column fallback. | Inspect `data_visualization_warning` and `data_visualization_function`; specify chart type, x/y columns, grouping, and aggregation. |
| `data_visualization_warning` reports chart type mismatch. | The requested chart type was explicit but reconstructed traces do not match it. | Restate the required chart type and columns. For line charts, specify that the trace mode must contain lines; for box/violin charts, name the category and numeric axes. |
| Visualization fails due to missing or misspelled columns. | The model selected column names that differ from the actual DataFrame schema. | Include exact column names in user instructions. The package may auto-substitute close matches, but explicit schema terms are more reliable. |
| Feature engineering error says the target column is missing from engineered output. | `target_variable` was provided, but generated code dropped or renamed it. | Pass the exact target name and state that it must be preserved in the returned DataFrame. If the target should be encoded, require the same column name unless the user requests otherwise. |
| Feature engineering creates too many one-hot columns. | High-cardinality categoricals were not bucketed before encoding. | Add a threshold instruction, such as bucket categories below 5% frequency to `Other` and avoid one-hot encoding ID-like columns. |
| Feature engineering invents domain-specific features. | User instructions were broad and the model inferred transformations. | Ask for only generic transformations: type conversion, imputation, high-cardinality bucketing, one-hot encoding, booleans, datetime parts, and target preservation. |
| Human review never resumes or resumes the wrong run. | The resume command used a different `thread_id` or checkpointer state was lost. | Use the same `config={"configurable": {"thread_id": ...}}` for invoke, state inspection, and `Command(resume=...)`. Keep the checkpointer object alive. |
| Human review accepts with `yes` but no final report appears. | `bypass_explain_code=True` routes accepted review directly to graph end. | If a report in `messages` is needed, construct the agent with `bypass_explain_code=False`. |
| Generated function path keys are `None`. | Logging is disabled or no generated function was written. | Set `log=True` and a caller-selected `log_path`, or use the in-memory getter such as `get_data_cleaner_function()`. |
| Logs overwrite previous generated functions. | `overwrite=True` is the default. | Set `overwrite=False` to create unique generated function file names. |
| Repeated repair attempts fail with similar errors. | The prompt/data contract is underspecified or generated code violates sandbox/return constraints. | Stop increasing retries. Reduce the task, sample data, add exact schema/return constraints, or split cleaning/wrangling/visualization/feature engineering into separate runs. |

## Quick no-model health check

From this sub-skill directory, run:

```bash
python scripts/inspect_dataframe_agents.py --json
```

This verifies imports, public signatures, expected methods, `DataWranglingAgent` input conversion, and a tiny pandas sandbox execution. It does not invoke any package agent or model.

## Retry discipline

Use retries to recover from simple generated-code mistakes, not as an unbounded loop.

Recommended defaults:

- `max_retries=1` for fast exploratory work.
- `max_retries=2` or `3` when the user explicitly wants generated-code repair attempts.
- `retry_count=0` for a new run.

If the same symptom repeats, change the data contract or instructions before trying again.
