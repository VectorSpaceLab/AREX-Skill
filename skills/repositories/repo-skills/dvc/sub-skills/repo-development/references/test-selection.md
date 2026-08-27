# Focused Test Selection

Use this reference to choose narrow DVC tests after code edits. It intentionally avoids full-suite mandates and separates safe local checks from opt-in network/contract coverage.

## Always Start With Marker Safety

Default marker expression for local development:

```bash
-m "not studio and not needs_internet and not vscode"
```

Use this unless the change explicitly targets one of those contracts:

- `studio`: DVC Studio contract or live experiment reporting. Requires appropriate mocking or credentials; skip by default.
- `needs_internet`: network-dependent tests. On CI they may be rerun as flaky; skip locally unless the task is specifically about internet behavior.
- `vscode`: VSCode extension contract/output compatibility. Run only when changing rendering/plots/experiment output consumed by VSCode.

Remote backend markers such as `s3`, `gs`, `azure`, `gdrive`, `oss`, `ssh`, `webdav`, `webhdfs`, `hdfs`, `http`, and `real_hdfs` are controlled by custom pytest options in `tests/conftest.py`. Do not enable broad remote coverage unless the backend extra and service are intentionally available.

## Command and Parser Changes

Changed files:

- `dvc/cli/__init__.py`
- `dvc/cli/parser.py`
- `dvc/cli/command.py`
- `dvc/commands/<name>.py`
- `dvc/commands/<family>/*.py`

Suggested focused tests:

```bash
python -m pytest tests/unit/cli tests/unit/command -m "not studio and not needs_internet and not vscode"
```

For a single command, narrow further:

```bash
python -m pytest tests/unit/command/test_add.py tests/func/test_add.py -m "not studio and not needs_internet and not vscode"
```

What to check:

- Parser maps argv to the intended `Cmd*` class.
- Parsed defaults match existing command behavior.
- The command delegates expected keyword arguments to `self.repo`.
- Expected user errors return documented nonzero values and log DVC-style messages.
- Unknown arguments show command-specific help through `DvcParserError` behavior.

Native candidates: `tests/unit/cli`, `tests/unit/command`, and command-specific functional files in `tests/func/`.

## Repo Method Changes

Changed files:

- `dvc/repo/<area>.py`
- `dvc/repo/<area>/...`
- `dvc/repo/experiments/*.py`
- `dvc/repo/metrics/*.py`, `dvc/repo/params/*.py`, `dvc/repo/plots/*.py`

Suggested tests:

```bash
python -m pytest tests/unit/repo tests/func/test_<area>.py -m "not studio and not needs_internet and not vscode"
```

Common mappings:

- `dvc/repo/add.py` → `tests/unit/command/test_add.py`, `tests/func/test_add.py`.
- `dvc/repo/reproduce.py` → `tests/unit/repo/test_reproduce.py`, `tests/unit/command/test_repro.py`, `tests/func/repro`.
- `dvc/repo/status.py` → `tests/unit/command/test_status.py`, `tests/func/test_status.py`, `tests/func/test_data_status.py` when data status is involved.
- `dvc/repo/fetch.py`, `pull.py`, `push.py` → local remote functional tests first; route deeper remote semantics to the remotes/cache sub-skill.
- `dvc/repo/experiments/*.py` → `tests/unit/repo/experiments`, `tests/unit/command/test_experiments.py`, `tests/func/experiments` with marker exclusions.
- `dvc/repo/metrics`, `params`, `plots` → matching `tests/func/metrics`, `tests/func/params`, `tests/func/plots`, plus `tests/unit/command/test_metrics.py`, `test_params.py`, or `test_plots.py`.

## Python API and Filesystem Changes

Changed files:

- `dvc/api/*.py`
- `dvc/fs/*.py`
- `dvc/repo/open_repo.py`
- data-index or filesystem-facing helpers used by API reads.

Suggested tests:

```bash
python -m pytest tests/unit/test_api.py tests/unit/fs tests/func/api/test_data.py -m "not studio and not needs_internet and not vscode"
```

For `dvc.api.open()`/`read()` behavior, include:

