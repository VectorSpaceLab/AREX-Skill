<!-- SPDX-License-Identifier: Apache-2.0 -->

# Airflow Monorepo Map

This reference helps future agents place a change in the right Airflow distribution, apply nested rules, and choose the first validation target.

## Workspace Shape

Airflow is a `uv` workspace monorepo with multiple Python distributions and non-Python components. The installed package facts verified for this skill are:

- `apache-airflow` 3.3.0 meta distribution.
- `apache-airflow-core` 3.3.0 core distribution.
- `apache-airflow-task-sdk` 1.3.0 Task SDK distribution.
- `apache-airflow-ctl` 0.1.5 CLI distribution.
- `apache-airflow-providers-standard` 1.15.0 standard provider distribution.

Important CLI groups verified for installed packages:

- `airflow`: `api-server`, `assets`, `backfill`, `config`, `connections`, `dag-processor`, `dags`, `db`, `info`, `jobs`, `plugins`, `pools`, `providers`, `scheduler`, `standalone`, `state-store`, `tasks`, `triggerer`, `variables`, `version`.
- `airflowctl`: `assets`, `auth`, `backfill`, `config`, `connections`, `dagrun`, `dags`, `jobs`, `plugins`, `pools`, `providers`, `variables`, `version`, `xcom`.

## Primary Ownership Areas

- `airflow-core/src/airflow/`: core scheduler, API server, Dag processor, models, migrations, CLI, config, security, plugins, assets, serialization, and React UI under `airflow-core/src/airflow/ui/`.
- `airflow-core/tests/`: core unit and system tests. Test paths generally mirror source paths.
- `airflow-core/docs/`: core Airflow documentation.
- `task-sdk/src/airflow/sdk/`: lightweight SDK for Dag authoring and task execution runtime.
- `task-sdk/tests/` and `task-sdk-integration-tests/`: Task SDK unit and integration coverage.
- `task-sdk/docs/`: Task SDK documentation.
- `airflow-ctl/src/airflowctl/`: standalone remote CLI that talks to a running Airflow instance through the Public API.
- `airflow-ctl/tests/`: `airflowctl` tests.
- `providers/<provider>/`: one provider distribution per tree, with `pyproject.toml`, `provider.yaml`, `src/`, `docs/`, and `tests/`.
- `providers/standard/`: standard provider, currently high blast radius because selective checks treat changes under `providers/standard/src/` as full-test triggers.
- `shared/<dist>/`: small shared Python distributions symlinked or bundled into consumers such as core and Task SDK.
- `chart/`: Helm chart templates, chart docs, values schemas, and Helm tests.
- `docker-stack-docs/`: Docker image/stack documentation.
- `dev/breeze/`: Breeze development and CI reproduction tooling.
- `scripts/ci/prek/`: Python hook scripts for `prek`; shared helpers live in `common_prek_utils.py`.
- `generated/`, `clients/gen`, `openapi-gen/`, generated OpenAPI specs, and generated provider dependency files: outputs owned by generation hooks, not freehand edit targets.

## Nested Instruction Hotspots

Always check for an applicable `AGENTS.md` before editing below these paths:

- Providers: each provider is an independent package. Keep `provider.yaml`, docs, and tests in sync. Never add provider newsfragments; update `docs/changelog.rst` only for important user-visible provider changes. Never blindly forward `Connection.extra` into hooks, operators, clients, or arbitrary kwargs; allowlist explicit extras.
- UI: TypeScript strict mode is enforced. Use configured path aliases. Use `react-icons`, generated OpenAPI clients, reusable components in `src/components/`, and no manual `useMemo` or `useCallback`. Do not write raw `axios` calls to API endpoints.
- `dev/`: new scripts must be standalone Python scripts with inline script metadata after the Apache license header, and documentation should invoke them with `uv run`.
- `scripts/ci/prek/`: hook scripts are Python, should reuse `common_prek_utils.py`, and Breeze-dependent hooks should call the shared Breeze helper rather than shelling out directly.
- `registry/`: minimal JavaScript, semantic HTML/CSS, no framework additions, no utility class style drift.
- Shared code under `_shared/`: follow the nested shared-library instructions where present.

## Architecture Boundaries To Preserve

- Users author Dags with `airflow.sdk`.
- Dag file processing parses user files in separate processes and stores serialized Dags.
- The scheduler reads serialized Dags and must never run user code.
- Workers execute tasks through the Task SDK and communicate through the Execution API; they must not access the metadata database directly.
- The API server owns client/database interaction and serves the React UI.
- Triggerer and Dag File Processor guardrails steer code through the Execution API, but those guardrails are not a malicious-code sandbox.
- Providers should use public SDK and API surfaces; do not import task-runner internals or supervisor plumbing.

## Test Ownership Map

Use the most specific test first, then broaden:

- Core Python source: mirror under `airflow-core/tests/unit/`; use `uv run --project airflow-core pytest <test> -xvs` when local dependencies are enough, or `breeze run pytest <test> -xvs` when system services or Breeze parity are needed.
- FastAPI public/UI API routes: `airflow-core/tests/unit/api_fastapi/` and API selective type; generated OpenAPI spec may change through `prek`.
- Execution API version changes: tests under `airflow-core/tests/unit/api_fastapi/execution_api/versions/head` and version-specific folders.
- Metadata DB migrations: migration CI commands from the workflow plus migration reference updates through `prek update-migration-references --all-files`.
- Providers: provider-local `tests/unit/`, `tests/integration/`, and selected `tests/system/`; CI provider tests use `breeze testing providers-tests --test-type "Providers[provider]"` on `main`.
- Task SDK: `task-sdk/tests/` and `task-sdk-integration-tests/`; integration runs through Breeze.
- `airflowctl`: `airflow-ctl/tests/` plus `breeze testing airflow-ctl-tests` or integration tests when a running Airflow instance is involved.
- UI: UI unit/build checks under `airflow-core/src/airflow/ui/`; e2e tests only when UI e2e paths or explicit CI labels demand them.
- Helm: `chart/tests/`; use `breeze testing helm-tests --use-xdist` and select test type when possible.
- Scripts and prek hooks: `scripts/tests/`, especially `scripts/tests/ci/prek/` for hook logic.

## Source Evidence Used

This reference distilled the root and nested `AGENTS.md` files, workspace package metadata, contribution docs, code-review checklist, selective-checks documentation and implementation, provider conventions, UI instructions, and verified installed-package CLI facts. It is self-contained; future agents should not need to open the original evidence just to apply these rules.
