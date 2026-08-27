# Repo Development Troubleshooting

Use this guide when source-editing, formatter, test, protobuf, dashboard, API compatibility, CI, or PR-prep work fails. Route runtime SkyPilot operation failures to the relevant sibling sub-skill.

## Formatter Version Mismatch

Symptoms:

- `format.sh` exits with `Wrong yapf version installed`, `Wrong pylint version installed`, `Wrong pylint-quotes version installed`, or `Wrong mypy version installed`.
- Local formatting differs from CI formatting.

Fix:

- Install development dependencies from `requirements-dev.txt` in the active development environment.
- Confirm the exact versions: `yapf==0.32.0`, `pylint==2.14.5`, `pylint-quotes==0.2.3`, `isort==5.12.0`, and `mypy==1.19.1`.
- Rerun `bash format.sh --files <changed-python-files>` for focused Python changes or `bash format.sh` for changed files against `origin/master`.
- If `format.sh` reports reformatted files, review the diff and rerun or include the change in the PR.

## `format.sh` Hangs Or Formats Too Much

Symptoms:

- Formatter appears to wait for input.
- Unexpected files are reformatted.
- `origin/master` is missing, so changed-file detection fails.

Fix:

- Prefer `bash format.sh --files path/to/file.py` during targeted work.
- Fetch or set up `origin/master` before relying on default changed-file mode.
- Avoid `--all` unless preparing a repo-wide formatting change.
- Do not hand-format `sky/schemas/generated/`; regenerate protobuf outputs instead.

## Mypy Or Pylint Fails Outside The Change

Symptoms:

- `format.sh` reaches mypy/pylint and reports unrelated existing failures.
- Pylint skips or includes unexpected paths.

Fix:

- First run a narrower command for the touched tests or files to prove the change.
- Check whether the failure is from `tests/mypy_files.txt` or changed `sky/`/`examples/` paths.
- Do not fix unrelated failures unless the user asks; record them as pre-existing or out-of-scope in the handoff.
- For new TODO/FIXME comments, include an owner: `TODO(username): ...`.

## Protobuf Generated Files Are Out Of Date

Symptoms:

- CI `compile-protos-check` fails with a diff in `sky/schemas/generated/`.
- Generated `.py`, `_pb2.py`, `_pb2_grpc.py`, or `.pyi` outputs do not match `.proto` sources.

Fix:

```bash
python -m grpc_tools.protoc \
  --proto_path=sky/schemas/generated=sky/schemas/proto \
  --python_out=. \
  --grpc_python_out=. \
  --pyi_out=. \
  sky/schemas/proto/*.proto
```

- Use compatible generator packages: `grpcio-tools==1.63.0`, `grpcio==1.63.0`, and `protobuf==5.29.6`.
- Commit regenerated outputs only because source `.proto` files changed.
- Do not edit generated files manually.

## API Version Or Compatibility Review Fails

Symptoms:

- Reviewers ask for `API_VERSION` handling.
- `APINotSupportedError`, ignored-field warnings, or old-client/new-server failures appear.
- Payload tests fail after adding or renaming request/response fields.

Fix:

- If adding a new API or incompatible API behavior, bump `API_VERSION` in `sky/server/constants.py` and add a named minimum-version constant when the feature needs gating.
- Decorate new SDK methods with `@versions.minimal_api_version(...)`.
- For existing SDK methods, branch with `versions.get_remote_api_version()` and provide fallback behavior for compatible older peers.
- Add defaults for new payload fields when possible; otherwise select version-aware bodies or serializers.
- Do not manually edit `MIN_COMPATIBLE_API_VERSION` or `MIN_COMPATIBLE_VERSION`.
- Add focused tests in server/client compatibility areas and consider `/quicktest-core` for CI coverage.

## Dashboard Is Missing, Stale, Or Fails After API Changes

Symptoms:

- Local API server starts but dashboard assets are missing or stale.
- Dashboard endpoint returns a blank page or outdated UI.
- Dashboard API client breaks after backend changes.

Fix:

```bash
npm --prefix sky/dashboard install
npm --prefix sky/dashboard run lint
npm --prefix sky/dashboard run format:check
npm --prefix sky/dashboard run test
npm --prefix sky/dashboard run build
sky api stop
sky api start
```

- For source checkouts, rebuild before restarting the API server.
- Keep dashboard API-version constants/client code aligned with server API changes.
- For development mode, set `SKYPILOT_API_SERVER_ENDPOINT` only when connecting to a non-local API server.

## Import Time Or Heavy Dependency Regression

