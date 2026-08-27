# DVC Experiments Troubleshooting

## Purpose

Use this reference when `dvc exp` output is missing rows, stale, failed, queued, blocked by workspace state, missing untracked files, affected by Hydra behavior, or crossing network/Studio boundaries.

## `exp show` Rows Are Missing Or Hidden

Symptoms:

- Expected queued, failed, or workspace rows do not appear.
- Only a recent baseline is shown.
- Branch or tag experiments are absent.

Likely causes and recovery:

- Check whether the command includes `--hide-failed`, `--hide-queued`, or `--hide-workspace`; remove the hide flag when those rows are needed.
- Add `--all-commits`, `--all-branches`, `--all-tags`, or repeated `--rev <commit>` selectors when experiments are attached to other baselines.
- Increase `--num <num>` or use a negative value if the experiment baseline is farther back in first-parent history.
- Use `--sha` when branch/tag names obscure which commit is being displayed.
- Use `--force` when completed-experiment table data may be stale.

## JSON Or Table Output Looks Stale

Symptoms:

- `dvc exp show` or `dvc.api.exp_show()` returns old metric/param values.
- Newly completed experiments are not reflected in the table.

Recovery:

```bash
dvc exp show --json --force
python scripts/inspect_experiments.py --repo . --force
```

`--force` tells DVC to re-collect experiment data instead of loading cached completed-experiment table data.

## Queued Experiments Do Not Run

Symptoms:

- `dvc exp show` lists queued rows but no new completed experiments appear.
- A sweep was queued but not executed.

Recovery:

- Execute queued entries with `dvc exp run --run-all -j <number>`.
- Use `dvc exp rm --queue` only when the user wants to discard all queued experiments.
- For Hydra sweep overrides, ensure the original run used `--queue`; sweep overrides without queueing are rejected.
- If ignored or untracked local files are required by queued/temp execution, include them with `-C/--copy-paths` or make them reproducible tracked inputs.

## Dirty Workspace Or Overwritten Files

Symptoms:

- Applying or saving experiments affects local files unexpectedly.
- `dvc exp apply` would overwrite workspace changes.
- The user wants a reviewable, durable result instead of workspace mutation.

Recovery:

- Prefer `dvc exp branch <experiment> <branch-name>` for review, CI, and collaboration.
- Use `dvc exp apply <experiment>` only when the user wants experiment changes in the current workspace.
- If a workspace already contains valuable changes, use `dvc exp save -n <name>` to capture them before further edits.
- For saved experiments with untracked files, pass `--include-untracked <path>` for each path that should be included.

## Temp Or Queue Runs Cannot Find Files

Symptoms:

- A command works in the workspace but fails under `--temp`, `--queue`, or `--run-all`.
- The failure mentions missing config, credentials, small local files, or generated inputs.

Likely causes and recovery:

- Temp and queued runs execute outside the active workspace context.
- `-C/--copy-paths <path>` only applies with `--temp` or `--queue`; add one entry per ignored or untracked path required by the executor.
- Prefer tracking reproducible files with Git or DVC instead of copying hidden local state.
- Route remote object/cache availability problems to `remotes-and-cache`; missing run-cache or data can require pulling cache data or pushing/pulling with `--run-cache`.

## Hydra And `--set-param` Behave Unexpectedly

Symptoms:

- A sweep override is rejected.
- `params.yaml` is updated even when no explicit `--set-param` was provided.
- The user expects Hydra to stay out of the experiment.

Recovery:

- Use `dvc exp run --queue -S key=a,b,c` for sweep-style overrides; sweeps are rejected without `--queue`.
- Add `--no-hydra` to disable automatic Hydra-driven updates to `params.yaml`.
- Keep explicit parameter updates with `-S/--set-param`; `--no-hydra` does not disable explicit `--set-param` changes.
- If an untracked params file is modified by a queued/temp run, expect DVC to make it available to the executor; prefer tracked params files for reproducibility.

## Remote Push/Pull Does Not Include Outputs

Symptoms:

- The experiment ref exists on the Git remote but outputs are missing.
- A collaborator can see an experiment name but cannot reproduce or inspect cached results.

Recovery:

- Do not use `--no-cache` when cached outputs should be transferred.
- Specify `-r/--remote <name>` when the project has multiple DVC remotes.
- Add `--run-cache` when stage run history is needed for downstream reproduction.
- Configure storage credentials and optional remote dependencies through the remotes/cache workflow. Extras such as S3, SSH, Azure, GDrive, GS, HDFS, OSS, WebDAV, and WebHDFS are optional and should not be assumed installed by default.

## Studio Or Live Experiment Boundaries

Symptoms:

- Live metrics or Studio links are missing.
- Network, token, or credential-related errors appear during experiment execution or push.

Recovery:

- Treat Studio/live experiment reporting as optional integration behavior, not required local experiment behavior.
- Do not add network calls or Studio credentials to local-only helpers.
- If the user asks for Studio integration, first confirm credentials, network access, and project configuration. Otherwise keep workflows local and use `dvc exp show`, `dvc exp diff`, and the bundled JSON inspector.

## No DVC Repository Found

Symptoms:

- The bundled inspector or API raises a no-repository error.
- `dvc exp` commands fail outside a DVC project.

Recovery:

- Run commands from inside a DVC project or pass `--repo <path>` to the bundled inspector.
- If no pipeline exists yet, route to `data-and-pipelines` to initialize stages before running experiments.
