# Notebook reference

## Basic setup

```python
%load_ext fugue_notebook
```

Or call the setup helper from Python:

```python
from fugue_notebook import setup
setup(fsql_ignore_case=True)
```

`setup(notebook_setup=None, is_lab=False, fsql_ignore_case=False)` registers the notebook environment. Set `is_lab=True` when JavaScript notebook highlighting should not be injected as classic Notebook code.

## Cell magic basics

```python
%%fsql
CREATE [[0]] SCHEMA a:int
PRINT
```

The cell content is parsed as FugueSQL and executed as a workflow.

## Engine line syntax

The `%%fsql` line is parsed before the cell body:

| Line | Meaning |
| --- | --- |
| `%%fsql` | use the default/current engine |
| `%%fsql native` | use the Native execution engine |
| `%%fsql dask+duckdb` | use Dask execution with DuckDB as the SQL engine |
| `%%fsql spark {"spark.sql.shuffle.partitions": 4}` | use a JSON config literal |
| `%%fsql dask my_conf` | read config from a notebook variable named `my_conf` |

If `+` appears in the engine token, Fugue passes an `(execution_engine, sql_engine)` tuple to `make_execution_engine(...)`.

## Sharing outputs between cells

Use `YIELD DATAFRAME` to expose a result into the notebook namespace:

```python
%%fsql native
a = CREATE [[0]] SCHEMA a:int YIELD DATAFRAME
```

A later cell can read `a`:

```python
%%fsql native
SELECT * FROM a
PRINT
```

## Custom `NotebookSetup`

Subclass `NotebookSetup` when a notebook needs default or enforced engine config:

```python
from fugue_notebook import NotebookSetup, setup

class MySetup(NotebookSetup):
    def get_pre_conf(self):
        return {"fugue.sql.compile.ignore_case": True}

    def get_post_conf(self):
        return {"fugue.workflow.exception.hide": False}

setup(MySetup(), fsql_ignore_case=True)
```

`get_post_conf()` values are enforced. If a user-supplied config conflicts, the magic raises a `ValueError` instead of silently overriding.

## Display behavior

When IPython is active, Fugue registers a notebook display adapter for Fugue dataframes. It renders a small HTML preview, schema string, and optional row count.

## Read next

- `references/troubleshooting.md`
- `scripts/notebook_smoke.py`
