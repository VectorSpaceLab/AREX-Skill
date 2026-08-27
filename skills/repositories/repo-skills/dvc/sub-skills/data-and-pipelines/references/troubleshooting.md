# DVC Data And Pipeline Troubleshooting

Use this guide to diagnose core DVC data and pipeline issues without jumping directly to destructive commands. Start with read-only commands, then choose the least invasive fix.

## No DVC Repository Or Empty Project

Symptoms:

- `dvc root` fails.
- `dvc status` says there are no data or pipelines tracked yet.
- Commands cannot find `dvc.yaml`, `.dvc` files, or stage targets.

Checks:

```bash
pwd
dvc root
git status --short
find . -maxdepth 3 -name dvc.yaml -o -name '*.dvc'
```

Fixes:

- Move to the intended project root or a subdirectory under it.
- For new projects, run `dvc init`, then use `dvc add` or `dvc stage add`.
- If metadata exists in a subdirectory, target it explicitly, such as `subdir/dvc.yaml:train`.

## Missing Cache Or Workspace Data

Symptoms:

- `dvc status` or `dvc diff` reports `not in cache`.
- `dvc data status` reports `Not in cache` and hints to use `dvc fetch`.
- `dvc checkout` cannot restore files.
- Repro fails because a dependency is missing.

Checks:

```bash
dvc status <target>
dvc data status --json <target>
dvc diff --show-hash --targets <path>
dvc checkout --summary <target>
```

Fixes:

- If the workspace file exists and should become the cached value, use `dvc commit <target>` after reviewing changes.
- If the data should come from remote storage, route to `../remotes-and-cache/SKILL.md` for `dvc fetch`, `dvc pull`, remote config, and optional storage extras.
- If only a dry plan is needed, use `dvc repro --dry <target>` or the bundled planner and do not run checkout/commit.
- Use `dvc checkout --allow-missing <target>` only when missing files are acceptable for the current task.

## Changed Dependencies, Outputs, Commands, Or Lockfile

Symptoms:

- `dvc status` reports `changed deps`, `changed outs`, or `changed command`.
- `dvc repro` skips a stage you expected to run.
- `dvc.lock` differs from `dvc.yaml` or was deleted.
- Parameter changes show as changed deps for `params.yaml`.

Checks:

```bash
dvc status <target>
dvc repro --dry <target>
git diff -- dvc.yaml dvc.lock params.yaml
dvc dag <target>
```

Fixes:

- If the command or declarations changed intentionally, run `dvc repro --dry <target>` first, then `dvc repro <target>` when execution is approved.
- If only output contents changed and the stage command should not rerun, use `dvc commit <target>` after verifying files.
- If a stage should run despite unchanged dependencies, use `dvc repro --force <target>`.
- If descendants should rerun after a forced or changed upstream stage, use `dvc repro --force-downstream <target>`.
- If a stage was created with missing deps/outs and later corrected, expect `dvc repro` to run once to update `dvc.lock`.

## Stage Graph, Overlap, Or Cycle Errors

Symptoms:

- DVC reports overlapping output paths.
- DVC reports a circular dependency.
- A dependency and output refer to the same path.
- A new `dvc add` target overlaps with an existing pipeline output.

Checks:

```bash
dvc dag
dvc status
git diff -- dvc.yaml '*.dvc'
```

Fixes:

- Ensure each output path is owned by exactly one DVC stage or `.dvc` file.
- Do not `dvc add` a parent directory that contains an output already tracked by another stage; either `dvc commit` the parent stage or remove/restructure the overlapping stage.
- Do not add a child output inside an already tracked parent; update the parent with `dvc commit` when that is the intended owner.
- Split dependencies and outputs so a stage does not read and write the same path.
- Use `dvc remove <target>` or `dvc remove --outs <target>` only after reviewing which metadata and workspace files will be affected.

## Invalid Stage Names Or Duplicate Stages

Symptoms:

- `dvc stage add` fails with invalid stage name.
- DVC says a stage already exists in `dvc.yaml`.
- Targets with punctuation are hard to address.

Checks:

```bash
dvc stage list --all
git diff -- dvc.yaml
```

Fixes:

- Use names like `featurize`, `train-model`, `copy_data`, or `12`.
- Avoid `$`, `?`, and `@` in stage names.
- Use `dvc stage add --force -n <name> ...` only when intentionally overwriting an existing stage.
- Prefer lowercase hyphen names for agent-generated stages.

