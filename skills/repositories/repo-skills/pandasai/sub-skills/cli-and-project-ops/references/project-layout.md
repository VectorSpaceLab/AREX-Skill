# PandasAI Project Layout

## Purpose

Use this when CLI or semantic-layer behavior depends on the current working
directory, `.env`, or `datasets/` placement.

## Project root discovery

PandasAI walks upward from the current working directory until it finds a common
project marker such as:

- `pyproject.toml`
- `setup.py`
- `requirements.txt`
- or a custom marker used by helper calls

If no marker is found, the current working directory is used as the project root.

## Dataset layout

The default local file manager stores datasets under:

```text
<project-root>/datasets/<organization>/<dataset>/
  schema.yaml
  data.parquet          # for local dataframe-backed datasets
```

SQL-backed virtual datasets usually store only `schema.yaml` locally; real query
execution happens through an optional connector.

## `.env` layout

`pai login` writes `PANDABI_API_KEY=...` to:

```text
<project-root>/.env
```

If `.env` already exists, the CLI preserves unrelated lines and replaces any
existing `PANDABI_API_KEY=` line.

## Operational advice

- Run CLI commands from the intended application or project root.
- Avoid running `pai login` from a nested directory that might discover a parent
  repository unexpectedly.
- Keep real API keys out of examples and logs.
- If a dataset cannot be loaded, print the detected current working directory
  and inspect the expected `datasets/<organization>/<dataset>/schema.yaml` path.
