# DVC Development Guide

This reference is for agents maintaining the DVC repository itself. It is not an end-user command guide.

## Verified Package Facts

- Distribution/import name: `dvc`.
- Observed package version in the inspection environment: `0.1.dev1+g8131c32c3`.
- Python requirement: `>=3.9`.
- Console script: `dvc = dvc.cli:main`.
- `dvc` also registers entry points for fsspec (`dvc.api:DVCFileSystem`), universal-pathlib DVC URL implementations, and PyInstaller hooks.
- `setuptools` package discovery excludes `tests` and `tests.*`, and uses `namespaces = false`.
- Optional storage extras include `azure`, `gdrive`, `gs`, `hdfs`, `oss`, `s3`, `ssh`, `webdav`, and `webhdfs`; do not assume any of them are installed unless the user installed that extra.
- Development extras are split: `tests`/`testing` for pytest support, `lint` for mypy and typing stubs, and `dev` as a broader bundle including many remotes.

For local development, an editable install with test extras is usually appropriate when the environment is dedicated to DVC work, for example `python -m pip install -e '.[tests]'`. Add optional remote extras only when the changed code or selected tests need them.

## Source Layout

- `dvc/cli/`: command-line entry point, parser helpers, completion, formatting, and global CLI behavior.
- `dvc/cli/__init__.py`: `parse_args()` and `main()`; handles logging, debug flags, analytics, DVC exceptions, parser errors, and cleanup of cached repos.
- `dvc/cli/parser.py`: imports command modules, defines the `COMMANDS` list, builds the top-level parser, and calls each command module's `add_parser()`.
- `dvc/cli/command.py`: base command classes. `CmdBase` changes to `args.cd`, constructs `Repo(uninitialized=..., _wait_for_lock=...)`, and wraps `run()` inside the repo context. `CmdBaseNoRepo` is for commands that do not need a DVC repo.
- `dvc/commands/`: CLI command modules. A typical command defines a `Cmd*` class and an `add_parser(subparsers, parent_parser)` function, then sets `parser.set_defaults(func=CmdClass)`.
- `dvc/commands/experiments/`, `dvc/commands/queue/`, `dvc/commands/ls/`: nested command families with their own subparsers.
- `dvc/repo/`: repository business logic for data tracking, stages, reproduction, status, push/pull/fetch, imports, metrics, params, plots, artifacts, and repository state.
- `dvc/repo/experiments/`: experiment logic backing `dvc exp`/`dvc experiments` commands.
- `dvc/api/`: public Python API (`open`, `read`, `get_url`, `DVCFileSystem`, metrics/params/artifacts/experiments helpers).
- `dvc/fs/`: filesystem abstractions, including DVC filesystem and backend integration points.
- `dvc/testing/`: reusable pytest fixtures and test harness code used by this repo and DVC plugin-style tests.
- `tests/unit/`: parser, command, repo, filesystem, config, render, utility, and API unit coverage.
- `tests/func/`: local functional workflows that exercise CLI/repo behavior with temporary DVC repos.
- `tests/integration/`: narrower integration/contract coverage, including Studio and VSCode-marked tests that should be opt-in.

## CLI Command Implementation Pattern

1. Add or update the command module under `dvc/commands/`.
2. Wire parser options in `add_parser()` using `dvc.cli.formatter`, `append_doc_link()`, and completion helpers where existing commands do.
3. Set the command class with `parser.set_defaults(func=CmdClass)`.
4. Keep parser validation in the command class when it depends on combinations of parsed arguments; return DVC-style nonzero codes for expected user errors.
5. Delegate repository behavior to `self.repo.<method>()` or a focused helper under `dvc/repo/`; avoid putting business logic entirely in the CLI layer.
6. Add unit tests for parser and delegation behavior under `tests/unit/command/test_<command>.py` or `tests/unit/cli/`.
7. Add functional tests under `tests/func/` only when the change needs a real temporary DVC repo workflow.

For example, `dvc/commands/add.py` validates incompatible `--to-remote`, `--out`, `--remote`, and `--remote-jobs` combinations, then calls `self.repo.add(...)`. `tests/unit/command/test_add.py` asserts parser selection and delegation arguments. `tests/func/test_add.py` covers local behavior with real temporary repo fixtures.

## Main Command Families

