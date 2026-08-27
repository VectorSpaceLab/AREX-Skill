# Data access and EDA API reference

This reference covers the data-loader, DataFrame summary, EDA tools, and tool-calling agents owned by `data-access-and-eda`. For end-to-end recipes, see [workflows.md](workflows.md). For optional report dependencies, see [optional-eda-reports.md](optional-eda-reports.md).

## Import map

```python
import pandas as pd

from ai_data_science_team.tools.data_loader import (
    auto_load_file,
    load_csv,
    load_excel,
    load_json,
    load_parquet,
    load_pickle,
    resolve_existing_file_path,
    load_file,
    load_directory,
    list_directory_contents,
    list_directory_recursive,
    get_file_info,
    search_files_by_pattern,
)
from ai_data_science_team.tools.dataframe import get_dataframe_summary
from ai_data_science_team.tools.eda import (
    explain_data,
    describe_dataset,
    visualize_missing,
    generate_correlation_funnel,
    generate_sweetviz_report,
    generate_dtale_report,
)
from ai_data_science_team.agents import DataLoaderToolsAgent
from ai_data_science_team.ds_agents import EDAToolsAgent
```

The decorated data-loader and EDA tools are LangChain `StructuredTool` objects. In ordinary Python code, call their underlying functions with `.func(...)` for deterministic, no-agent execution. In LangChain tool execution, pass tool inputs with `.invoke({...})`. The smoke script uses `.func(...)` so it does not call an LLM.

## Data-loader tool functions

| API | Direct call pattern | Purpose | Important return shape / notes |
| --- | --- | --- | --- |
| `load_file` | `content, artifact = load_file.func(file_path="data.csv")` | Load one recognized tabular file. | `artifact` includes `status`, `data`, `error`, and `file_path`. Convert successful data with `pd.DataFrame(artifact["data"])`. |
| `load_directory` | `content, artifact = load_directory.func(directory_path="data", file_type="csv", max_mb=20, max_rows=5000)` | Load recognized tabular files directly inside one directory. | `artifact` is keyed by filename; each value includes `status`, `data`, and `error`. Skips directories and files over `max_mb`. |
| `list_directory_contents` | `content, artifact = list_directory_contents.func(directory_path="data", show_hidden=False)` | Non-recursive directory listing. | `content` is display-oriented; `artifact` is a list of `{filename, type}` dictionaries. |
| `list_directory_recursive` | `content, artifact = list_directory_recursive.func(directory_path="data", show_hidden=False, max_depth=5, max_entries=1000)` | Bounded recursive tree. | Stops at `max_depth` / `max_entries`; artifacts include file/directory records. |
| `get_file_info` | `content, artifact = get_file_info.func(file_path="data.csv")` | Inspect size and modification metadata for one file. | Returns a one-row artifact list. Useful before loading large files. |
| `search_files_by_pattern` | `content, artifact = search_files_by_pattern.func(directory_path="data", pattern="*.csv", recursive=True)` | Find files by wildcard pattern. | `artifact` is a list of `{file_path}` records. Prefer this for extension-filtered discovery. |

Supported tabular formats: `.csv`, `.csv.gz`, `.tsv`, `.xlsx`, `.xls`, `.json`, `.jsonl`, `.ndjson`, `.parquet`, and `.pkl` when pickle loading is explicitly enabled for trusted files.

### Lower-level loaders

| API | Signature | Use when |
| --- | --- | --- |
| `resolve_existing_file_path` | `(file_path: str) -> tuple[pathlib.Path | None, list[str]]` | You need to diagnose path resolution before loading. It tries the given path, common project data/temp locations, and a shallow basename search. |
| `auto_load_file` | `(file_path: str, max_rows: Optional[int] = None) -> pandas.DataFrame` | You want extension-based loading without LangChain tool wrapping. On failure it returns an error string rather than raising for common file resolution problems. |
| `load_csv` | `(file_path: str, sep: str = ',', nrows: Optional[int] = None) -> pandas.DataFrame` | You already know the file is CSV/TSV and want pandas options exposed by this helper. |
| `load_excel` | `(file_path: str, sheet_name=None, nrows: Optional[int] = None) -> pandas.DataFrame` | You already know the file is Excel. |
| `load_json` | `(file_path: str, lines: bool = False, nrows: Optional[int] = None) -> pandas.DataFrame` | You already know whether JSON is records or line-delimited records. |
| `load_parquet` | `(file_path: str, max_rows: Optional[int] = None) -> pandas.DataFrame` | You already know the file is Parquet. It reads the file then truncates with `head(max_rows)`. |
| `load_pickle` | `(file_path: str) -> pandas.DataFrame` | Only for trusted pickle files after explicit `ALLOW_UNSAFE_PICKLE` opt-in; otherwise it raises a safety error. |

## DataFrame summaries

