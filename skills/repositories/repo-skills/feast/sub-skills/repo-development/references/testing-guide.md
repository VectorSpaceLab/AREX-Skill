# Feast Testing Guide

## Unit vs Integration Boundary

Feast tests are split by dependency level:

- Unit tests live under `sdk/python/tests/unit/`; they should be fast and not require external cloud services.
- Integration tests live under `sdk/python/tests/integration/`; they exercise cross-store behavior, service-backed stores, Docker-backed local services, or cloud resources.
- Universal integration tests use parametrized fixtures to run the same behavior across offline stores, online stores, and providers.
- Prefer expanding an existing test when a fixture already covers the behavior; starting stores and universal fixtures is expensive.

Rule of thumb: if the test needs mocks for an external service, make it a unit test. If it requires real infrastructure, service containers, cloud credentials, or universal store fixtures, mark it as integration and document prerequisites.

## Common Test Targets

Targeted checks:

```bash
uv run python -m pytest sdk/python/tests/unit/test_unit_feature_store.py -v
uv run python -m pytest sdk/python/tests/unit/test_unit_feature_store.py -k "test_apply" -v
uv run python -m pytest sdk/python/tests/unit/infra/online_store/ -v
uv run python -m pytest sdk/python/tests/unit/infra/registry/ -v
```

Fast or broader local checks:

```bash
make test-python-smoke
make test-python-unit-fast
make test-python-unit
make test-python-changed
```

Integration checks:

```bash
make test-python-integration-local
make test-python-integration
make test-python-universal
```

Interpretation:

- `make test-python-smoke` is a quick development smoke that includes core `FeatureStore` and project-name validation tests.
- `make test-python-unit` runs unit tests under `sdk/python/tests/unit` with optional `pattern=<pattern>` filtering.
- `make test-python-integration-local` sets local integration environment variables and excludes several slow or unsafe subsets.
- `make test-python-integration` is CI-oriented and broad; do not treat it as a default local check.
- `make test-python-universal` runs broad integration coverage and should be reserved for backend/store changes with prerequisites.

## Path-to-Test Heuristics

Use these as starting points, then refine by nearby imports and existing test names.

| Changed path pattern | Suggested first tests | Notes |
|---|---|---|
| `sdk/python/feast/feature_store.py` | `sdk/python/tests/unit/test_unit_feature_store.py`, `sdk/python/tests/unit/infra/registry/` | Add `-k "apply or registry or plan"` for registry/apply changes |
| `sdk/python/feast/repo_config.py` | repo config and project validation unit tests | Also run YAML/config-related CLI tests when config discovery changes |
| `sdk/python/feast/cli/` | CLI unit tests and local init tests | Verify live CLI commands such as `init`, `apply`, `plan`, `validate`, `serve`, `serve_offline`, and `serve_registry` only when safe |
| `sdk/python/feast/infra/online_stores/` | matching `sdk/python/tests/unit/infra/online_store/` tests | Service-backed store tests may need integration skips |
| `sdk/python/feast/infra/offline_stores/` | matching offline store unit tests plus targeted retrieval tests | Cloud stores require credentials; skip unless available |
| `sdk/python/feast/infra/registry/` | `sdk/python/tests/unit/infra/registry/` | Include serialization/proto checks if registry protos change |
| `sdk/python/feast/permissions/` | permission/RBAC unit tests and server auth tests | Remote RBAC integration needs explicit authorization |
| `sdk/python/feast/feature_server.py` or server modules | server unit tests plus targeted smoke commands | Route server behavior details to `../../servers-and-remote/SKILL.md` |
| `protos/` | `make compile-protos-python`, `make protos`, Go/Java checks if affected | Generated files may change across languages |
| `go/` | `make format-go`, `make lint-go`, `make build-go`, `make test-go` | Go test target installs dependencies and compiles protos |
| `java/` | `make format-java`, `make lint-java`, `make test-java`, `make build-java` | Java integration tests are heavier |
| `docs/` | docs navigation review and relevant build target | Add or update navigation for new docs pages |
| `infra/website/docs/blog/` | frontmatter review | Blog posts require `title`, `description`, `date`, `authors` |

The bundled `../scripts/select_feast_tests.py` applies these heuristics and prints suggested commands without executing them.

## Writing or Reusing Tests

When adding tests:

1. Search for an existing test file in the same subsystem.
2. Match existing fixture signatures and parametrization style.
3. Prefer extending an existing test when setup cost is high.
4. For universal tests, use existing fixtures such as environment-style feature store fixtures and data-source creators.
5. Use store markers to bound coverage when possible, for example a marker with `only=["redis"]` for a specific online store.
6. Keep cloud/service requirements explicit in markers, test names, and skip conditions.

For new offline or online store behavior:

- Add or update store-specific config in the universal repo configuration area.
- Keep the initial local path small: unit tests plus a local or SQLite-backed integration where possible.
- Run broad universal integration only when services, credentials, and runtime budget are available.
- For external plugin-style verification, use a custom `FULL_REPO_CONFIGS_MODULE` rather than modifying the main repository just to test plugin configs.

## Safe Integration Selection

Treat the following as unsafe by default unless explicitly authorized:

- Cloud-backed stores such as BigQuery, Snowflake, Redshift, DynamoDB, or object storage paths needing credentials.
- Docker-backed local clusters when Docker is unavailable or cannot be started.
- Remote RBAC, Ray, Spark, Trino, Cassandra, Hazelcast, Milvus, Qdrant, MongoDB, Couchbase, SingleStore, and similar service-backed targets.
- Release, publish, or Docker push targets.
- Tests that mutate external infrastructure or require non-local secrets.

When skipping, report the command, prerequisite, and reason. Example: `Skipped make test-python-universal: requires service-backed stores and explicit credentials; ran unit registry coverage instead.`

## Difficult Case: Registry Change in `FeatureStore`

For a change touching registry/apply behavior in `sdk/python/feast/feature_store.py`, choose smallest safe checks first:

```bash
uv run ruff check sdk/python/feast/feature_store.py sdk/python/tests/unit/test_unit_feature_store.py
uv run ruff format sdk/python/feast/feature_store.py sdk/python/tests/unit/test_unit_feature_store.py
uv run bash -c "cd sdk/python && mypy feast/feature_store.py"
uv run python -m pytest sdk/python/tests/unit/test_unit_feature_store.py -k "apply or registry or plan" -v
uv run python -m pytest sdk/python/tests/unit/infra/registry/ -v
make test-python-smoke
```

Escalate only if the change affects retrieval/materialization or real backend behavior:

```bash
make test-python-integration-local
```

Record cloud-backed universal tests as skipped unless credentials and services are confirmed.

## Difficult Case: New Online Store Docs and Tests

For a new online store contribution:

1. Route extension design to `../../integrations-and-extensibility/SKILL.md` for implementation checklist.
2. Add unit tests under the matching online store test area using mocks when possible.
3. Add minimal integration config only when the store can be exercised safely.
4. Run scoped checks:

```bash
uv run ruff check sdk/python/feast/infra/online_stores/<store>.py sdk/python/tests/unit/infra/online_store/
uv run bash -c "cd sdk/python && mypy feast/infra/online_stores/<store>.py"
uv run python -m pytest sdk/python/tests/unit/infra/online_store/ -k "<store>" -v
```

5. Update docs as described in `docs-and-protos.md`; do not put a normal reference page under the blog directory.