DVC exposes many command families. Current high-level families include `add`, `stage`, `repro`, `status`, `push`, `pull`, `fetch`, `remote`, `metrics`, `params`, `plots`, `experiments`/`exp`, `data`, `artifacts`, `get`, `import`, `config`, `root`, and `version`. When adding or editing one family, check both its `dvc/commands/` wrapper and the corresponding `dvc/repo/` implementation.

## Testing Fixtures and Local Repo Helpers

- `tests/conftest.py` imports fixtures from `dvc.testing.fixtures`, `tests/dir_helpers.py`, test remotes, and `tests/scripts.py`.
- It sets `DVC_TEST=true`, `DVC_IGNORE_ISATTY=true`, and `GIT_CONFIG_NOSYSTEM=1` to disable updater/analytics side processes, stabilize UI output, and isolate Git config.
- `tmp_dir` creates a temporary working directory and switches into it. Requesting `scm` or `dvc` fixtures makes `tmp_dir` initialize Git and/or DVC.
- `dvc` yields a `Repo` instance inside a context manager.
- `tmp_dir.gen()`, `tmp_dir.scm_gen()`, and `tmp_dir.dvc_gen()` create files and optionally add/commit them to Git/DVC.
- `tests/scripts.py` and `dvc/testing/scripts.py` provide tiny temporary helper scripts for tests. Treat them as reference-only when writing public repo skills; do not make runtime skill content execute them from the source repo.
- Remote fixtures default-enable only local-ish backends such as `hdfs`, `http`, and `webdav`; cloud credentials/backends are opt-in through CLI flags and markers.

## Lint, Type, and Test Configuration

- Pytest config lives in `pyproject.toml` with `testpaths = ["tests"]`, `xfail_strict = true`, coverage config, and warning filters that treat resource/unraisable/mock warnings strictly.
- Official markers include `needs_internet`, `studio`, and `vscode`; `tests/conftest.py` also registers remote markers from its `REMOTES` mapping.
- Ruff config selects broad rule families with preview rules enabled. Notable ignores include `S101` for asserts and several style/complexity rules. `tests/**` has extra per-file ignores for security/assertion-style test code.
- Mypy checks files under `dvc`, has `check_untyped_defs = true`, `no_implicit_optional = true`, `strict_equality = true`, `extra_checks = true`, and many ignored third-party import overrides.
- First-party imports for ruff/isort are `dvc`, `dvc_*`, and `tests`.
- `funcy.cached_property` is banned; use `from dvc.utils.objects import cached_property`.

## Safe Local Check Strategy

Prefer specific commands over broad suites:

- Parser/command wrapper: `python -m pytest tests/unit/cli tests/unit/command/test_<command>.py -m 'not studio and not needs_internet and not vscode'`.
- Repo method: `python -m pytest tests/unit/repo/test_<area>.py tests/func/test_<area>.py -m 'not studio and not needs_internet and not vscode'`.
- API open/read/filesystem: `python -m pytest tests/unit/test_api.py tests/unit/fs tests/func/api/test_data.py -m 'not studio and not needs_internet and not vscode'`.
- Reproduction/stage behavior: `python -m pytest tests/unit/command/test_repro.py tests/unit/repo/test_reproduce.py tests/func/repro -m 'not studio and not needs_internet and not vscode'`.
- Config/schema behavior: `python -m pytest tests/unit/test_config.py tests/func/test_config.py -m 'not studio and not needs_internet and not vscode'`.

Do not run full tests by default. The full suite can be slow, may require optional remotes, and includes contract tests that are intentionally marker-gated.

## Contribution Pitfalls

- Do not import from `tests.*` in runtime code because tests are not packaged.
- Do not assume optional remote packages are installed; preserve `RemoteMissingDepsError` behavior and user-facing hints.
- Do not bypass `CmdBase` repo lifecycle or `Repo.open()`/context cleanup patterns.
- Keep command parser errors granular: `DvcParser.parse_args()` tries to show command-specific help for unknown flags.
- Keep functional tests self-contained with `tmp_dir` helpers instead of relying on global sample repos.
- Avoid hidden network or Studio calls in default tests; use markers and mocks.
- Be careful with `.dvcignore`, config validation, and stage path logic; small path handling changes often need both unit and functional tests.
