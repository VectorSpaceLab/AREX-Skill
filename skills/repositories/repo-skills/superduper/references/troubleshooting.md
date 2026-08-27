# Superduper Cross-Cutting Troubleshooting

Use this reference before diving into a sub-skill when the failure could be install, import, plugin, backend, config, or CLI related.

## Fast diagnostic

Run the root helper without network or credentials:

```bash
python scripts/check_superduper_env.py --as-json
```

For plugin-specific import checks:

```bash
python sub-skills/plugins-and-integrations/scripts/check_superduper_plugins.py mongodb sql openai
```

For Datalayer construction checks:

```bash
python sub-skills/datalayer-and-config/scripts/superduper_datalayer_smoke.py --check-imports --build-db --uri mongomock://skill-smoke
```

## Common failures

| Symptom | Likely cause | Next route / fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'superduper'` | Base package not installed in the active Python environment. | Install `superduper-framework` and rerun `scripts/check_superduper_env.py`. |
| `ModuleNotFoundError: No module named 'superduper_mongodb'` or another `superduper_<name>` module | Optional plugin missing for the selected backend/provider. | Use `plugins-and-integrations` to choose and install only the needed plugin. |
| `superduper --help` fails with `No module named 'superduper.__main__'` | This source snapshot declares a console script but lacks the target module. | Use Python API calls and bundled smoke helpers. Refresh this skill if a later version adds the CLI. |
| Import warns about `~/.superduper/secrets` | Default secrets directory is absent. | Non-blocking for local/scratch tasks; credentialed plugins need configured env vars or secrets. |
| Default `superduper()` tries `mongodb://localhost:27017/test_db` and fails | Default config expects MongoDB and the MongoDB plugin/service. | Use `mongomock://...` with `superduper_mongodb` for no-service smoke, or provide the real service URI. |
| `sqlite://` or `duckdb://` fails despite base install | SQL URI routes to the SQL plugin. | Install `superduper_sql`; verify local SQL dependencies before remote DBs. |
| Cloud/API plugin imports but live calls fail | Credentials, network, service endpoint, or account/model access is missing. | Treat import as only a package check; configure credentials/services and use plugin docs under `plugins-and-integrations`. |
| Torch/Transformers/vLLM plugin install/import is slow or fails | Heavy optional ML stack, GPU/runtime/wheel mismatch, or model download dependency. | Do not add GPU/model packages unless the task requires them. Verify hardware/framework separately. |
| `db.drop` threatens user data | Destructive Datalayer operation. | Only use scratch URIs; ask for explicit confirmation for shared/production data. |
| Vector search returns empty or bad results | Listener outputs not materialized, dimensions mismatch, unsupported measure, or missing backend plugin. | Route to `vector-search-and-retrieval`. |
| Listener outputs missing | Wrong `select`, `key`, model signature, or component was registered without jobs. | Route to `components-and-workflows`. |

## Triage order

1. Confirm base import and version.
2. Confirm the selected backend/provider plugin import.
3. Confirm config values are set before the first `import superduper` when config is import-time sensitive.
4. Build the smallest scratch Datalayer before applying models/listeners/vector indexes.
5. Add one component family at a time: table/data, model/listener, vector index, optional provider/backend plugin.
6. Only then run service-backed, credentialed, GPU, or model-download workflows.

## Privacy and safety

Do not paste API keys, database passwords, cloud account secrets, or private connection strings into prompts. Use redacted URIs when asking for help. Never run destructive Datalayer calls on a user's real database without explicit confirmation.