| API | Signature | Output |
| --- | --- | --- |
| `get_dataframe_summary` | `(dataframes: pandas.DataFrame | list[pandas.DataFrame] | dict[str, pandas.DataFrame], n_sample: int = 30, skip_stats: bool = False) -> list[str]` | One text summary per input DataFrame, including shape, dtypes, missing percentages, unique counts, sample rows, and optionally `describe()` / `info()`. |

Use `skip_stats=True` for very wide, mixed-type, or sensitive DataFrames when a lightweight structure/sample summary is enough. Dictionary-valued cells are converted to strings before unique-count calculation to avoid unhashable-value failures.

## EDA tools

All EDA tools receive `data_raw` as a dictionary, normally `df.to_dict()`. For direct calls, use `.func(data_raw=df.to_dict(), ...)`.

| Tool | Direct call pattern | Purpose | Artifact / caveat |
| --- | --- | --- | --- |
| `explain_data` | `summary = explain_data.func(data_raw=df.to_dict(), n_sample=30, skip_stats=False)` | Narrative DataFrame overview using `get_dataframe_summary`. | Returns content only. The implementation returns the summary list from the helper. |
| `describe_dataset` | `content, artifact = describe_dataset.func(data_raw=df.to_dict())` | Concise pandas `describe(include="all")` snapshot. | `artifact["describe_df"]` is a flattened dictionary with a `stat` column plus original columns. |
| `visualize_missing` | `content, artifact = visualize_missing.func(data_raw=df.to_dict(), n_sample=500)` | Missingness matrix, bar plot, and heatmap. | Requires `missingno`; artifact has `matrix_plot`, `bar_plot`, `heatmap_plot` base64 PNG strings. |
| `generate_correlation_funnel` | `content, artifact = generate_correlation_funnel.func(data_raw=df.to_dict(), target="Churn", target_bin_index="Yes")` | Binarize features and compute correlation funnel against a target level. | Requires `pytimetk` and plotting deps; artifact has `correlation_data`, `plot_image`, and `plotly_figure`. Plot keys may contain error dictionaries if plotting fails. |
| `generate_sweetviz_report` | `content, artifact = generate_sweetviz_report.func(data_raw=df.to_dict(), target=None, report_directory="reports", open_browser=False, include_html=False)` | Generate a Sweetviz HTML report. | Requires `sweetviz`; writes an HTML file. Keep `open_browser=False` in automation. |
| `generate_dtale_report` | `content, artifact = generate_dtale_report.func(data_raw=df.to_dict(), host="localhost", port=40000, open_browser=False)` | Launch a D-Tale interactive exploration server. | Requires `dtale`; starts a local service and should be explicitly approved. |

## Tool-calling agents

| Class / factory | Verified public signature | When to use |
| --- | --- | --- |
| `DataLoaderToolsAgent` | `(self, model: Any, create_react_agent_kwargs: Optional[Dict] = {}, invoke_react_agent_kwargs: Optional[Dict] = {}, checkpointer: Checkpointer | None = None, log_tool_calls: bool = True)` | Let a model choose among file listing, search, metadata, file load, and directory load tools. |
| `make_data_loader_tools_agent` | `make_data_loader_tools_agent(model, create_react_agent_kwargs={}, invoke_react_agent_kwargs={}, checkpointer=None, log_tool_calls=True)` | Build the compiled LangGraph/LangChain graph directly instead of using the OO wrapper. |
| `EDAToolsAgent` | `(self, model: Any, create_react_agent_kwargs: Optional[Dict] = {}, invoke_react_agent_kwargs: Optional[Dict] = {}, checkpointer: Checkpointer | None = None, log_tool_calls: bool = True)` | Let a model choose among EDA explanation, describe, missingness, correlation, and optional report tools. |
| `make_eda_tools_agent` | `make_eda_tools_agent(model, create_react_agent_kwargs={}, invoke_react_agent_kwargs={}, checkpointer=None, log_tool_calls=True)` | Build the compiled EDA graph directly instead of using the OO wrapper. |

Common wrapper methods on both agent classes:

- `invoke_agent(user_instructions=..., **kwargs)` / `ainvoke_agent(...)`: execute the compiled graph. EDA variants accept `data_raw=<DataFrame>`.
- `invoke_messages(messages, **kwargs)` / `ainvoke_messages(...)`: execute using an explicit message list.
- `get_ai_message(markdown=False)`: return the final AI message or Markdown display object.
- `get_artifacts(as_dataframe=False)`: return captured tool artifacts; with `as_dataframe=True`, attempts convenient pandas conversion.
- `get_internal_messages(markdown=False)`: inspect graph-internal messages.
- `get_tool_calls()`: list tool calls detected in the response.

Agent invocation can call an external or local model through the supplied `model`. Do not instantiate or invoke these agents for smoke checks unless the caller has intentionally configured a model/provider.
