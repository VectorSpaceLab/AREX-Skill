# Cross-cutting troubleshooting

Read this when imports, model-provider setup, optional dependencies, services, generated code, or app workflows fail before a task reaches a specific sub-skill.

## Import and installation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: ai_data_science_team` | Package is not installed in the active Python. | Install `ai-data-science-team`, or install the checkout in editable mode when working on the package. Run `python -c "import ai_data_science_team"` before invoking agents. |
| `ModuleNotFoundError: IPython` while importing agent classes | The source imports `IPython.display`, but package metadata may not declare `ipython`. | Install `ipython` in the same environment. This is needed for imports even outside notebooks. |
| LangChain/LangGraph import errors | Base dependencies are missing or version-incompatible. | Reinstall the base package in a clean environment, then run `python -m pip check` and root `scripts/check_env.py`. |
| Optional report/model errors such as `No module named missingno`, `No module named pytimetk`, `No module named sweetviz`, `No module named dtale`, `No module named h2o`, or `No module named mlflow` | Optional workflow dependency is not installed. | Install only the needed extra/package: `ai-data-science-team[data_science]`, `dtale`, or `ai-data-science-team[machine_learning]`. Do not install all extras unless the task needs all optional surfaces. |

## Model-provider and credential failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Agent invocation fails before producing code or tool calls with provider authentication errors | OpenAI key or equivalent provider credentials are missing/invalid. | Ask the user to configure credentials or pass a local model. Do not embed keys in scripts or skill files. |
| Ollama model invocation fails with connection refused or missing model | Ollama daemon is not running or the requested model has not been pulled. | Ask the user to start Ollama and make the model available before invoking the package. |
| Tool-calling agents loop or hit recursion limits | Tool-calling prompt is ambiguous or `invoke_react_agent_kwargs` recursion limit is too small. | Narrow the user instruction, ask for file paths/schemas, and set an appropriate recursion limit for the task. |

## Generated-code agents

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Wide/large DataFrame causes token-limit errors | Too many columns/rows are summarized for the model. | Reduce `n_samples`, summarize or select relevant columns first, or split the task into smaller transformations. |
| Generated code fails on execution | Model emitted invalid Python, used unavailable columns, or hit a sandbox/runtime limit. | Keep `max_retries` > 0, inspect the logged/generated function, validate columns/dtypes, and rerun on a tiny fixture before production data. |
| Getter returns `None` after an invocation | The graph did not reach the expected node, failed, or the wrong getter is being used for the agent type. | Inspect `agent.response` keys and read the owning sub-skill API reference for the expected getter. |
| Human-in-the-loop resume does not continue | Missing checkpointer/thread config or resume command sent to the wrong graph state. | Use the code-agent human-in-the-loop reference and preserve the LangGraph `configurable.thread_id` between interrupt and resume. |

## SQL safety and database issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Non-SELECT SQL is rejected | `SQLDatabaseAgent` defaults to `safe_mode=True`. | Keep safe mode for analysis tasks; rewrite the user request as read-only `SELECT`. Disable safe mode only with explicit authorization and database-level protections. |
| Valid-looking query rejected because a blocked keyword appears in text | `_validate_sql` is conservative string validation, not a full parser. | Inspect the SQL; if it is genuinely read-only, adjust aliases/comments or use a proper SQL parser/sandbox outside the package. |
| Database metadata prompt is too long | Large schema or many sample values. | Reduce `n_samples`, enable schema pruning, or query a narrowed schema/table set. |

## Optional ML, EDA report, and app services

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| H2O AutoML does not start | `h2o` extra missing, Java/H2O runtime unavailable, or runtime memory is insufficient. | Run the modeling optional import checker, install `machine_learning`, and keep `max_runtime_secs`/`max_models` small for smoke tasks. |
| MLflow tools cannot find runs/artifacts/models | Tracking URI, experiment, run id, artifact path, or registry backend is wrong. | Use read-only search/list tools first. Only transition registry stages after explicit user approval. |
| Sweetviz, D-Tale, or correlation-funnel report fails | Optional package missing, browser/service not approved, NumPy/pandas compatibility issue, or target column mismatch. | Use basic `describe_dataset` as fallback; then install/report optional dependency only when the user wants that report. |
| Streamlit app launch blocks the session | Apps are long-running UI services and may require credentials/session state. | Do not launch apps unless requested. If requested, clarify model/provider, port, and whether the service should remain running. |

## Verification path

1. Run root `scripts/check_env.py --json` to confirm package import and optional dependency visibility.
2. Run the owning sub-skill smoke/inspection script for deterministic helper tasks.
3. Avoid LLM calls, training, browser/UI launch, or database mutations unless the user explicitly asks for those side effects.
4. If a problem is specific to a workflow, switch to the nearest sub-skill troubleshooting reference.