Symptoms:

- CLI startup becomes slower after adding imports.
- `python -X importtime -c "import sky"` shows a new heavy module during base import.
- Optional provider dependency imports fail for users without that provider extra.

Fix:

- Keep imports at module top by default, but use `LazyImport` for third-party modules imported during `import sky` when import time is significant.
- Move type-only imports under `if typing.TYPE_CHECKING:`.
- Avoid importing cloud/provider SDKs from base modules unless the provider extra is selected.
- Measure with `python -X importtime -c "import sky"`; use `tuna import.log` if deeper visualization is needed.

## Unit Tests Pass But Smoke Tests Are Needed

Symptoms:

- The change affects real provisioning, credentials, managed jobs, serving, Kubernetes, Slurm, SSH, or cloud cleanup.
- Review requires confidence beyond parser/unit tests.

Fix:

- Do not run smoke tests by default; they can launch clusters and cost money.
- Ask/confirm before running local smoke tests and specify cloud/backend flags.
- Prefer a focused target such as `pytest tests/test_smoke.py::test_minimal` or a CI comment like `/smoke-test -k test_name`.
- Use `--terminate-on-failure` only when preserving failed clusters for debugging is not needed.
- Record skipped smoke tests and why in `Tested:` if credentials or budget are unavailable.

## Buildkite Status Is Unclear

Symptoms:

- PR comment triggered CI but results are not visible yet.
- Need detailed Buildkite logs for `/quicktest-core` or `/smoke-test`.

Fix:

- First check the PR commit status checks for the Buildkite URL; it may take a moment to appear after triggering.
- If using the Buildkite API, a `BUILDKITE_TOKEN` with read access is required.
- A typical API check is `curl -H "Authorization: Bearer $BUILDKITE_TOKEN" "https://api.buildkite.com/v2/organizations/skypilot/pipelines/<pipeline>/builds/<build-number>"`.
- Do not expose tokens in logs, Markdown, or PR comments.

## API Server Manual Test Does Not Pick Up Source Changes

Symptoms:

- Manual API behavior still reflects old code.
- Dashboard changes do not appear after editing.

Fix:

- Stop and restart the API server after Python source edits: `sky api stop` then `sky api start`.
- Rebuild dashboard before restart if dashboard files changed.
- For remote or containerized servers, rebuild and redeploy the image rather than expecting local source changes to apply.
- For Helm upgrades, use `--reuse-values` on existing deployments to preserve database, auth, storage, and credential config.

## Critical Path Change Seems Small But Risky

Symptoms:

- A small diff touches managed jobs recovery, request executor, backend status caching, SSH/provisioning, CLI/SDK semantics, or cloud provider abstractions.
- Existing tests do not cover failure/retry/race behavior.

Fix:

- Identify the state machine, retry, concurrency, or compatibility invariant before editing.
- Add a narrow unit test that exercises the edge case without launching cloud resources when possible.
- For API server code, consider memory and latency impact; avoid broad blocking work in request paths.
- For `Cloud` subclasses, keep cloud objects lightweight/stateless and cache expensive provider queries in cloud utility modules.
- For CLI/SDK UX, avoid changing existing flag meanings or return types without compatibility and docs.

## Dependency Change Breaks Installation

Symptoms:

- `pip install -e .` or `uv pip install -e ".[all]"` fails.
- `pip check` reports incompatible packages.
- Optional extras pull in broad or conflicting dependencies.

Fix:

- Put core dependencies only in core install requirements; keep cloud-specific dependencies in extras.
- Preserve Python 3.9-3.11 compatibility.
- Add comments for non-obvious pins or upper bounds, especially for typing/runtime compatibility.
- Test minimum and latest allowed versions when the dependency is central or cloud-provider-facing.

## PR `Tested:` Section Is Too Vague

Symptoms:

- PR says only "tested locally" or omits commands.
- Reviewers cannot tell whether cloud/API/dashboard/protobuf compatibility was covered.

Fix:

Use concrete bullets:

```text
Tested:
- `bash format.sh --files sky/server/foo.py tests/unit_tests/test_sky/server/test_foo.py`
- `pytest tests/unit_tests/test_sky/server/test_versions.py tests/unit_tests/test_sky/server/requests/test_payloads.py`
- `npm --prefix sky/dashboard run test`
- Not run: smoke tests; require cloud credentials and are covered by planned `/smoke-test -k ...`.
```

Mention generated protobuf regeneration, dashboard rebuild, API-server restart, or CI trigger commands when relevant.
