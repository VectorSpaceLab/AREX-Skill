# Automation Recipes

## When to read

Read this when a user wants fg-data-profiling in a scheduled job, data pipeline,
IDE external tool, or shell batch workflow.

## Shell batch recipe

```bash
set -euo pipefail
for csv in data/*.csv; do
  report="reports/$(basename "${csv%.*}")-profile.html"
  mkdir -p "$(dirname "$report")"
  data_profiling --silent --minimal "$csv" "$report"
done
```

Use `--silent` for unattended runs. For non-CSV inputs, verify the extension is
supported by the CLI reader or load with Python first.

## Python task wrapper

This pattern is useful in workflow engines where Python callables are easier to
observe than shell commands:

```python
from pathlib import Path
import pandas as pd
from data_profiling import ProfileReport


def profile_file(input_path: str, output_path: str) -> str:
    df = pd.read_csv(input_path)
    profile = ProfileReport(df, title=f"Profile: {Path(input_path).name}", minimal=True)
    profile.to_file(output_path)
    return output_path
```

Prefer this over the CLI when you need custom reading, privacy-sensitive
preprocessing, sampling, or JSON post-processing.

## Airflow-style BashOperator pattern

```python
profiling_task = BashOperator(
    task_id="profile_customers",
    bash_command="data_profiling --silent --minimal /data/customers.csv /reports/customers-profile.html",
)
```

For sensitive data, pre-sample or redact in a Python task and use the privacy
sub-skill before writing shareable reports.

## IDE external tool pattern

An IDE external tool can call the installed `data_profiling` executable with:

```text
Arguments: "$FilePath$" "$FileDir$/$FileNameWithoutAllExtensions$_report.html"
Working directory: project root
```

Use the IDE's executable discovery to point at the environment where
fg-data-profiling is installed.

## Pipeline artifact pattern

For systems that can display inline HTML artifacts, use the Python API and pass
`profile.to_html()` into the platform's metadata format. If the platform serves
static files better than inline HTML, write `profile.to_file("report.html")` and
publish that file as an artifact.

## Validation before deployment

Run:

```bash
python scripts/cli_smoke.py --command data_profiling
```

If that fails, fix PATH/environment issues before wiring the command into a
scheduler.
