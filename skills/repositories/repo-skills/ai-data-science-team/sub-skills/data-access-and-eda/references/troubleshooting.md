# Data access and EDA troubleshooting

Use this guide for symptoms in the data-loader, direct DataFrame summaries, `DataLoaderToolsAgent`, `EDAToolsAgent`, and optional EDA report functions.

## Import and environment symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'IPython'` while importing `ai_data_science_team` or agent classes | The package imports `IPython.display.Markdown`, but `ipython` may not be present in a minimal environment. | Install `ipython` in the active environment, then rerun the import. For CI/smoke checks, verify package import before invoking agents. |
| `ModuleNotFoundError` for `missingno`, `pytimetk`, `sweetviz`, or `dtale` | Optional EDA report dependency is not installed. | Use `describe_dataset` / `get_dataframe_summary` as a fallback, or install only the missing optional dependency needed for the selected report. `dtale` may need a separate install. |
| Import succeeds but agent invocation fails with provider/model errors | `DataLoaderToolsAgent` and `EDAToolsAgent` require a configured LangChain-compatible chat model when invoked. | Confirm the user intended an LLM call, configure the model/provider outside the skill, and retry. For no-LLM workflows, use direct `.func(...)` tool calls instead. |

## File discovery and loading symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `Directory not found` | Directory path is wrong, relative to a different working directory, or not accessible. | Ask for/compute the intended directory, list the parent directory, or use an absolute path supplied by the user. Do not guess across unrelated folders. |
| `File not found ... Try data/<filename>` | The file path did not resolve through the helper's best-effort search. | Use `search_files_by_pattern` to find candidate files, then pass the selected full path to `load_file`. |
| `Multiple matches found; please specify a full path` | The basename exists in more than one searched location. | Present the candidate names/locations at an appropriate level of detail and ask the user which one to load, or use a full path if already known. |
| `Unsupported file extension` | The file is not one of the supported tabular formats. | Convert/export to CSV, Excel, JSON/JSONL/NDJSON, Parquet, or route to a specialized parser outside this sub-skill. For SQL databases, route to `sql-analysis`. |
| A directory load marks files as `skipped` because they are larger than `max_mb` | `load_directory` enforces a file size cap. | Increase `max_mb` only with user approval and resource awareness, or load a selected file with pandas chunking outside this helper. |
| Loaded DataFrame has fewer rows than expected | `max_rows`/`nrows` was set, or `load_directory` defaulted to a capped row count. | State that a sample was loaded. Rerun with a higher cap only when the user wants more rows and memory budget allows. |
| Pickle loading raises a safety error | Pickle deserialization is disabled by default to avoid arbitrary code execution. | Do not bypass this for untrusted data. For trusted data only, the user may set `ALLOW_UNSAFE_PICKLE=1` in the process environment before loading. Prefer non-pickle formats. |
| `pd.read_parquet` fails inside `load_parquet` | A parquet engine such as `pyarrow` or `fastparquet` is missing, or the file is incompatible. | Install the required parquet engine or convert the file to CSV/JSON in a trusted environment. |

## DataFrame summary and EDA symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `TypeError: Input must be a single DataFrame...` from `get_dataframe_summary` | Input is not a pandas DataFrame, list of DataFrames, or dict of DataFrames. | Convert loaded tool artifacts with `pd.DataFrame(...)` before summarizing. |
| Summary is too long for a wide/large table | `n_sample` is high and `skip_stats=False` includes `describe()` and `info()`. | Reduce `n_sample`, set `skip_stats=True`, or summarize selected columns. Route transformation/code requests to `dataframe-code-agents`. |
| `EDAToolsAgent` logs `No data_raw provided` | The wrapper was invoked without a DataFrame. | Pass `data_raw=df` to `invoke_agent` / `invoke_messages`. Direct EDA tool calls should pass `data_raw=df.to_dict()`. |
| `describe_dataset` artifact shape is surprising | The tool flattens `df.describe(include="all")` into `artifact["describe_df"]` with a `stat` column. | Convert with `pd.DataFrame(artifact["describe_df"])` rather than `pd.DataFrame.from_dict(...).T`. |
| `visualize_missing` sampling fails | `n_sample` is larger than the number of rows, or data cannot be plotted. | Use `n_sample=min(len(df), desired_sample)` or fall back to `df.isna().mean()`. |
| Correlation funnel uses a different target level than requested | The requested one-hot target level did not match generated `target__level` columns. | Inspect the returned content for the actual level used; rerun with a valid `target_bin_index` string or integer. |
| Correlation data is present but plot artifacts contain errors | Static/Plotly rendering failed after the correlation calculation. | Use `artifact["correlation_data"]` as the primary result, install/fix plotting dependencies only if plots are required. |

## Agent artifact symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `get_artifacts()` returns `None` or empty output | The agent did not call a tool, the model answered directly, or invocation failed before tool execution. | Check `get_tool_calls()` and `get_internal_messages()`. Prompt the agent to use a specific tool, or call the tool directly with `.func(...)`. |
| The data loader agent loads files when the user only wanted a listing | Prompt ambiguity allowed the model to choose a loading tool. | Re-prompt with “list/search only; do not load file contents,” or use `list_directory_contents` / `search_files_by_pattern` directly. |
| Agent loops or stops due to recursion limit | The model could not settle on a tool sequence or needed more steps. | Tighten the user instruction, specify the exact tool and file/directory, or increase `invoke_react_agent_kwargs={"recursion_limit": ...}` only when appropriate. |
| Tool-call logging exposes local paths in console output | Loader tools naturally report inspected paths. | Avoid copying raw console logs into public reports. Summarize filenames or sanitized paths when sharing results. |

## Optional report symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Sweetviz writes a report to an unexpected location | `report_directory` was omitted, so the tool created a default reports directory under the current working directory. | Pass a caller-approved `report_directory` explicitly and keep `open_browser=False` in automation. |
| Sweetviz report generation fails with NumPy warning/attribute issues | Sweetviz compatibility with newer NumPy can be fragile. The tool includes a compatibility patch, but dependency combinations may still fail. | Retry in an environment with compatible Sweetviz/NumPy versions, or use `describe_dataset` plus missingness/correlation summaries. |
| D-Tale fails with port already in use | The default port is occupied. | Choose another high local port and ensure the user approves starting a service. |
| D-Tale or browser opening is not acceptable in CI/non-interactive runs | D-Tale launches a local service; browser opening is interactive. | Do not run D-Tale. Use direct summaries or a file-based Sweetviz report if writes are approved. |

## Safe fallback checklist

When a data-access/EDA workflow fails and the user did not request optional reports or LLM calls:

1. List/search the directory instead of loading everything.
2. Load one selected non-pickle tabular file with `load_file.func(...)` or `auto_load_file(...)`.
3. Convert the artifact to pandas.
4. Run `get_dataframe_summary(..., n_sample=5, skip_stats=True)`.
5. Run `describe_dataset.func(data_raw=df.to_dict())` only if structured statistics are still needed.
6. Report exact skipped optional capabilities and what dependency or approval would be needed.
