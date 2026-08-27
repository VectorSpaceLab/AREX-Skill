<!-- SPDX-License-Identifier: Apache-2.0 -->

# Development Workflows

Use this reference to choose safe commands for Airflow contribution work. Commands intentionally use repository-relative paths and placeholders, never machine-local paths.

## Setup Baseline

- Install `prek` with `uv tool install prek` and enable hooks with `prek install`.
- Install the Breeze shim with `scripts/tools/setup_breeze` when Breeze is needed.
- Use `uv` for local workspace environments. The workspace lockfile is committed and should be regenerated only through Airflow's normal `uv lock` / `uv sync` workflow.
- Prefer the smallest `uv sync` scope that covers the touched package. For a provider, sync that provider package rather than the full monorepo when possible.
- If Docker networking is broken during Breeze work, `docker network prune` is the standard cleanup hint.

## Host Command Rule

Do not run host `pytest`, `python`, or `airflow` directly while working on the Airflow repository. Use one of these instead:

```bash
uv run --project <PROJECT> pytest path/to/test.py::test_name -xvs
uv run --project <PROJECT> python dev/my_script.py
breeze run pytest path/to/test.py::test_name -xvs
breeze run airflow dags list
```

Use `breeze run ...` when local `uv` cannot satisfy system dependencies, when the test needs a service/backend, when CI parity matters, or for provider mypy. Use `uv run --project <PROJECT>` for fast local targeted tests and standard-library-only dev scripts.

## Python Edit Loop

After each Python file you create or edit:

```bash
uv run ruff format <file_path>
uv run ruff check --fix <file_path>
```

Then run the most specific tests that prove the changed behavior. Airflow expects tests to cover exactly the changed behavior: no missing regression coverage and no padding tests for unchanged logic.

## Common Test Commands

```bash
# Single test or test file in a workspace project.
uv run --project airflow-core pytest airflow-core/tests/unit/... -xvs
uv run --project task-sdk pytest task-sdk/tests/... -xvs
uv run --project scripts pytest scripts/tests/ -xvs

# Breeze fallback or CI-parity run.
breeze run pytest airflow-core/tests/unit/... -xvs

# Core and provider suites.
breeze testing core-tests --skip-db-tests --use-xdist
breeze testing providers-tests --test-type "Providers[standard]"

# Integration-oriented suites.
breeze testing airflow-ctl-tests
breeze testing task-sdk-tests
breeze testing helm-tests --use-xdist
```

SQLite is the default backend. Use `--backend postgres` or `--backend mysql` only when the changed behavior depends on that database.

## Static Checks

- Fast regular checks: `prek run --from-ref <target_branch> --stage pre-commit`.
- Slower manual checks: `prek run --from-ref <target_branch> --stage manual`.
- Ruff-only lint: `prek run ruff --from-ref <target_branch>`.
- Ruff-only format: `prek run ruff-format --from-ref <target_branch>`.
- Non-provider mypy: `prek run mypy-<project> --all-files`, such as `mypy-airflow-core`, `mypy-task-sdk`, `mypy-scripts`, or `mypy-shared-<dist>`.
- Provider mypy: `breeze run mypy path/to/provider/code`.

Non-provider mypy hooks create dedicated environments and caches under repository build directories and do not mutate the normal project virtualenv. Clear mypy caches with:

```bash
breeze down --cleanup-mypy-cache
```

## Selective Checks Mental Model

Airflow CI uses changed files to conservatively decide what to run. For a quick local first pass, use the bundled recommender:

```bash
uv run skills/apache-airflow/sub-skills/contribution-tooling/scripts/select_test_command.py <changed-file> [...]
```

For authoritative CI-style outputs once a commit reference exists, run:

```bash
breeze selective-checks --commit-ref <commit_with_squashed_changes>
```

Conservative rules distilled from Airflow selective checks:

- Push, schedule, workflow dispatch, missing commit ref, root `pyproject.toml` changes, or `generated/provider_dependencies.json` changes can force all tests and all versions.
- Environment files force broad testing: `.github/workflows`, `dev/breeze/src`, `dev/breeze` lock/project files, most `dev/*.py`, Dockerfiles, `scripts/ci`, `scripts/docker`, `scripts/in_container`, and generated provider dependencies.
- API contract/codegen files force broad testing: generated public OpenAPI specs and generated clients.
- `providers/git/src/`, `providers/standard/src/`, and core test utilities currently force broad testing.
- UI-only source changes can skip Python unit tests but still need UI checks.
- Provider tests are selected on the `main` target branch; release branches suppress provider matrix selection.
- Docs builds are selected for docs paths and for source changes that feed generated docs, including providers, Task SDK, core, `airflowctl`, Docker stack docs, chart docs, and provider summary docs.

## Documentation Builds

Documentation lives close to each distribution:

- Core: `airflow-core/docs`.
- Providers: `providers/**/docs`.
- Helm chart: `chart/docs`.
- Task SDK: `task-sdk/docs`.
- `airflowctl`: `airflow-ctl/docs`.
- Docker stack: `docker-stack-docs`.
- Provider summary: `providers-summary-docs`.

Local docs build pattern:

```bash
uv run --group docs build-docs [package ...]
```

Breeze docs build pattern:

```bash
breeze build-docs [package ...]
```

Use Breeze if local docs dependencies fail to install. Provider docs can be built by provider id, and related provider docs may need to build together when cross-links or inventories interact.

## Git Remotes and PR Prep

Airflow expects `upstream` to point at the canonical Apache Airflow repository and `origin` to point at the contributor fork. Before any remote-based command, inspect remotes:

```bash
git remote -v
```

If names do not match the convention, do not silently use the wrong remote names. Surface the mismatch and ask before renaming or adding remotes.

Before opening a PR:

1. Check for existing open PRs addressing the same issue or keywords.
2. Review the full diff against the target branch and remove unrelated changes.
3. Check the code-review checklist: architecture boundaries, DB correctness, code quality, tests, API correctness, UI rules, generated files, and AI-generated-code signals.
4. Run targeted tests, fast static checks, and any manual checks appropriate to the change.
5. Run selective checks to understand CI blast radius.
6. Rebase on the latest target branch before pushing.
7. Push only to `origin`, never to `upstream` or `main` directly.

## GitHub Message and PR Conventions

- Commit and PR titles use imperative mood and plain wording. Do not use Conventional Commit prefixes such as `fix:`, `feat:`, or `chore:`.
- Airflow accepts area tags such as `UI:` or `API:` when they are customary.
- Commit bodies explain why the change is made, not what the diff already shows.
- If an agent drafts a GitHub issue, comment, PR review, or discussion reply, append the required AI attribution footer before posting.
- Do not tag individual contributors unless a human explicitly authorizes it.
- If a fix is imminent, open the PR rather than filing a duplicate issue. File a tracking issue only for deferred workaround/mitigation work, and link the full issue URL at the workaround site.
