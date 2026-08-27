# DVC Data and Pipeline Workflows

These recipes cover core DVC workflows for package `dvc` version `0.1.dev1+g8131c32c3`. The installed console entry point is `dvc = dvc.cli:main`; use the CLI from a DVC project root unless a command explicitly accepts another target path. Python requires `>=3.9`.

## Preflight Checklist

- Verify context: `dvc root` should print the repository root. If it fails, initialize or move to a DVC project before using project commands.
- Inspect current state: `dvc status`, `dvc data status --json`, and `git status --short` reveal whether DVC metadata and workspace data are already changed.
- Avoid unintended execution: prefer `dvc repro --dry <target>` and the bundled `scripts/plan_dvc_pipeline.py` for planning before running commands that execute user code.
- Keep DVC metadata in Git: `.dvc` files, `dvc.yaml`, `dvc.lock`, `.dvcignore`, `.gitignore`, config changes, and code/param files usually need Git review.

## Track Data With `dvc add`

Use `dvc add` for source data or large artifacts that are not produced by a DVC stage.

```bash
dvc add data/raw.csv
dvc add images/
dvc add --glob 'data/*.csv'
dvc add --no-commit data/large-unverified.bin
dvc add --out tracked/input.csv downloads/raw.csv
dvc status tracked/input.csv.dvc
```

Important flags:

- `--no-commit` writes metadata without putting data into the DVC cache; follow with `dvc commit <target>` when the contents are ready to cache.
- `--glob` expands shell-style wildcard targets.
- `--out <path>` writes a single target to a different tracked output path and cannot be combined with multiple targets, `--glob`, or `--no-commit`.
- `--to-remote`, `--remote`, and `--remote-jobs` are remote workflows; use `../remotes-and-cache/SKILL.md` for setup and storage details.
- `--force` allows overwriting a local file or folder; inspect `dvc status` and Git status first.
- `--no-relink` avoids recreating workspace cache links after adding.

Repo API equivalent:

```python
from dvc.repo import Repo

repo = Repo()
stages = repo.add(
    ["data/raw.csv"],
    no_commit=False,
    glob=False,
    out=None,
    remote=None,
    to_remote=False,
    remote_jobs=None,
    force=False,
    relink=True,
)
```

`Repo.add()` returns created or updated stage objects. It raises DVC exceptions for missing files, overlapping outputs, duplicate outputs, invalid option combinations, or cache-link failures.

## Build A Pipeline With `dvc stage add`

Use `dvc stage add` for commands that can be reproduced from declared dependencies and outputs. The command requires `-n/--name` and accepts the command remainder after DVC flags.

```bash
dvc stage add -n featurize \
  -d src/featurize.py \
  -d data/raw.csv \
  -p params.yaml:featurize \
  -o data/features.parquet \
  python src/featurize.py --config params.yaml

dvc stage add -n train \
  -d src/train.py \
  -d data/features.parquet \
  -p params.yaml:train.lr,train.epochs \
  -o models/model.pkl \
  -M metrics/train.json \
  --plots plots/loss.json \
  python src/train.py
```

Common declarations:

- Dependencies: `-d/--deps <path>` for code, data, configs, and other files that should trigger reruns.
- Parameters: `-p/--params [<filename>:]<params_list>` for parameter subsets; DVC parses repeated values such as `params.yaml:train.lr,train.epochs`.
- Cached outputs: `-o/--outs <path>` for normal DVC-cached outputs.
- No-cache outputs: `-O/--outs-no-cache <path>` for outputs DVC should track in metadata but not store in the DVC cache.
- Persisted outputs: `--outs-persist` and `--outs-persist-no-cache` for outputs not removed before repro.
- Metrics/plots declarations: `-m/--metrics`, `-M/--metrics-no-cache`, `--plots`, and `--plots-no-cache` mark outputs for reporting; use `../metrics-params-plots/SKILL.md` for report interpretation.
- Working directory: `-w/--wdir <path>` runs the command relative to a repo-contained directory.
- Stage behavior: `--always-changed` forces the stage to be treated as changed; `--desc <text>` stores human context; `--run` executes immediately after creating the stage.
- Existing names: `--force` overwrites an existing stage definition.

Repo API equivalents:

```python
from dvc.repo import Repo

repo = Repo()
stage = repo.run(
    name="train",
    cmd="python src/train.py",
    deps=["src/train.py", "data/features.parquet"],
    params=["params.yaml:train.lr,train.epochs"],
    outs=["models/model.pkl"],
    metrics_no_cache=["metrics/train.json"],
    plots=["plots/loss.json"],
    no_exec=True,
    no_commit=False,
    run_cache=True,
    force=True,
)
```

`Repo.run()` creates a pipeline stage and writes `dvc.yaml`; with `no_exec=True` it records the stage without running the command and does not update the lock from execution. Internally it parses params and delegates stage creation through `Repo.stage.create()`.

## Reproduce Pipelines Safely

Start with a dry run:

```bash
dvc repro --dry train
dvc repro --dry dvc.yaml:train
dvc repro --dry --pipeline train
dvc repro --dry --downstream featurize
```

Then execute only when the target scope is clear:

```bash
dvc repro train
dvc repro --force train
dvc repro --pipeline train
dvc repro --all-pipelines
dvc repro --downstream featurize
dvc repro --force-downstream featurize
dvc repro --keep-going
dvc repro --ignore-errors
dvc repro --allow-missing --pull train
```

Important flags:

