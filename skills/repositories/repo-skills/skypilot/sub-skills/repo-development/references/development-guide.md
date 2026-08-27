# SkyPilot Development Guide

This guide is for coding agents modifying the SkyPilot repository. It distills maintainer evidence from the repo's development instructions, formatter/test configuration, CI workflows, protobuf sources, dashboard package, and critical source paths. Use sibling sub-skills for user-facing SkyPilot operations.

## Repository Map For Maintainers

- `sky/`: main Python package. Important entry points include `core.py`, `task.py`, `resources.py`, `optimizer.py`, `execution.py`, `exceptions.py`, `skypilot_config.py`, `client/`, `server/`, `jobs/`, `serve/`, `backends/`, `provision/`, `clouds/`, `data/`, `utils/`, `catalog/`, and `schemas/`.
- `tests/`: pytest coverage. `tests/unit_tests/` is the preferred focused starting point; `tests/smoke_tests/` and `tests/test_smoke.py` can launch real resources and are not default checks.
- `docs/source/`: Sphinx docs and contributor-facing guidance.
- `examples/` and `llm/`: user recipes and evidence for behavior; many examples require clouds, GPUs, downloads, or credentials.
- `sky/dashboard/`: Next.js dashboard. Python API-server changes can affect dashboard API calls, and dashboard source changes require Node/npm validation.
- `sky/schemas/proto/`: source protobuf definitions. Generated outputs live under `sky/schemas/generated/` and should be regenerated, not hand-edited.
- `sky/setup_files/`, `pyproject.toml`, `requirements-dev.txt`, `.github/workflows/`, `.buildkite/`, and `format.sh`: packaging, dependency, formatter, CI, and maintainer workflow surfaces.

## Development Setup Assumptions

SkyPilot development uses Python 3.9-3.11. A typical clean setup is:

```bash
uv venv --seed --python 3.11
source .venv/bin/activate
uv pip install -e ".[all]"
uv pip install -r requirements-dev.txt
```

Use narrower extras only when the change is scoped to a subset of clouds. Set `SKYPILOT_DEV=1` or `SKYPILOT_DEBUG=1` only for local debugging; do not bake environment-specific settings into source changes.

## Coding Conventions

- Follow Google Python style and the repo's YAPF/isort configuration.
- Prefer f-strings over `.format()` for readability.
- Use `class MyClass:` rather than `class MyClass(object):`.
- Use `abc` for abstract classes and keep type-only imports under `if typing.TYPE_CHECKING:`.
- Keep imports at file top unless a circular dependency forces a local import; if so, document the circularity, not performance.
- Use `LazyImport` for third-party modules imported during `import sky` when import time is significant, especially above roughly 100 ms.
- Use exceptions with clear messages for user-visible errors; reserve `assert` for debugging/proof-checking.
- Write `TODO(username): ...` and `FIXME(username): ...`, never bare TODO/FIXME markers.
- When dependency constraints change, update the owning dependency file and explain version limits with comments when compatibility is non-obvious.

## Formatting And Linting

`format.sh` is the canonical maintainer wrapper. It checks exact tool versions, formats Python, runs isort, mypy, pylint, and runs dashboard lint/format when Node/npm are available.

Key version pins from `requirements-dev.txt`:

- `yapf==0.32.0`
- `pylint==2.14.5`
- `pylint-quotes==0.2.3`
- `isort==5.12.0`
- `mypy==1.19.1`

Common commands:

```bash
bash format.sh
bash format.sh --files path/to/file.py
bash format.sh --all
```

Important behavior:

- `bash format.sh` formats Python files changed since `origin/master` and then runs repo-level isort, mypy, and selective pylint.
- `bash format.sh --files ...` is useful for targeted Python edits, but mypy and dashboard steps still run through the script.
- The script excludes `build/**`, `sky/schemas/generated/**`, and unit-test backend testdata from YAPF/isort globs.
- If `format.sh` changes files, review the diff and rerun or record the formatted files in the PR notes.

## Focused Test Selection

Start as close to the changed code as possible. Examples:

- Task/resources/YAML: `pytest tests/unit_tests/test_sky/test_task.py tests/unit_tests/test_resources.py tests/test_yaml_parser.py`
- CLI validation/help behavior: `pytest tests/unit_tests/test_sky/test_cli_launch_validation.py tests/unit_tests/test_sky/test_cli_helpers.py tests/unit_tests/test_sky/test_cli_json_output.py`
- Client SDK/API server: `pytest tests/unit_tests/test_client_sdks.py tests/unit_tests/test_sky/client/test_sdk_async.py tests/unit_tests/test_sky/server/test_versions.py tests/unit_tests/test_sky/server/requests/test_payloads.py`
- Managed jobs internals: `pytest tests/unit_tests/test_sky/jobs/test_client_sdk.py tests/unit_tests/test_sky/jobs/test_recovery_strategy.py tests/unit_tests/test_sky/jobs/test_server_core.py`
- SkyServe internals: `pytest tests/unit_tests/test_serve_service.py tests/unit_tests/test_serve_autoscaler.py tests/unit_tests/test_serve_proto_converter.py`
- Cloud/Kubernetes/storage utilities: `pytest tests/unit_tests/kubernetes tests/unit_tests/test_sky/clouds/test_kubernetes.py tests/unit_tests/test_sky/storage/test_storage_utils.py`
- API compatibility/smoke anchors: `pytest tests/test_api_compatibility.py` or CI `/quicktest-core` when old/new client-server behavior is in scope.

