---
name: fugue
description: "Operate Fugue workflows, FugueSQL, backend selection, and notebook
  magics for pandas and distributed dataframe execution."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Fugue

Use this skill when a request is about Fugue's unified dataframe and SQL workflow API. Fugue wraps pandas-style code and runs it on Native, Spark, Dask, Ray, DuckDB, Ibis, and Polars backends.

## Start here

- Read `references/overview.md` for install choices and the top-level API map.
- Read `references/troubleshooting.md` for generic import, extra, and runtime failures.
- Read `references/repo-provenance.md` when you need to judge staleness.
- Run `scripts/inspect_install.py --help` or `scripts/inspect_install.py` to confirm the installed package.
- Then choose the narrowest sub-skill:
  - `sub-skills/workflow/` for `FugueWorkflow`, `transform`, `process`, `output`, partitioning, checkpoints, `module`, and dataframe helpers.
  - `sub-skills/sql/` for `fugue_sql`, `fsql`, `fugue_sql_flow`, `raw_sql`, `YIELD`, `PRINT`, `TRANSFORM USING`, `OUTPUT USING`, and SQL templating.
  - `sub-skills/backends/` for execution-engine selection, registration, plugin imports, and backend extras.
  - `sub-skills/notebook/` for `%load_ext fugue_notebook`, `%%fsql`, `NotebookSetup`, and Jupyter display behavior.

## Quick install guide

Install the smallest extra that matches the task:

- `pip install fugue` for core dataframe and workflow helpers.
- `pip install "fugue[sql]"` for FugueSQL.
- `pip install "fugue[duckdb]"`, `"fugue[spark]"`, `"fugue[dask]"`, `"fugue[ray]"`, `"fugue[ibis]"`, `"fugue[polars]"`, or `"fugue[notebook]"` for a single backend or notebook support.
- `pip install "fugue[all]"` when you want the broad runtime set.

## Minimal import check

```bash
python -c "import fugue, fugue.api as fa; print(fugue.__version__)"
```

If the request mentions a backend, notebook, or FugueSQL syntax error, open the matching sub-skill before writing code.