- Targets default to `dvc.yaml` when omitted.
- `--dry` prints commands that would execute without actually executing them.
- `--force` reproduces even when dependencies did not change.
- `--single-item` reproduces only the named data item or stage without recursive dependency checks.
- `--pipeline` reproduces the full pipeline containing the target and disables single-item/downstream behavior.
- `--all-pipelines` reproduces all pipelines and also disables single-item/downstream behavior.
- `--recursive` collects stages under a directory target.
- `--downstream` starts from the specified stage and walks descendants.
- `--force-downstream` forces descendants of a changed or forced stage even if their direct dependencies did not change.
- `--pull` tries to pull missing run-cache/data before repro; route remote details to `../remotes-and-cache/SKILL.md`.
- `--allow-missing` skips stages with missing data but no other changes.
- `--no-commit` avoids committing outputs to cache after run.
- `--no-run-cache` bypasses DVC's run cache for stage commands.
- `--glob` treats stage-name portions of targets as wildcard patterns.

Repo API equivalent:

```python
from dvc.repo import Repo

repo = Repo()
changed = repo.reproduce(
    targets=["dvc.yaml:train"],
    recursive=False,
    pipeline=False,
    all_pipelines=False,
    downstream=False,
    single_item=False,
    glob=False,
    on_error="fail",
    dry=True,
    force=False,
    force_downstream=False,
    allow_missing=False,
    pull=False,
)
```

`Repo.reproduce()` returns the stages that were reproduced or would be reproduced for dry runs. `on_error` accepts `"fail"`, `"keep-going"`, or `"ignore"`.

## Inspect Status, Data Status, Diff, And DAG

Use local status for stage and output changes:

```bash
dvc status
dvc status train
dvc status --json dvc.yaml:train
dvc status --with-deps train
dvc status --recursive pipelines/
```

Typical local status findings include changed commands, changed dependencies, changed outputs, deleted outputs, modified data, and `not in cache` entries. `Repo.status(targets=None, cloud=False, remote=None, with_deps=False, recursive=False, check_updates=True)` returns a dictionary; local mode rejects cloud-only options such as all-branches/all-tags/all-commits/jobs.

Use `dvc data status` to compare the last Git commit, DVC files, and workspace data:

```bash
dvc data status
dvc data status --json
dvc data status --granular --untracked-files all
dvc data status --not-in-remote --remote myremote
```

Use `dvc diff` for Git revisions versus workspace or another revision:

```bash
dvc diff
dvc diff HEAD main --targets data/raw.csv models/model.pkl
dvc diff --json --show-hash
dvc diff --md --hide-missing
```

`Repo.diff(a_rev="HEAD", b_rev=None, targets=None, recursive=False)` reports `added`, `deleted`, `modified`, `renamed`, and `not in cache` entries; missing cache appears when comparing a Git revision to the workspace unless hidden.

Use `dvc dag` to visualize pipeline structure:

```bash
dvc dag
dvc dag train
dvc dag --outs
dvc dag --mermaid
dvc dag --md
dvc dag --full train
dvc dag --collapse-foreach-matrix
```

`--outs` switches nodes from stages to output files; it is mutually exclusive with `--collapse-foreach-matrix`.

## Cache And Workspace Maintenance

Use these only after status and target scope are clear:

```bash
dvc checkout --summary
dvc checkout --with-deps train
dvc checkout --recursive data/
dvc checkout --force --allow-missing train
dvc checkout --relink train

dvc commit train
dvc commit --force train
dvc commit --with-deps train
dvc commit --recursive data/
dvc commit --no-relink train

dvc remove train
dvc remove --outs train
dvc move old-output new-output
dvc update imported-data.dvc --rev main
dvc freeze train
dvc unfreeze train
```

Notes:

- `dvc checkout` restores workspace data from the local cache and can delete/replace workspace files; use `--summary` first when uncertain.
- `dvc commit` records current tracked output contents in the cache; use `--force` when DVC did not detect a content hash change but you need to update metadata.
- `dvc remove` removes DVC metadata; with `--outs`, it also removes outputs.
- `dvc move` updates DVC-tracked output paths and moves files in the workspace.
- `dvc update` applies to imported data; remote-transfer flags such as `--to-remote`, `--remote`, and `--jobs` are storage workflows.
- `dvc freeze` marks stages as frozen so their dependencies are not reproduced; `dvc unfreeze` restores normal dependency traversal.

## Target Syntax

DVC command targets can refer to stages, files, outputs, directories, or DVC metadata files depending on the command.

- Bare stage in root `dvc.yaml`: `train`.
- Explicit stage in root `dvc.yaml`: `dvc.yaml:train` or `:train` for commands that accept target parsing.
- Stage in another pipeline file: `subdir/dvc.yaml:train`.
- `.dvc` file target: `data/raw.csv.dvc`.
- Tracked output target: `data/features.parquet`.
- Recursive directory target: `dvc status --recursive pipelines/` or `dvc repro --recursive pipelines/`.
- Glob stage-name target: `dvc repro --glob 'train*'` or `dvc repro --glob 'subdir/dvc.yaml:train*'`; glob applies to the stage name part, not the file path.

Ambiguity rules favor stages in `dvc.yaml` before output paths when a bare target could be either. Do not target `dvc.lock` directly for stages; DVC will suggest the corresponding `dvc.yaml` form.

## Safe Planning Pattern

When asked to design or review a DVC pipeline without executing commands:

1. Draft stage declarations from inputs, outputs, params, metrics, plots, and commands.
2. Print planned `dvc stage add` commands with shell quoting.
3. Print `dvc repro --dry <target>` commands for each target or the whole pipeline.
4. Print inspection commands: `dvc status`, `dvc dag`, `dvc diff`, `git diff -- dvc.yaml dvc.lock`.
5. Defer actual `dvc repro`, `dvc commit`, `dvc checkout`, `dvc remove`, or `dvc move` until the user approves workspace/cache mutations.

The bundled helper implements this pattern without importing or executing DVC.
