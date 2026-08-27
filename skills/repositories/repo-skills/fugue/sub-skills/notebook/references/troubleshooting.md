# Notebook troubleshooting

## `%%fsql` is not recognized

**Symptoms**
- The cell magic is unknown

**Likely cause**
- The extension was not loaded in the active IPython kernel.

**Fix**
- Run `%load_ext fugue_notebook` in the notebook.
- Or call `from fugue_notebook import setup; setup()`.

## Running outside IPython or Jupyter

**Symptoms**
- `get_ipython()` is `None`
- `setup(...)` cannot register magics in a plain Python process

**Likely cause**
- Notebook magics require IPython/Jupyter.

**Fix**
- Use `fugue.api.fugue_sql(...)` or `fugue_sql_flow(...)` in plain Python.
- Use `scripts/notebook_smoke.py` as an import check outside notebooks; it only registers magics when IPython is present.

## SQL parser missing in notebook cells

**Symptoms**
- `%%fsql` loads but a cell fails before execution

**Likely cause**
- The `sql` extra is missing even if the notebook extra is installed.

**Fix**
- Install both notebook and SQL dependencies, for example `pip install "fugue[notebook,sql]"` or `pip install "fugue[all]"`.

## Engine-line config is not parsed

**Symptoms**
- `%%fsql spark my_conf` fails or uses the wrong config

**Likely cause**
- The line parser treats the second token as a variable name unless it starts with `{`.

**Fix**
- Use a JSON literal after the engine token, or make sure the named config variable exists in the notebook local namespace.

## `NotebookSetup` rejects config

**Symptoms**
- `ValueError` saying a config key must be a certain value

**Likely cause**
- `get_post_conf()` enforces a value that the cell line tried to override.

**Fix**
- Remove the conflicting cell-line setting or update the `NotebookSetup` policy intentionally.

## Classic notebook highlighting does not appear

**Symptoms**
- The magic works, but FugueSQL syntax highlighting is absent

**Likely cause**
- The JavaScript highlighting hook is classic Notebook-specific and may not run in JupyterLab or headless execution.

**Fix**
- Treat highlighting as optional. The SQL execution path is controlled by the magic registration, not by the JavaScript highlighter.
