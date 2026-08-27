# DVC Repository Development Troubleshooting

Use this when local development checks fail while editing the DVC repository.

## Import or Editable Install Failures

Symptoms:

- `ModuleNotFoundError: No module named 'dvc'`.
- Running `dvc` uses an installed release instead of the checkout.
- Tests cannot import `dvc.testing` fixtures.

Checks and fixes:

- Verify the environment has an editable install for this checkout: `python -m pip install -e '.[tests]'` in a dedicated development environment.
- Do not add imports from `tests.*` into runtime code; `pyproject.toml` excludes `tests` and `tests.*` from packaged modules.
- Use `python -m pytest ...` from the repository root so pytest sees local fixtures and config.
- If `dvc` command behavior differs from source edits, inspect `python -c "import dvc, dvc.cli; print(dvc.__file__, dvc.cli.__file__)"` to confirm the checkout is imported.

## Optional Remote Dependency Failures

Symptoms:

- `RemoteMissingDepsError` for `s3://`, `gs://`, `azure://`, `ssh://`, `webdav://`, `webhdfs://`, `hdfs://`, `oss://`, or another backend.
- CLI output suggests installing `dvc[proto]` or a `dvc-proto` conda package.
- Remote-marked tests are skipped or fail because service credentials are unavailable.

Checks and fixes:

- Do not claim optional extras are installed by default. Package extras include `azure`, `gdrive`, `gs`, `hdfs`, `oss`, `s3`, `ssh`, `webdav`, and `webhdfs`.
- For generic command/repo logic, prefer local remote fixtures and skip cloud credentials.
- For backend-specific work, install only the needed extra in a dedicated environment and run the specific backend tests with the required pytest enable flag.
- Preserve user-facing `RemoteMissingDepsError` hints in `dvc/cli/__init__.py`; tests in `tests/unit/cli/test_main.py` assert this behavior.

## Flaky, Network, Studio, and VSCode Tests

Symptoms:

- Tests unexpectedly contact network services.
- Studio tests require tokens or contract-specific mocks.
- VSCode-marked tests fail after output/schema changes.

Checks and fixes:

- Add `-m "not studio and not needs_internet and not vscode"` to default focused local runs.
- `needs_internet` tests may be rerun as flaky on CI; do not treat that marker as safe local default.
- Skip `tests/integration/test_studio_live_experiments.py` unless the task explicitly targets Studio live experiment behavior and the environment has the required credentials/mocks.
- Run `vscode` marker tests only when changing output consumed by the VSCode extension, especially plots or experiment table/rendering data.

## CLI Parser and Command Errors

Symptoms:

- `dvc <command> --new-flag` reports `unrecognized arguments`.
- A command's help output is generic instead of command-specific.
- `args.func` is missing or points to the wrong class.
- A command accesses `self.repo` when it should not require a DVC repo.

Checks and fixes:

- Ensure the command module is imported in `dvc/cli/parser.py` and included in `COMMANDS` or the appropriate nested command list.
- Ensure `add_parser()` calls `parser.set_defaults(func=CmdClass)`.
- Use `CmdBaseNoRepo` for commands that must work outside a DVC repository; ordinary `CmdBase` constructs `Repo(...)` after changing to `args.cd`.
- Keep parser validation and DVC-style return codes consistent with nearby commands.
- Add or update `tests/unit/command/test_<command>.py` to assert `parse_args([...]).func` and delegated keyword arguments.

## Config, Schema, and Warning Failures

Symptoms:

- Tests fail because warnings are treated as errors.
- Config changes raise `ConfigError`, validation errors, or unexpected `voluptuous` messages.
- Remote/cache config tests fail after schema edits.

Checks and fixes:

- Pytest treats `ResourceWarning`, unraisable exceptions, and pytest-mock warnings strictly. Close files, sockets, repos, and temporary resources.
- Config schema changes should update both `dvc/config_schema.py` or `dvc/schema.py` and focused tests under `tests/unit/test_config.py` and `tests/func/test_config.py`.
- For remote settings, check CLI-facing behavior through `dvc/commands/remote.py` and local remote functional tests before enabling cloud remotes.
- If a test relies on Git config, remember `tests/conftest.py` isolates `HOME`, `XDG_CONFIG_HOME`, and `GIT_CONFIG_NOSYSTEM`.

## DVC Repo Fixture Mistakes

Symptoms:

- `tmp_dir` methods say a fixture is missing.
- A test accidentally writes into the original checkout.
- DVC/Git state is missing even though the test assumes it exists.
- Cached repo state leaks between tests.

Checks and fixes:

- Request `scm` when using `tmp_dir.scm_gen()` or Git assertions.
- Request `dvc` when using `tmp_dir.dvc_gen()`, `tmp_dir.add_remote()`, or `tmp_dir.dvc`.
- Use `tmp_dir.gen()` for local files, `tmp_dir.scm_gen()` for Git-tracked files, and `tmp_dir.dvc_gen()` for DVC-tracked files.
- Use descriptive file names in each test instead of depending on global sample repos.
- `tests/conftest.py` automatically calls `clean_repos()` and enables UI; avoid adding hidden global state that bypasses these fixtures.

## API and Filesystem Behavior Changes

Symptoms:

- `dvc.api.open()` errors before entering a `with` block.
- Write modes fail for `dvc.api.open()`.
- `DVCFileSystem` reads dirty workspace data differently from API expectations.
- External repo reads fail with missing cache, subrepo, or SCM errors.

Checks and fixes:

- `dvc.api.open()` intentionally returns a context manager and raises `AttributeError` if used like an opened file before `with`.
- Only read modes are supported by `dvc.api.open()`.
- Include `tests/unit/test_api.py`, `tests/unit/fs/test_dvc.py`, `tests/unit/fs/test_dvcfs.py`, and `tests/func/api/test_data.py` for API read/open changes.
- For end-user semantics, route to the `python-api` sub-skill; for maintainer edits, keep test selection and source layout guidance here.

## Lint and Type Failures

Symptoms:

- Ruff rejects imports, test style, or banned APIs.
- Mypy fails on untyped code paths or optional imports.

Checks and fixes:

- Ruff treats `dvc`, `dvc_*`, and `tests` as first-party import groups.
- Tests have broader per-file ignores than runtime code; do not copy test-only style into `dvc/` modules.
- `funcy.cached_property` is banned; use `dvc.utils.objects.cached_property`.
- Mypy checks `dvc` with `check_untyped_defs`, `strict_equality`, `extra_checks`, and no implicit optional. Prefer explicit `Optional[...]`/`| None` handling and keep third-party import typing behind configured overrides.
