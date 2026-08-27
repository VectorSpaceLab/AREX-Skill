# Installation and Optional Features

## When to read

Read this before selecting an installation command or diagnosing an import that
fails only for a specific datasource, memory, UI, or MCP workflow.

## Base installation

```bash
pip install wrenai
wren --version
wren --help
```

The base package includes DuckDB support and the `wren` CLI. It requires Python
3.11 or newer.

## Add only the needed extra

Use one datasource extra matching the project's `data_source` or connection
profile. Do not install `all` only to fix a single connector.

```bash
pip install "wrenai[postgres]"
pip install "wrenai[mysql]"
pip install "wrenai[bigquery]"
pip install "wrenai[snowflake]"
pip install "wrenai[clickhouse]"
pip install "wrenai[trino]"
pip install "wrenai[mssql]"
pip install "wrenai[databricks]"
pip install "wrenai[redshift]"
pip install "wrenai[spark]"
pip install "wrenai[athena]"
pip install "wrenai[oracle]"
```

Other optional surfaces:

```bash
pip install "wrenai[memory]"       # LanceDB and sentence-transformer semantic retrieval
pip install "wrenai[mcp]"          # wren serve mcp
pip install "wrenai[ui]"           # browser profile form
pip install "wrenai[interactive]"  # interactive prompts
pip install "wrenai[main]"         # interactive + UI convenience group
```

`wrenai[all]` installs every listed connector and convenience extra. Use it only
for an intentionally broad development or demo environment.

## Matching a project to the install

1. Inspect `wren_project.yml` for `data_source` and `profile`.
2. If a profile exists, use `wren profile debug <name>` to inspect masked,
   resolved configuration rather than printing secrets.
3. Query connector-specific field requirements from the installed package:
   ```bash
   wren docs connection-info postgres
   wren docs connection-info duckdb --format md
   ```
4. Install the matching extra before testing a live connection.

DuckDB profiles generally point at a **directory** containing database files;
not at a single database path. File-backed models must use the catalog/schema
shape expected by the chosen connector.

## Framework and browser packages

```bash
pip install wren-langchain
pip install wren-pydantic
npm install @wrenai/wren-core-wasm
```

The framework packages forward datasource and memory extras to `wrenai`, so
installing for a specific connector can be done on the framework package too:

```bash
pip install "wren-langchain[postgres,memory]"
pip install "wren-pydantic[postgres,memory]"
```

## Safe checks before side effects

Use the bundled root helper for a read-only check:

```bash
python scripts/check_wren_environment.py
```

For package API inspection, these are also safe:

```bash
python -c "import wren, wren_core; print(wren.__version__)"
wren skills list
wren docs connection-info duckdb
```

Do not treat any of these checks as a proof that a remote database, cloud
credential, MCP client, deployment provider, or semantic-memory model is ready.
