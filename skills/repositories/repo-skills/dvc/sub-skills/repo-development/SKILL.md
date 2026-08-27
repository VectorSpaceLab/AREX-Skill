---
name: repo-development
description: "Maintain the DVC repository itself: source layout, CLI command
  internals, focused test selection, optional dependency boundaries, lint/type
  config, and contribution pitfalls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DVC Repository Development

Use this sub-skill when an agent is editing the DVC codebase rather than using DVC in an end-user project. It covers package layout, command implementation patterns, focused tests, optional dependency boundaries, and local quality checks for safe maintainer workflows.

## Start Here

1. Identify the changed surface: CLI parser/command class, `Repo` method, Python API helper, filesystem/remote backend, config/schema, testing fixture, or docs-only change.
2. Read `references/development-guide.md` for the code layout, entry points, packaging facts, and command implementation flow before editing.
3. Use `scripts/select_tests.py` with changed file paths to propose focused pytest targets and marker exclusions without running tests.
4. Read `references/test-selection.md` before running tests; prefer narrow unit/functional targets and skip opt-in network, Studio, and VSCode contract markers unless explicitly needed.
5. Read `references/troubleshooting.md` when imports, optional backends, parser errors, config validation, or DVC test fixtures fail.

## Maintainer Defaults

- Console entry point is `dvc = dvc.cli:main`; in this checkout `dvc.cli` is a package and the main implementation is `dvc/cli/__init__.py`.
- CLI commands are registered from `dvc/cli/parser.py`, implemented under `dvc/commands/`, and usually delegate business logic to `dvc/repo/`.
- Tests are not part of setuptools packages (`tests`, `tests.*` excluded; namespaces disabled), so runtime code must not import `tests.*`.
- Optional remote extras such as `azure`, `gdrive`, `gs`, `hdfs`, `oss`, `s3`, `ssh`, `webdav`, and `webhdfs` are not installed by default.
- Do not run the full test suite by default; start with focused paths and marker exclusions.

## Bundled References

- `references/development-guide.md` explains source layout, package metadata, command wiring, editable install expectations, and local quality tooling.
- `references/test-selection.md` maps common changed files to focused test targets, marker policy, and safe no-network commands.
- `references/troubleshooting.md` covers dependency/import failures, parser errors, optional extras, flaky network/Studio tests, config warnings, and fixture mistakes.
- `scripts/select_tests.py` prints suggested pytest targets and marker exclusions from changed paths; it never imports DVC or runs pytest.

## Routing Notes

- Route end-user data tracking, stages, `dvc repro`, and pipeline operation to `../data-and-pipelines/SKILL.md`.
- Route end-user remotes, cache behavior, `push`/`pull`/`fetch`, and storage credentials to `../remotes-and-cache/SKILL.md`.
- Route metrics, params, and plots usage to `../metrics-params-plots/SKILL.md`.
- Route experiment workflows to `../experiments/SKILL.md`.
- Route public Python API usage (`dvc.api`, `DVCFileSystem`, `Repo` automation) to `../python-api/SKILL.md` unless the task is about changing those APIs inside the DVC repo.
