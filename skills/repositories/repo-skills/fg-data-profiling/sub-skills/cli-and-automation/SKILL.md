---
name: cli-and-automation
description: "Guides fg-data-profiling data_profiling and pandas_profiling CLI
  usage, input files, output naming, and automation patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI and Automation

Use this sub-skill when the user wants shell commands, batch jobs, pipeline
steps, or IDE tasks that invoke fg-data-profiling without writing a full Python
script.

## Read first

- Read [references/cli-reference.md](references/cli-reference.md) for the
  verified command names, positional arguments, flags, and input extension
  behavior.
- Read [references/automation-recipes.md](references/automation-recipes.md) for
  Airflow/Python-task, shell, and IDE-style automation patterns.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  missing executables, parser errors, file-reader limitations, and browser
  opening behavior.
- Run [scripts/cli_smoke.py](scripts/cli_smoke.py) when you need a safe
  no-network CLI validation against a tiny generated CSV.

## Primary command pattern

```bash
data_profiling --silent --minimal data.csv report.html
```

The legacy command name also exists:

```bash
pandas_profiling --silent --minimal data.csv report.html
```

Prefer `data_profiling` in new automation. If `output_file` is omitted, the CLI
uses the input file stem with a `.html` suffix.

## Verified CLI surface

The parser supports:

- `--version`
- `-s`, `--silent` to generate without opening a browser
- `-m`, `--minimal` for minimal configuration
- `-e`, `--explorative` for richer unicode/file/image-oriented analysis
- `--pool_size <int>`
- `--title <text>`
- `--infer_dtypes` and `--no-infer_dtypes`
- `--config_file <yaml>`
- positional `input_file`
- optional positional `output_file`

Use the Python API sub-skill when the user needs custom readers, advanced
preprocessing, redaction logic, or programmatic summary access.

## Automation boundary

CLI automation is best when each task starts from a standard local file and
writes an HTML report artifact. Use the Python API for:

- private or sensitive datasets needing custom samples/redaction decisions;
- non-standard input loading or database access;
- profile comparison or JSON post-processing;
- Spark DataFrames or notebook displays;
- dynamic configuration built in Python.

For settings-file generation and HTML asset behavior, route to
[../configuration-and-output/SKILL.md](../configuration-and-output/SKILL.md).
For optional Spark or notebook readiness, route to
[../integrations-and-backends/SKILL.md](../integrations-and-backends/SKILL.md).

## Safe validation

Run the bundled smoke helper before embedding a command in a larger pipeline:

```bash
python scripts/cli_smoke.py --command data_profiling
```

The helper creates a temporary CSV, calls the selected CLI, and verifies a
report file was created. It does not download data or require the source
repository checkout.
