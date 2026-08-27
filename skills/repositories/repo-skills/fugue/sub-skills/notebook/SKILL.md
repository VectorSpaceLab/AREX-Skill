---
name: notebook
description: "Use Fugue's Jupyter and IPython notebook extension, %%fsql magic,
  and notebook display setup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# notebook

Use this sub-skill for Fugue notebook integration and `%%fsql` cell magic.

## Covers

- `%load_ext fugue_notebook`
- `from fugue_notebook import setup, NotebookSetup`
- `%%fsql` cell magic, line engine parsing, and yielded local variables
- notebook display behavior for Fugue dataframes
- notebook-specific case-sensitivity and config controls

## Excludes

- Full FugueSQL grammar and query construction, which belong in `../sql/`
- Backend package installation and engine registration, which belong in `../backends/`
- Plain Python DAG code outside notebooks, which belongs in `../workflow/`

## Read these files

- `references/notebook-reference.md` for notebook setup, line syntax, and config examples
- `references/troubleshooting.md` for magic-registration and headless/runtime failures
- `scripts/notebook_smoke.py` for a safe import check that can optionally register magics inside IPython

## Typical user prompts

- "How do I use FugueSQL in a notebook cell?"
- "Why is %%fsql not recognized?"
- "How do I force FugueSQL cells to ignore case?"
- "How do I pass a Dask or DuckDB engine into %%fsql?"

If the user is writing SQL text rather than debugging notebook setup, route to `../sql/` after confirming the magic is loaded.
