# Feast Repo Development Troubleshooting

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'feast'`
- `feast: command not found`
- Python tests import an installed release instead of the editable checkout
- `uv run` cannot find pinned dependencies

Actions:

```bash
make install-python-dependencies-dev
uv run python -c "import feast; print(feast.__version__)"
uv run feast version
```

If the task only needs a small static edit, avoid full reinstall until a command actually fails. If editable install is needed, run the dev dependency target from the repository root.

Expected package/CLI facts for this generated skill:

- Installed Feast distribution observed as `0.1.dev1+geb042f04f` during inspection.
- The console entry point is `feast`.
- Live CLI commands include `init`, `apply`, `plan`, `materialize`, `materialize-incremental`, `serve`, `serve_offline`, `serve_registry`, `get-online-features`, `get-historical-features`, `permissions`, `validate`, and `ui`.

## Optional Extra and Backend Errors

Symptoms:

- Import errors for cloud, vector, database, Spark, Ray, Redis, or other backend libraries.
- Tests fail only for a backend-specific store.
- An optional integration imports but cannot connect to a service.

Actions:

1. Identify the backend from the changed path or failing test name.
2. Check whether the relevant optional extra is needed.
3. Prefer mocked unit tests for store logic when possible.
4. Skip service-backed tests unless credentials and services are explicitly available.
5. Route backend selection and extension design to `../../integrations-and-extensibility/SKILL.md` when the user asks about optional store/provider configuration rather than contributor mechanics.

Do not install all extras just to run a small unit test. Use the narrowest dependency set that matches the changed subsystem.

## Ruff, Formatting, and MyPy Failures

Scoped repair loop:

```bash
uv run ruff check --fix <changed-python-paths>
uv run ruff format <changed-python-paths>
uv run ruff check <changed-python-paths>
uv run bash -c "cd sdk/python && mypy feast/<changed-module>.py"
```

Common signals:

- Ruff import-order failures: keep first-party imports under `feast` grouped consistently.
- Ruff format check failures: run `uv run ruff format` on changed files, not the whole tree unless needed.
- MyPy dynamic backend failures: check existing nearby use of `cast`, `Optional`, protocol-like interfaces, and typed config classes.
- Missing generated proto types: regenerate protobufs when `.proto` files or generated interfaces changed.

## Test Selection Failures

Symptoms:

- A broad suite is slow, flaky, or asks for missing services.
- `pytest` cannot find optional backend imports.
- Integration tests fail because Docker, cloud credentials, or local clusters are unavailable.

Actions:

1. Re-run the smallest relevant unit test with `-v --tb=short`.
2. Use `-k` to focus behavior, for example `-k "apply or registry or plan"`.
3. Use subsystem directories such as `sdk/python/tests/unit/infra/registry/` or `sdk/python/tests/unit/infra/online_store/`.
4. Escalate to `make test-python-smoke` before broad integration.
5. Skip unsafe service-backed tests with an explicit reason.

Safe skip wording:

```text
Skipped make test-python-universal because it requires service-backed integration prerequisites; ran scoped unit and smoke tests instead.
```

## Config and Data Validation Failures

Symptoms:

- Config parsing errors in `feature_store.yaml`
- Validation errors from Pydantic or Feast config classes
- Wrong provider, registry path, online store, offline store, or serialization version
- Data source schema inference mismatch

Contributor actions:

- For implementation changes, add or update unit tests around config parsing and validation.
- For user-facing repo config questions, route to `../../feature-repos-and-cli/SKILL.md`.
- For schema/object modeling failures, route to `../../feature-definitions/SKILL.md`.
- For retrieval/materialization data mismatches, route to `../../retrieval-and-materialization/SKILL.md`.

Useful API facts for contributor tests:

```python
from feast import FeatureStore
store = FeatureStore(repo_path=".")
```

`FeatureStore` can also be constructed with `config=` or `fs_yaml_file=`. Verified methods include `apply`, `plan`, `get_historical_features`, `get_online_features`, `materialize`, `materialize_incremental`, `push`, `serve`, `serve_offline`, and `serve_registry`.

## CLI and API Misuse

Symptoms:

- CLI command exists but fails in the wrong working directory.
- A command reads a different feature repository than expected.
- Python API calls fail because feature references, project names, or repo paths are wrong.

Actions:

- Use explicit CLI repo selection such as a chdir/global repo flag when validating feature repository commands.
- Use `feast plan` before `feast apply` for user-facing repository changes.
- Use `feast validate` for safe validation when appropriate.
- For contributor CLI implementation changes, add or update CLI unit tests instead of running mutating real-repo commands.

Route operational CLI usage to `../../feature-repos-and-cli/SKILL.md`; keep this sub-skill focused on changing and testing the Feast codebase.

## Backend Credentials and Service Failures

Symptoms:

- `403`, `401`, missing token, missing cloud project, missing AWS/GCP/Azure credentials.
- Docker daemon unavailable or local service ports unavailable.
- Redis, Trino, Spark, Ray, Milvus, Qdrant, MongoDB, Cassandra, Hazelcast, Couchbase, SingleStore, or Snowflake tests fail before exercising changed code.

Actions:

1. Do not paper over credential failures by changing production code.
2. Confirm the failing test is required for the changed subsystem.
3. Prefer mocked unit tests or local SQLite/file provider tests.
4. Record the native integration test as skipped if prerequisites are unavailable.
5. Ask before starting Docker clusters, cloud-backed tests, or long integration suites.

## Protobuf and Generated Artifact Failures

Symptoms:

- `DecodeError` while reading registries.
- Generated Python/Go protobuf packages missing new fields.
- Go or Java serving code fails after proto changes.

Actions:

```bash
make compile-protos-python
make compile-protos-go
make protos
```

Then run language checks appropriate to the affected files. If only Python generated code changes, `make compile-protos-python` plus targeted Python tests may be enough. If serving API protos changed, include Go and Java validation when feasible.

## Docs and Navigation Failures

Symptoms:

- A docs page exists but does not appear in the rendered site.
- A blog post is placed under the wrong directory.
- Blog frontmatter is missing required fields.
- Config or CLI behavior changed without reference docs.

Actions:

- Put blog posts only under `infra/website/docs/blog/`.
- Include blog frontmatter fields: `title`, `description`, `date`, and `authors`.
- Put normal reference docs under `docs/` and update navigation.
- For new stores, update store reference docs and indices.
- Use `make build-templates`, `make build-sphinx`, or `make build-helm-docs` only when relevant tooling and files are in scope.

## Workflow-Specific Failure Matrix

| Workflow | Failure signal | First response |
|---|---|---|
| Small Python SDK edit | Ruff/MyPy or targeted unit failure | Fix scoped file, rerun scoped command |
| Registry/apply change | `FeatureView not found`, stale registry diff, failing apply/plan test | Run `test_unit_feature_store.py` and registry unit tests |
| New backend/store | Optional dependency or service connection failure | Use unit mocks first; skip service tests without prerequisites |
| Proto change | Decode errors or missing generated fields | Regenerate protos and run language-specific checks |
| Docs change | Page missing from navigation or wrong blog path | Move to correct docs/blog location and update navigation |
| Server/RBAC change | 401/403 vs missing object confusion | Route serving semantics to server sub-skill; run scoped server/auth tests |