Pytest config sets `SKYPILOT_DEBUG=1`, disables usage collection, and defaults to parallel execution with `-n 16`. Use explicit files or test nodes for fast iteration.

Smoke tests can launch clusters and incur cost. Treat these as opt-in validation:

```bash
pytest tests/test_smoke.py::test_minimal
pytest tests/test_smoke.py --terminate-on-failure
```

CI comments for maintainers include `/quicktest-core`, `/smoke-test`, `/smoke-test --kubernetes --postgres`, and `/smoke-test --kubernetes --remote-server --postgres`.

## API Server Compatibility Changes

SkyPilot is client-server versioned. From the compatibility rules:

- Bump `API_VERSION` in `sky/server/constants.py` when an API change requires special compatibility handling.
- Do not manually edit `MIN_COMPATIBLE_API_VERSION` or `MIN_COMPATIBLE_VERSION`; CI owns those values.
- New SDK methods that call new APIs should use `@versions.minimal_api_version(...)`.
- Existing SDK methods that call changed APIs should branch on `versions.get_remote_api_version()` and preserve behavior for older compatible peers.
- Payload additions should have defaults when possible; incompatible payload changes need explicit version-aware body selection or fallback.
- Serialization/deserialization changes should account for old clients and old servers, especially for request bodies, status records, handles, managed jobs, serve replicas, and workspace/default fields.
- Add tests that exercise old/new behavior or update existing compatibility tests when changing API bodies, response fields, request statuses, or SDK semantics.

When dashboard code consumes the API, also update dashboard constants/client code and run dashboard checks.

## Protobuf Workflow

When editing any source `.proto` under `sky/schemas/proto/`, regenerate Python outputs:

```bash
python -m grpc_tools.protoc \
  --proto_path=sky/schemas/generated=sky/schemas/proto \
  --python_out=. \
  --grpc_python_out=. \
  --pyi_out=. \
  sky/schemas/proto/*.proto
```

The CI compile-protos check installs `grpcio-tools==1.63.0`, `grpcio==1.63.0`, and `protobuf==5.29.6`, then fails if `sky/schemas/generated/` has a diff. Regenerate rather than editing generated files manually.

## Dashboard Workflow

For dashboard source changes or API-server changes that affect dashboard pages:

```bash
npm --prefix sky/dashboard install
npm --prefix sky/dashboard run lint
npm --prefix sky/dashboard run format:check
npm --prefix sky/dashboard run test
npm --prefix sky/dashboard run build
```

For local source-checkout API server testing, rebuild dashboard assets before restarting the API server:

```bash
npm --prefix sky/dashboard install
npm --prefix sky/dashboard run build
sky api stop
sky api start
sky api status
```

For dashboard development mode, `sky/dashboard` uses `npm run dev` and defaults to local API server `http://127.0.0.1:46580`; set `SKYPILOT_API_SERVER_ENDPOINT` only for temporary manual debugging.

## Critical Code Paths

Be extra conservative in these areas:

- Managed jobs recovery: `sky/jobs/controller.py`, `sky/jobs/recovery_strategy.py`, and managed-job server/client/state modules. Watch for preemption, controller failures, retries, and async state races.
- Execution backend and provisioning: `sky/backends/cloud_vm_ray_backend.py`, `sky/backends/backend_utils.py`, `sky/provision/`, `sky/clouds/`, and provider utilities. Avoid blocking calls, heavy state in cloud objects, and cache invalidation mistakes.
- API server: `sky/server/`, `sky/server/requests/`, `sky/client/sdk.py`, and `sky/client/sdk_async.py`. Preserve latency, memory behavior, compatibility headers, request IDs, logging, auth, and dashboard expectations.
- CLI/SDK UX: `sky/client/cli/` and SDK modules. Keep flags and return behavior stable unless compatibility handling and documentation are updated.
- Schemas/protobuf/dashboard coupling: changes can require server constants, dashboard API client updates, generated proto outputs, and compatibility tests.

## Dependency And Packaging Changes

- Core and optional dependencies are managed from package setup files under `sky/setup_files/` and project metadata.
- Development/test pins live in `requirements-dev.txt`; keep comments when pins work around dependency or typing breakage.
- If adding cloud-specific packages, prefer extras-scoped dependencies so users do not pay for unneeded providers.
- Consider Python version support and both minimum/latest allowed dependency behavior.
- Run `python -m pip check` or equivalent when dependency changes are substantial.

## PR Handoff Checklist

A good SkyPilot PR description includes:

- Summary: one to three bullets describing the user-visible or maintainer-visible change.
- `Tested:` section with exact commands run and important manual verification.
- Explicit skipped checks when they are expensive or require credentials, GPUs, Kubernetes, Slurm, or cloud resources.
- Backward compatibility note for API/server/SDK/protobuf/dashboard changes.
- CI trigger suggestions for maintainers when local validation cannot cover cloud behavior, such as `/quicktest-core` or a focused `/smoke-test -k ...`.

## Difficult Maintainer Case Pattern

For a change touching server API, protobuf, and dashboard:

1. Identify request/response shape changes and whether `API_VERSION` plus compatibility branching are needed.
2. Update `.proto` sources and regenerate generated files.
3. Update server payload/serializer/client SDK/dashboard API client together.
4. Add or update focused unit tests for payload defaults, version gates, and SDK behavior.
5. Run proto generation diff check, targeted server/client tests, dashboard lint/test/build, and `bash format.sh --files` for touched Python files.
6. Restart a local API server only after rebuilds when manual dashboard/API validation is required.
7. Document old-client/new-server and new-client/old-server expectations in `Tested:` or PR notes.
