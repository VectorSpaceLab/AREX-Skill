# Setup, Memory, Registry, and Output Troubleshooting

## Import or package metadata fails

Symptoms: `ModuleNotFoundError: pyrit`, `PackageNotFoundError: pyrit`, console scripts missing.

Likely causes: PyRIT is not installed in the active Python environment; a checkout is on `PYTHONPATH` but the distribution metadata is missing; optional packages were installed into a different environment.

Recovery:
1. Run the root `scripts/pyrit_api_smoke.py --json` from the generated skill.
2. Install PyRIT into the environment that will run the workflow.
3. Avoid relying on the original checkout path; use package imports.

## Config file is missing or malformed

Symptoms: initialization fails while reading a config, scanner says the config is invalid, or values appear to be ignored.

Likely causes: wrong PyRIT home, invalid YAML, a relative path resolved from the wrong working directory, or CLI arguments overriding config values.

Recovery:
1. For no-secret debugging, start with `initialize_pyrit_async("InMemory", load_defaults=False, silent=True)` or an equivalent minimal flow.
2. Add one initializer/config layer at a time.
3. Keep credentials in environment files or secret stores, not inline in config committed to a repo.
4. Route CLI config precedence questions to `cli-backend-scanner`.

## Secrets appear in logs or examples

Symptoms: API keys, endpoints, connection strings, or Key Vault references are printed or copied into prompts.

Recovery: replace real values with placeholders before sharing logs; prefer `.env.local` or task-owned secret injection; never paste secrets into generated examples. If using Azure Key Vault, verify the reference format and identity permissions separately from PyRIT code.

## SQLite memory errors

Symptoms: unable to open database, schema/version errors, stale results, or labels unexpectedly returning old runs.

Likely causes: database path not writable, process working directory changed, an old database schema needs migration, or labels are too broad.

Recovery:
1. Use an explicit caller-approved SQLite path or a temporary file for tests.
2. Run schema migration/check code only when the user expects persistent database mutation.
3. Narrow labels and scenario/result IDs before deleting or rewriting data.
4. For no-persistence tasks, switch to `InMemory`.

## Azure SQL memory errors

Symptoms: ODBC driver failures, login/auth errors, network timeouts, or missing connection settings.

Decision: Azure SQL is optional and service-bound. Do not treat a SQLite or in-memory smoke as proof of Azure SQL readiness.

Recovery: verify ODBC driver installation, connection string/managed identity, firewall/network, database permissions, and schema migration plan outside any no-secret smoke helper.

## Registry lookup fails

Symptoms: unknown converter/target/scorer/initializer name, duplicate generated enum member, or a scenario/technique is not listed.

Likely causes: initializer not loaded, wrong registry family, instance name vs class name confusion, custom module not discoverable, or duplicate metadata.

Recovery:
1. Identify whether the task needs a class registry or an instance registry.
2. Confirm the initializer path ran before lookup.
3. Use registry list/discovery APIs or CLI list commands to inspect available names.
4. For scanner-specific list failures, route to `cli-backend-scanner`.

## Output rendering fails

Symptoms: result prints as raw objects, file sink fails, or notebook rendering is missing.

Recovery: choose a PyRIT output helper matching the object type, choose a sink with a writable destination, and keep formatting separate from memory retrieval. In notebooks, verify display dependencies separately.
