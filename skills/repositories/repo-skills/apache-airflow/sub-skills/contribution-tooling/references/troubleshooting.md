<!-- SPDX-License-Identifier: Apache-2.0 -->

# Contribution Tooling Troubleshooting

Use this reference when Airflow contribution commands fail or when a future agent is unsure which recovery path is safe.

## Breeze Is Missing or Stale

Symptoms:

- `breeze` is not found.
- Breeze uses the wrong source checkout.
- Breeze or Docker-based `prek` hooks say the CI image is stale.

Safe recovery:

```bash
scripts/tools/setup_breeze
breeze ci-image build
```

The Breeze shim should resolve Breeze from the current worktree. Rebuild the CI image after dependency changes or when hooks explicitly say the image is out of date.

## Missing or Wrong `uv`

Symptoms:

- `uv` is missing.
- A hook warns that `uv` is below the version pinned by the repository.
- Local workspace sync behaves differently from CI.

Safe recovery:

```bash
uv self update
uv sync --project <PROJECT>
uv tool install prek
```

Some mypy hooks prefer the project-pinned `uv` from the workspace environment and fall back to `uv` on `PATH` with a warning. If the workspace environment is absent, sync the relevant project first.

## Direct Host Pytest Rule

Do not run `pytest`, `python`, or `airflow` directly from the host while validating Airflow repository changes. Direct host commands can silently use the wrong packages, system dependencies, configuration, database, or CLI entry points.

Use:

```bash
uv run --project <PROJECT> pytest path/to/test.py::test_name -xvs
uv run --project <PROJECT> python dev/my_script.py
breeze run pytest path/to/test.py::test_name -xvs
breeze run airflow dags list
```

If `uv run` fails because a provider or docs dependency needs a system package, fall back to Breeze rather than installing broad host dependencies.

## Docker or Network Problems

Symptoms:

- Breeze cannot create or attach Docker networks.
- Integration tests fail before the test body starts due to Docker networking.

Safe recovery:

```bash
docker network prune
```

Ask before destructive Docker cleanup beyond network pruning.

## Mypy Cache or Environment Drift

Symptoms:

- `mypy-*` hooks fail with stale cache errors.
- Provider mypy behaves differently from non-provider mypy.
- A hook environment seems corrupted.

Safe recovery:

```bash
breeze down --cleanup-mypy-cache
prek run mypy-<project> --all-files
breeze run mypy path/to/provider/code
```

Non-provider mypy hooks use dedicated local environments and caches under repository build directories. Provider mypy runs through Breeze and may require a current CI image.

## Generated File Drift

Symptoms:

- OpenAPI generated spec changed unexpectedly.
- Provider dependency files are out of sync.
- Migration references or filenames fail checks.
- Task SDK or UI generated clients look stale.

Safe recovery patterns:

```bash
prek --all-files
prek update-providers-dependencies --all-files
prek update-migration-references --all-files
```

Do not patch generated output by hand unless the file documents a preserved input section, such as provider dependency sections that survive regeneration.

## Provider Docs or Dependency Failures

Symptoms:

- Provider docs fail because optional dependencies are missing.
- A provider dependency change does not appear in generated dependency metadata.
- Lowest-direct-dependency checks cannot install an optional dependency.

Safe recovery:

```bash
uv sync --package apache-airflow-providers-<provider>
prek update-providers-dependencies --all-files
breeze ci-image build
breeze build-docs <provider>
```

If a provider has dependencies that cannot be installed by default, keep them as optional extras and use the documented pre-extras manifest mechanism. Do not convert difficult optional dependencies into unconditional runtime dependencies just to satisfy CI.

## Docs Build Problems

Symptoms:

- `uv run --group docs build-docs` fails on system libraries.
- Sphinx inventory or cross-package references fail.
- Provider docs need multiple packages built together.

Safe recovery:

```bash
breeze build-docs <package>
breeze build-docs --doc-only --clean <package>
uv run --group docs build-docs PACKAGE_1 PACKAGE_2
```

Use Breeze when local docs dependencies are too difficult to install. Build related packages together when cross-links require it.

## Selective Checks Seem Too Broad or Too Narrow

Symptoms:

- CI runs more jobs than expected.
- A path change does not trigger the expected suite.
- A PR changes selective-check logic.

Safe recovery:

```bash
breeze selective-checks --commit-ref <commit_with_squashed_changes>
```

Remember that selective checks are conservative: environment files, root `pyproject.toml`, provider dependency generation, API contract changes, standard provider source, git provider source, and test utilities can intentionally force broad testing. If the selective-check implementation changes, update the docs and tests for selective checks in the same PR.

## API or OpenAPI Drift

Symptoms:

- API tests pass but generated OpenAPI spec changes.
- UI generated clients no longer match API responses.
- Execution API schema changes break old clients.

Safe recovery:

```bash
prek --all-files
uv run --project airflow-core pytest airflow-core/tests/unit/api_fastapi/... -xvs
```

For Execution API schema or behavior changes, add Cadwyn version migrations and tests for old and new versions. For public API route changes, verify permissions, response models, error mapping, pagination/filtering, and generated docs.

## Migration Conflicts

Symptoms:

- Rebase conflicts in migration files or migration reference docs.
- Two migrations have the same generated sequence/version prefix.

Safe recovery:

1. Resolve unrelated code conflicts first.
2. Run:

```bash
prek update-migration-references --all-files
```

3. Stage the generated migration/reference updates and continue the rebase.

Do not import ORM classes into migration files. If a migration rebuilds parent tables on SQLite, keep foreign-key disabling around the whole DDL/DML body.

## PR Preparation Problems

Symptoms:

- Remote names do not match Airflow conventions.
- A PR overlaps an existing open PR.
- A workaround lacks a tracking issue.

Safe recovery:

- Inspect remotes with `git remote -v`; use `upstream` for Apache Airflow and `origin` for the contributor fork. Ask before renaming remotes.
- Search open PRs before starting or opening a new PR. If another PR already solves the issue, prefer review/build-on unless your approach is genuinely different.
- For partial fixes or workarounds, open a tracking issue first and link its full URL in code comments at the workaround site and in the PR body.

## Common Anti-Patterns To Stop

- Running host `pytest`, `python`, or `airflow` directly.
- Adding a newsfragment for a provider, `airflow-ctl`, tests-only change, CI-only change, or internal refactor.
- Hand-editing generated OpenAPI clients or generated specs.
- Adding a new provider connection option by forwarding all extras.
- Adding a new `AirflowException` raise in touched code.
- Adding direct DB access to remote CLI commands or task execution paths.
- Changing selective-check rules without updating selective-check docs and tests.
