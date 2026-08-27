# Data access and EDA workflows

Use these recipes instead of sending future agents back to source notebooks. They distill the package's demonstrated data loader and EDA usage into self-contained operating patterns.

## 1. Choose direct helpers vs. tool-calling agents

Prefer direct helpers when:

- The task is deterministic: load one file, list files, summarize a DataFrame, or compute `describe()`.
- No model/provider is configured.
- The user needs a smoke check, CI-safe validation, or a reproducible preprocessing step.

Use `DataLoaderToolsAgent` or `EDAToolsAgent` when:

- The user asks in natural language and expects an LLM to decide which tool to call.
- The user has intentionally supplied a LangChain-compatible model.
- Tool-call traces and artifacts are useful to expose back to the user.

Never use this sub-skill for pandas transformation code generation, SQL query generation, app launch orchestration, or ML training; route those tasks to the owning sibling sub-skill.

## 2. Discover files without loading contents

Use listing and search tools before loading when the user asks what files exist.

```python
from ai_data_science_team.tools.data_loader import (
    list_directory_contents,
    list_directory_recursive,
    search_files_by_pattern,
    get_file_info,
)

# Top-level listing.
content, listing = list_directory_contents.func(
    directory_path="data",
    show_hidden=False,
)

# Bounded recursive tree.
tree_text, tree_rows = list_directory_recursive.func(
    directory_path="data",
    show_hidden=False,
    max_depth=3,
    max_entries=200,
)

# Extension-filtered search.
content, matches = search_files_by_pattern.func(
    directory_path="data",
    pattern="*.csv",
    recursive=True,
)

# Inspect one selected file before loading.
content, info_rows = get_file_info.func(file_path=matches[0]["file_path"])
```

Operating notes:

- `search_files_by_pattern` is the best first choice for “find CSV files” or “list only Excel files”.
- `list_directory_recursive` returns absolute paths in its artifact. Avoid pasting sensitive paths into public outputs; summarize names and types when appropriate.
- `get_file_info` does not load file contents and is useful before loading large files.

## 3. Load one file safely

```python
import pandas as pd
from ai_data_science_team.tools.data_loader import load_file, auto_load_file

content, artifact = load_file.func(file_path="data/churn_data.csv")
if artifact["status"] != "ok":
    raise RuntimeError(artifact["error"])

df = pd.DataFrame(artifact["data"])
```

For lower-level code where you want a DataFrame directly:

```python
loaded = auto_load_file("data/churn_data.csv", max_rows=5000)
if isinstance(loaded, str):
    raise RuntimeError(loaded)
df = loaded
```

File resolution behavior:

- Existing absolute or relative paths are used directly.
- Relative basenames are searched in common working directories such as `data`, `temp`, and upload folders.
- If multiple basename matches are found, specify the full path rather than letting the helper guess.

## 4. Load a directory of tabular files

```python
import pandas as pd
from ai_data_science_team.tools.data_loader import load_directory

content, loaded = load_directory.func(
    directory_path="data",
    file_type="csv",
    max_mb=20,
    max_rows=5000,
)

dataframes = {}
for filename, record in loaded.items():
    if record["status"] == "ok":
        dataframes[filename] = pd.DataFrame(record["data"])
    else:
        print(f"Skipped or failed {filename}: {record['error']}")
```

Use a directory load only when the user explicitly asks to load all matching files. For discovery-only requests, list/search instead.

## 5. Summarize DataFrames directly

```python
from ai_data_science_team.tools.dataframe import get_dataframe_summary

summaries = get_dataframe_summary(
    {"churn": df},
    n_sample=10,
    skip_stats=False,
)
print(summaries[0])
```

Use `skip_stats=True` when:

- The DataFrame is very wide.
- `describe()` would be slow or noisy.
- The user only needs shape, dtypes, and sample rows.

## 6. Run basic EDA tools directly

```python
from ai_data_science_team.tools.eda import explain_data, describe_dataset

summary = explain_data.func(
    data_raw=df.to_dict(),
    n_sample=5,
    skip_stats=True,
)

content, artifact = describe_dataset.func(data_raw=df.to_dict())
describe_df = pd.DataFrame(artifact["describe_df"])
```

`describe_dataset` is the safest default EDA tool: it requires only pandas and returns a structured artifact. Use optional report tools only after checking [optional-eda-reports.md](optional-eda-reports.md).

## 7. Use DataLoaderToolsAgent with an intentional model call

```python
from ai_data_science_team.agents import DataLoaderToolsAgent

# Supply a configured LangChain-compatible chat model.
agent = DataLoaderToolsAgent(
    model,
    invoke_react_agent_kwargs={"recursion_limit": 10},
)

agent.invoke_agent("List CSV files in the data folder; do not load file contents.")
message = agent.get_ai_message(markdown=False)
artifacts = agent.get_artifacts(as_dataframe=True)
tool_calls = agent.get_tool_calls()
```

Prompting guidance:

- For listing tasks, say “list/search only; do not load file contents.”
- For file reads, name the specific file.
- For loading all files, say “load all CSV files in this directory” and bound directory scope.
- Use `get_artifacts(as_dataframe=True)` when you want pandas-friendly output.

## 8. Use EDAToolsAgent with an intentional model call

```python
from ai_data_science_team.ds_agents import EDAToolsAgent

agent = EDAToolsAgent(
    model,
    invoke_react_agent_kwargs={"recursion_limit": 10},
)

agent.invoke_agent(
    user_instructions="Describe this dataset with the describe_dataset tool.",
    data_raw=df,
)
message = agent.get_ai_message(markdown=False)
artifacts = agent.get_artifacts(as_dataframe=False)
tool_calls = agent.get_tool_calls()
```

Prompting guidance:

- Ask for `describe_dataset` for a fast, structured statistical snapshot.
- Ask for `explain_data` for a narrative DataFrame summary.
- Mention optional tools by name only when optional dependencies and side effects are acceptable.
- `data_raw` must be a pandas DataFrame for the wrapper method; the wrapper converts it to the dictionary state expected by EDA tools.

## 9. Combine loading and EDA without an LLM

```python
import pandas as pd
from ai_data_science_team.tools.data_loader import load_file
from ai_data_science_team.tools.dataframe import get_dataframe_summary
from ai_data_science_team.tools.eda import describe_dataset

content, artifact = load_file.func("data/churn_data.csv")
if artifact["status"] != "ok":
    raise RuntimeError(artifact["error"])

df = pd.DataFrame(artifact["data"])
print(get_dataframe_summary(df, n_sample=5, skip_stats=True)[0])
content, describe_artifact = describe_dataset.func(data_raw=df.to_dict())
describe_df = pd.DataFrame(describe_artifact["describe_df"])
```

This is the preferred automation path for verification and batch jobs because it performs no model calls, service launches, downloads, training, or destructive writes.