## Target Syntax Errors

Symptoms:

- DVC cannot find a stage, output, or `.dvc` file.
- A stage in another directory is not selected.
- A glob pattern matches no stages.
- DVC suggests replacing `dvc.lock` with `dvc.yaml`.

Checks:

```bash
dvc stage list --all
dvc dag
dvc status --recursive <dir>
```

Fixes:

- Root stage: use `train` or `dvc.yaml:train`.
- Stage in another directory: use `subdir/dvc.yaml:train`.
- `.dvc` file: target `data/raw.csv.dvc`.
- Output path: target `data/features.parquet` for commands that accept output targets.
- Directory recursion: add `--recursive` when a directory should collect contained stages.
- Stage-name glob: add `--glob`, such as `dvc repro --glob 'train*'`; the wildcard applies to stage names, not pipeline file paths.
- Do not target `dvc.lock` as a stage file; use the matching `dvc.yaml` target.

## Frozen Stages And Repro Skips

Symptoms:

- `dvc repro` warns that a stage is frozen.
- Dependencies of a frozen stage are not reproduced.
- `dvc status` omits dependency detail for a frozen non-import stage.

Checks:

```bash
dvc status <target>
grep -n "frozen:" dvc.yaml
dvc dag <target>
```

Fixes:

- Use `dvc unfreeze <target>` when dependency traversal should resume.
- Use `dvc freeze <target>` for intentional pinning of imported data or expensive stages.
- Pair freeze/unfreeze changes with `git diff -- dvc.yaml` review.

## `dvc repro --dry` Does Not Match Expectations

Symptoms:

- Dry run prints no commands.
- Dry run prints more stages than expected.
- A downstream stage is skipped after an upstream failure.

Checks:

```bash
dvc status <target>
dvc repro --dry <target>
dvc repro --dry --pipeline <target>
dvc repro --dry --downstream <target>
dvc dag --full <target>
```

Fixes:

- No commands usually means DVC considers data and pipelines up to date; check `dvc status` and `git diff`.
- Use `--force` to run unchanged stages.
- Use `--single-item` to avoid recursive dependency checks for one target.
- Use `--pipeline` for the whole connected pipeline that contains a target.
- Use `--downstream` or `--force-downstream` when descendants matter.
- Use `--keep-going` to continue independent branches after failures; use `--ignore-errors` only when downstream correctness is not required.

## Lockfile Or Config Validation Errors

Symptoms:

- YAML validation errors mention `dvc.lock` or another lockfile path.
- `dvc.lock` is Git-ignored.
- Config errors appear after editing DVC metadata.

Checks:

```bash
git check-ignore -v dvc.lock || true
dvc status
dvc repro --dry
git diff -- .gitignore .dvcignore dvc.yaml dvc.lock .dvc/config
```

Fixes:

- Do not Git-ignore `dvc.lock`; remove the ignore rule and re-check.
- Regenerate lock state with `dvc repro --dry` first, then `dvc repro <target>` if execution is approved.
- If corruption came from hand-editing, restore from Git or re-run the relevant DVC command instead of manually reconstructing checksums.
- Route remote config and credentials to `../remotes-and-cache/SKILL.md`.

## `.dvcignore` Hides Expected Paths

Symptoms:

- DVC does not see a dependency or output.
- `dvc status` does not mention an expected file.
- File walking misses a directory.

Checks:

```bash
dvc check-ignore --details <path>
dvc check-ignore --details --non-matching <path>
git diff -- .dvcignore
```

Fixes:

- Remove or narrow the `.dvcignore` rule if the path is a real dependency or output.
- Use explicit stage deps/outs paths after fixing ignore rules.
- Re-run `dvc status` and `dvc repro --dry <target>` to validate visibility.

## Safe Escalation Order

1. Read-only: `dvc root`, `dvc status`, `dvc data status --json`, `dvc dag`, `dvc diff`, `dvc check-ignore`.
2. Dry planning: `dvc repro --dry <target>` and `scripts/plan_dvc_pipeline.py`.
3. Metadata-only or reviewed changes: `dvc stage add`, `dvc freeze`, `dvc unfreeze`, `dvc remove` without `--outs`.
4. Cache/workspace mutation: `dvc add`, `dvc commit`, `dvc checkout`, `dvc move`, `dvc update`, `dvc repro`.
5. Remote/cache cleanup and storage mutation: route to `../remotes-and-cache/SKILL.md`.