- `tests/unit/test_api.py` for context-manager and mode validation.
- `tests/func/api/test_data.py` for tracked local/external repo reads, revisions, remotes, subrepos, and missing-path behavior.
- `tests/unit/fs/test_dvc.py` and `tests/unit/fs/test_dvcfs.py` when `DVCFileSystem` behavior changes.

If a change touches only public API docs or call-shape guidance, use the sibling `python-api` sub-skill for end-user semantics but keep maintainer test selection here.

## Config, Schema, and Parsing Changes

Changed files:

- `dvc/config.py`
- `dvc/config_schema.py`
- `dvc/schema.py`
- `dvc/parsing/**`
- serialize utilities.

Suggested tests:

```bash
python -m pytest tests/unit/test_config.py tests/func/test_config.py tests/func/parsing -m "not studio and not needs_internet and not vscode"
```

Add targeted command tests if parser or config options affect a specific command such as `remote`, `cache`, `stage`, or `params`.

## Stage, Output, and Pipeline Metadata Changes

Changed files:

- `dvc/stage/**`
- `dvc/output.py`
- `dvc/dvcfile.py`
- `dvc/dependency/**`
- `dvc/repo/stage.py`, `run.py`, `reproduce.py`.

Suggested tests:

```bash
python -m pytest tests/unit/stage tests/unit/output tests/unit/dependency tests/func/test_stage.py tests/func/repro -m "not studio and not needs_internet and not vscode"
```

When YAML/lock serialization changes, include `tests/unit/stage/test_serialize_pipeline_file.py`, `tests/unit/stage/test_serialize_pipeline_lock.py`, and relevant `tests/func/test_stage_load.py` or `tests/func/test_dvcfile.py` targets.

## Remote, Cache, and Optional Backend Changes

Changed files:

- `dvc/data_cloud.py`
- `dvc/cachemgr.py`
- `dvc/repo/fetch.py`, `pull.py`, `push.py`, `gc.py`
- `dvc/fs/**`
- optional-backend error handling.

Suggested local-first tests:

```bash
python -m pytest tests/unit/remote tests/func/test_remote.py tests/func/test_data_cloud.py tests/func/test_gc.py -m "not studio and not needs_internet and not vscode"
```

Only opt into remote-specific tests when the extra and service are available. The package extras declare backend dependencies, but default installs should not claim them. Prefer local remote fixtures before cloud backends.

## Studio and VSCode Contract Changes

Only run these when the change directly affects Studio or VSCode-facing output:

- Studio: `tests/integration/test_studio_live_experiments.py`, `tests/integration/plots/test_repo_plots_api.py`, selected `tests/unit/render/test_vega_converter.py` cases marked `studio`.
- VSCode: marked tests in `tests/integration/plots/test_plots.py`, `tests/func/experiments/test_show.py`, `tests/func/plots/test_diff.py`, and `tests/unit/render/test_convert.py`.

Do not include these in ordinary focused test suggestions.

## Safe No-Network Commands

These commands are normally safe because they run selected tests locally and skip opt-in markers:

```bash
python -m pytest tests/unit/command/test_add.py -m "not studio and not needs_internet and not vscode"
python -m pytest tests/unit/cli tests/unit/command/test_repro.py -m "not studio and not needs_internet and not vscode"
python -m pytest tests/unit/test_api.py tests/unit/fs/test_dvc.py tests/func/api/test_data.py -m "not studio and not needs_internet and not vscode"
python -m pytest tests/unit/test_config.py tests/func/test_config.py -m "not studio and not needs_internet and not vscode"
```

The bundled `scripts/select_tests.py` prints suggested commands from changed paths but never executes them.

## Difficult Synthetic Usability Cases

Use these as verification prompts for this sub-skill:

1. An agent changes `dvc/commands/add.py` to add an option that delegates to `Repo.add()`. It must identify parser/delegation unit tests, a focused functional test, and the marker expression that avoids Studio/network/VSCode tests.
2. An agent changes `dvc/api/data.py` so `dvc.api.open()` handles a missing local cache differently. It must select API, filesystem, and functional data tests, explain why `tests/integration/test_studio_live_experiments.py` is out of scope, and update troubleshooting notes if user-facing errors changed.
