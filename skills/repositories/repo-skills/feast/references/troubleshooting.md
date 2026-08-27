# Feast Cross-Cutting Troubleshooting

Use this reference when a Feast request fails before it clearly belongs to a focused sub-skill, or when multiple areas are involved.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'feast'`
- CLI command `feast` is not found
- Import fails for a provider-specific source, store, or compute engine

Recovery:

1. Check the base package: `python -c "import feast; print(getattr(feast, '__version__', 'unknown'))"`.
2. Check the CLI: `feast --help` and `feast version`.
3. If a backend import fails, install the narrow extra for that backend instead of all extras, for example `feast[redis]`, `feast[snowflake]`, `feast[postgres]`, `feast[grpcio]`, `feast[rag]`, or `feast[milvus]`.
4. Route backend/extra decisions to `../sub-skills/integrations-and-extensibility/SKILL.md`.
5. For source-checkout contributor environments, route setup and tests to `../sub-skills/repo-development/SKILL.md`.

## Feature Repository Not Found

Symptoms:

- CLI cannot find `feature_store.yaml`
- `FeatureStore(repo_path=...)` points at the wrong directory
- Commands work from one shell directory but not another

Recovery:

1. Use one canonical feature repo root for both Python and CLI calls.
2. Prefer `feast --chdir <feature-repo> <command>` or `FeatureStore(repo_path='<feature-repo>')`.
3. If the YAML file is not named or located normally, use `--feature-store-yaml` or `fs_yaml_file` consistently.
4. Run `sub-skills/feature-repos-and-cli/scripts/feature_repo_doctor.py --repo <feature-repo>` for non-destructive config checks.

## Config Or Optional Backend Fails

Symptoms:

- Unknown provider/store type
- Credential, network, or service connection errors
- Cloud or vector store examples fail locally

Recovery:

1. Separate config parsing from service connectivity. First parse `feature_store.yaml` and identify `provider`, `registry`, `offline_store`, `online_store`, `feature_server`, and `auth` sections.
2. Install only the extra required by the selected store/provider.
3. Verify credentials and service reachability outside destructive Feast commands.
4. For local reproduction, switch to file offline store and SQLite online store when possible.
5. Route store/provider/compute selection to `../sub-skills/integrations-and-extensibility/SKILL.md`.

## Definition Versus Runtime Failure

Use this split:

- Constructor, schema, `Field` dtype, vector metadata, source wiring, ODFV, stream/batch feature view, label, permission-object, or feature-service definition failures: `../sub-skills/feature-definitions/SKILL.md`.
- `apply`, `plan`, registry path, CLI object listing, project naming, or teardown failures: `../sub-skills/feature-repos-and-cli/SKILL.md`.
- Historical retrieval, online retrieval, materialization, push ingestion, null/stale values, join keys, or saved datasets: `../sub-skills/retrieval-and-materialization/SKILL.md`.
- Feature server, registry server, offline server, transformation server, MCP, remote stores, TLS, auth, RBAC, ports, or endpoint failures: `../sub-skills/servers-and-remote/SKILL.md`.
- Vector field linting, vector DB config, document retrieval, embeddings, chunking, or RAG: `../sub-skills/rag-and-vector-search/SKILL.md`.

## Safe Command Defaults

Prefer read-only checks first:

```bash
feast --help
feast version
feast --chdir <feature-repo> configuration
feast --chdir <feature-repo> entities list
feast --chdir <feature-repo> feature-views list
```

Review before running commands with side effects:

- `feast apply` mutates registry/infrastructure state.
- `feast materialize` and `materialize-incremental` write to online stores.
- `feast push` writes feature rows.
- `feast teardown` removes Feast-managed infrastructure and should never be run against a shared or remote environment without explicit confirmation.
- Server commands bind ports and may expose endpoints; verify host, TLS, and auth settings first.

## When To Stop

Stop and ask for user confirmation or missing prerequisites when the task requires:

- Cloud credentials, Kubernetes cluster access, databases, vector DB services, Redis/Postgres/Snowflake/etc., or private datasets.
- Running destructive commands such as teardown or broad infrastructure apply.
- Broad integration test suites, benchmarks, notebooks, long-running materialization, or release/publish scripts.
- Installing broad extras or dev dependencies beyond the narrow workflow requested.
