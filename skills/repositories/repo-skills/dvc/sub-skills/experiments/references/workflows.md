# DVC Experiments Workflows

## Purpose

Use this reference to run, queue, compare, promote, share, and clean up DVC experiments. Experiments are lightweight Git refs created around DVC pipeline reproduction; they are not a replacement for defining stages, dependencies, outs, metrics, params, or remotes.

## Command Family

DVC exposes the experiments command as both `dvc exp` and `dvc experiments`. The installed command family includes:

- `dvc exp run` to reproduce a pipeline as an experiment.
- `dvc exp show` to display experiment rows with metrics, params, deps, state, and executor columns.
- `dvc exp diff` to compare metrics and params between two experiments, a baseline, or the workspace.
- `dvc exp apply` and `dvc exp branch` to inspect or promote experiment changes.
- `dvc exp list`/`dvc exp ls`, `push`, `pull`, `remove`/`rm`, `rename`, `save`, and `clean` for lifecycle management.

## Run One Experiment Now

Use this when the user wants a normal experiment run against the current workspace:

```bash
dvc exp run -n trial-a -S train.lr=0.01 -S train.epochs=5
```

Decision points:

- `dvc exp run` inherits ordinary `dvc repro` targeting and reproduction flags, so route stage construction or target-selection design to `data-and-pipelines`.
- `-n/--name` gives a human-readable experiment name; DVC auto-generates one when omitted.
- `-S/--set-param [<filename>:]<param_name>=<param_value>` modifies params for the experiment run.
- `-m/--message` sets the experiment commit message.
- `--no-hydra` disables automatic Hydra-driven updates to `params.yaml`, but `--set-param` still applies explicit parameter changes.

## Queue Parameter Sweeps

Use `--queue` when the user wants deferred runs, parallel execution, or Hydra sweep overrides:

```bash
dvc exp run --queue -n lr-sweep -S train.lr=0.001,0.01,0.1

dvc exp run --queue -n depth-sweep -S model.depth=3,5,7 -S train.epochs=20

dvc exp run --run-all -j 2
```

Decision points:

- Hydra sweep-style overrides require `--queue`; DVC raises an argument error for sweep overrides without it.
- `--run-all` executes all queued experiments and implies temp execution behavior.
- `-j/--jobs <number>` controls how many queued experiments run in parallel.
- Queueing is best for repeated parameter changes; a single immediate run is simpler with plain `dvc exp run`.

## Use Temporary Execution And Copy Paths

Use temp execution when the user wants to avoid mutating the current workspace during a run:

```bash
dvc exp run --temp -n isolated-trial -S train.lr=0.02
```

Use `--copy-paths` only for ignored or untracked files that the temp or queued executor must see:

```bash
dvc exp run --queue -n uses-local-secret-config -C local_config.yaml -S model.dropout=0.2
```

Decision points:

- `--temp` runs the experiment in a separate temporary directory instead of the workspace.
- `-C/--copy-paths <path>` is only used with `--temp` or `--queue`.
- Prefer tracking reproducible inputs through DVC/Git over relying on copied untracked paths.
- If `--set-param` targets an untracked params file during temp or queued runs, DVC may add that params file to Git so it can be modified by the executor.

## Compare Experiments

Use `dvc exp show` for multi-row inspection:

```bash
dvc exp show --only-changed --sort-by metrics.accuracy --sort-order desc

dvc exp show --json --all-commits --param-deps --force

dvc exp show --md --drop 'deps:.*' --keep 'metrics:.*|params:.*'
```

Important `show` selectors and display controls:

- Revision selection: `--rev <commit>`, `--num <num>`, `--all-commits`, `--all-branches`, and `--all-tags`.
- Filtering: `--only-changed`, `--drop <regex>`, `--keep <regex>`, and `--param-deps`.
- Sorting and identity: `--sort-by <metric/param>`, `--sort-order asc|desc`, and `--sha`.
- Visibility: `--hide-failed`, `--hide-queued`, and `--hide-workspace`.
- Output formats: default rich table, `--json`, `--csv`, `--md`, `--precision <n>`, and `--force` to ignore cached experiment table data.

Use `dvc exp diff` for pairwise comparison:

```bash
dvc exp diff baseline-exp candidate-exp --param-deps --json

dvc exp diff candidate-exp --md --precision 4
```

`dvc exp diff` defaults the old revision to `HEAD` and the new revision to the workspace when omitted. Add `--all` to include unchanged metrics/params and `--no-path` to hide metric/param paths.

For scripted JSON inspection without invoking the CLI renderer, use the bundled helper:

```bash
python scripts/inspect_experiments.py --repo . --rev HEAD --num 3 --param-deps --force
```

## Promote Or Restore Results

Use `apply` when the user wants the selected experiment changes in the working tree:

```bash
dvc exp apply candidate-exp
```

Use `branch` when the experiment should become a durable Git branch for review, CI, or collaboration:

```bash
dvc exp branch candidate-exp candidate-exp-review
```

Decision points:

- `apply` changes the workspace; confirm the user is ready for local file changes. `--no-force` exists but is deprecated in this package version.
- `branch` creates a Git branch from an experiment. If no branch name is provided, DVC derives one from the experiment name.
- Use `dvc exp save` when the workspace already contains useful changes and the user wants to capture them as an experiment without rerunning the pipeline.

## Save Current Workspace As An Experiment

```bash
dvc exp save -n manual-fix --include-untracked notes/config.yaml --json
```

Useful flags:

- `targets` limits caching to specific `.dvc` files or stage names.
- `-R/--recursive` caches subdirectories of a target directory.
- `-f/--force` replaces an existing experiment with the same name.
- `-I/--include-untracked <path>` includes untracked file paths in the saved experiment.
- `-m/--message` records a custom experiment commit message.

## Share Experiments

Use `push` and `pull` for experiment refs on a Git remote, optionally including DVC cache and run-cache data:

```bash
dvc exp push origin candidate-exp -r storage -j 4 --run-cache

dvc exp pull origin candidate-exp -r storage --run-cache
```

Decision points:

- `git_remote` is required and can be a remote name or Git URL.
- `--rev`, `--num`, and `--all-commits` select experiment baselines for push/pull.
- `--force` resolves name conflicts by replacing the remote or local experiment.
- `--no-cache` transfers experiment refs without cached outputs; rerun without `--no-cache` when cached outputs are needed.
- `-r/--remote <name>` chooses the DVC remote for cached outputs; configure remotes and credentials through `remotes-and-cache`.
- `--run-cache` transfers run history for all stages.
- Studio/live experiment updates may require configured Studio credentials and network access; do not treat them as local default behavior.

## List, Rename, Remove, And Clean

List local or remote experiments:

```bash
dvc exp list --all-commits

dvc exp ls origin --name-only

dvc exp ls --rev HEAD --sha-only
```

Rename an experiment locally or on a remote:

```bash
dvc exp rename old-name new-name

dvc exp rename -g origin old-name new-name --force
```

Remove selected experiments, queued entries, or remote experiments:

```bash
dvc exp remove candidate-exp

dvc exp rm --queue

dvc exp rm --all-commits --keep keep-this-exp

dvc exp rm -g origin candidate-exp
```

Clean temporary internal experiment files:

```bash
dvc exp clean
```

Decision points:

- `remove` requires either experiment names or one selector such as `--rev`, `--all-commits`, or `--queue`.
- `--keep` inverts rev/all-commit removal to keep selected experiments.
- `--sha-only` is not supported when listing a remote Git repository.
- `clean` removes internal temporary experiment files, not user project data.
