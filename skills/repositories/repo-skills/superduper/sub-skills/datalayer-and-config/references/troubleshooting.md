# Datalayer and Configuration Troubleshooting

Use this when Superduper import, configuration, backend connection, schema/query, or Datalayer lifecycle work fails before the task reaches model/listener/vector logic.

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'superduper_mongodb'` when using `mongodb://`, `mongodb+srv://`, or `mongomock://` | The base package is installed but the MongoDB plugin package is missing. | Install the MongoDB plugin for that environment, then rerun the import smoke. For a no-service local smoke, use `mongomock://...` after the plugin is installed. |
| `ModuleNotFoundError: No module named 'superduper_sql'` when using `sqlite://`, `duckdb://`, `postgresql://`, `mssql://`, or `mysql://` | SQL URI schemes route to the SQL plugin. | Install the SQL plugin and its backend-specific dependencies; use a scratch SQLite/DuckDB URI before trying a remote DB. |
| `No support for uri: ...` or `ValueError` from `superduper("...")` | Connection string lacks a URI scheme or uses an unsupported scheme. | Use a documented scheme such as `mongomock://name`, `mongodb://host/db`, `sqlite://...`, `duckdb://...`, `snowflake://...`, `redis://...`, or `inmemory://...`. |
| Import emits `Warning: The path '~/.superduper/secrets' is not a valid directory` | The default secrets directory is absent. | For local/scratch tasks, this is non-blocking. For credentialed plugins, create the expected secrets structure or pass environment variables/config that the plugin expects. |
| `ConfigError` or import-time failure after setting `SUPERDUPER_CONFIG` | Config path is missing or invalid YAML/fields. | Set `SUPERDUPER_CONFIG` to an existing YAML file before import, remove unknown fields, and verify booleans/paths. |
| Changing `artifact_store` in a `superduper(..., artifact_store=...)` call appears ineffective | In this version, artifact-store construction reads the process-global config. | Prefer a config file or `SUPERDUPER_ARTIFACT_STORE` before the first import when artifact-store location matters. |
| `superduper --help` fails with `No module named 'superduper.__main__'` | The package declares a console script but this checkout lacks `superduper.__main__`. | Do not route users through the CLI for this version. Use Python API calls or the bundled smoke helpers. Refresh the skill if a later repo version adds the CLI module. |
| `db.drop(...)` prompts or risks deleting data | Drop is destructive and confirmation-protected unless `force=True`. | Only call `drop(force=True, data=True)` against scratch URIs created for the current test. For real service URIs, ask for explicit confirmation and prefer targeted cleanup. |
| `identifier cannot be empty or None` | A `Component`/`Table`/`Model` was constructed without an identifier. | Supply a stable `identifier` string; use lowercase or descriptive names when they become output table/model identifiers. |
| Schema/datatypes fail during encode/decode or vector indexing | Field names or datatype strings do not match actual data/model outputs. | Start with primitive fields, add explicit vector dimensions, and run a tiny `Document`/`Schema` or vector smoke before applying a listener/index. |
| Queries return no rows after insert | Table name, primary id, backend transaction semantics, or filter expression is wrong. | List rows without filters first, check table spelling, coerce result to `list(...)`, and verify backend/plugin support for the operator. |
| Listener/vector output query fails through `outputs`, `missing_outputs`, or `like` | The issue belongs to component/vector workflow output tables, not only the base query layer. | Route to `components-and-workflows` for listener outputs or `vector-search-and-retrieval` for `like(..., vector_index=...)`. |

## Debug sequence

1. Run the bundled helper in import-only mode:

   ```bash
   python scripts/superduper_datalayer_smoke.py --check-imports
   ```

2. If a Datalayer must be built, use a scratch URI and explicit flag:

   ```bash
   python scripts/superduper_datalayer_smoke.py --check-imports --build-db --uri mongomock://skill-smoke
   ```

3. If the task uses a config file, set or pass it before import/build:

   ```bash
   python scripts/superduper_datalayer_smoke.py --build-db --config-path /path/to/scratch-superduper.yaml
   ```

4. When the helper reports a missing optional plugin, install only the plugin required by the selected URI. Do not install every plugin unless the user explicitly asks for broad optional coverage.
