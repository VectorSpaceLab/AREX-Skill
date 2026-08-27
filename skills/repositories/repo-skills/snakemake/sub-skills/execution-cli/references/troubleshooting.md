# Execution CLI Troubleshooting

Use this guide when a Snakemake command fails, runs unexpected jobs, ignores an intended profile, scales poorly, or appears blocked by locks/incomplete outputs. Keep diagnosis non-mutating until the user approves a real run or cleanup.

## Install or Entrypoint Mismatch

Symptoms:

- `snakemake: command not found`
- `python -m snakemake` works but `snakemake` does not, or the reverse
- `ModuleNotFoundError: No module named snakemake`
- CLI help does not show expected plugin executor flags

Checks:

```bash
snakemake --help
python -m snakemake --help
python -c "import snakemake; print(snakemake.__version__)"
python scripts/snakemake_smoke_check.py --snakemake snakemake --show-output
python scripts/snakemake_smoke_check.py --snakemake "python -m snakemake" --show-output
```

Interpretation:

- If import works but the command does not, the console script is missing from `PATH`; use `python -m snakemake` or fix the environment activation.
- If `snakemake --help` works but a plugin executor is absent from `--executor` choices, the relevant executor plugin is not installed in the active environment.
- If the smoke check fails on a tiny dry-run, fix installation before diagnosing the user workflow.

## Missing or Confusing Cores/Jobs

Symptoms:

- Snakemake asks for cores/jobs.
- Local run does not scale as expected.
- Remote run submits too many or too few jobs.
- `--local-cores` appears ignored.

Checks and fixes:

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --cores 4 --dry-run --printshellcmds
snakemake --executor slurm --jobs 50 --local-cores 2 --dry-run
```

Rules:

- Use `--cores N` for local CPU concurrency and local validation.
- Use `--jobs N` for cluster/cloud submitted jobs; in local mode it aliases `--cores`, but prefer `--cores`.
- `--local-cores` only matters in cluster/cloud execution.
- If a rule requests more threads than expected, use `--set-threads RULE=N` or `--max-threads N` after confirming the Snakefile authoring intent.

## Profile Merge Surprises

Symptoms:

- A dry-run uses unexpected cores, executor, resources, or shell printing.
- Adding a second profile drops some `default-resources` entries.
- A workflow behaves differently when run from another directory.

Diagnostic commands:

```bash
snakemake --profile base --cores 1 --dry-run --printshellcmds
snakemake --profile base --profile override --cores 1 --dry-run --printshellcmds
snakemake --workflow-profile none --cores 1 --dry-run --printshellcmds
snakemake --workflow-profile default --cores 1 --dry-run --printshellcmds
```

Common causes:

- Later `--profile` values override earlier profiles at top-level keys.
- Workflow profiles override global profiles at top-level keys.
- CLI arguments override profile values for the same top-level option.
- If a later profile sets `default-resources`, the entire earlier `default-resources` map is replaced.
- Snakemake can implicitly load `profiles/default/` relative to the Snakefile or current directory unless `--workflow-profile none` is supplied.
- Profile values can expand environment variables; check user-owned profiles for environment-dependent paths or usernames.

Fix strategy:

1. Reproduce with `--workflow-profile none`.
2. Add profiles back one at a time in intended order.
3. Move stable compute-environment settings to a global profile and workflow-instance resource settings to a workflow profile.
4. Put one-off overrides on the CLI so precedence is obvious.

## Resource Scope and Value Errors

Symptoms:

- CLI parsing fails for resources.
- Cluster group submissions request unexpected memory/disk.
- A custom resource limit applies globally when it should apply per group, or vice versa.

Checks:

```bash
snakemake --cores 8 --resources mem_mb=32000 disk_mb=200000 --dry-run
snakemake --cores 8 --set-resource-scopes mem_mb=local gpu=global --dry-run
snakemake --cores 8 --set-resources align:partition="long" align:mem_mb=12000 --dry-run
```

Rules:

- `--resources NAME=INT` accepts integer limits.
- `--set-resources RULE:RESOURCE=VALUE` accepts positive integers or strings.
- Quote string resource values in shells and profile YAML.
- By default, `mem_mb` and `disk_mb` are local resources in cluster execution; most other resources are global.
- CPU cores from `--cores` are always local.
- For grouped jobs, resources aggregate by group layers; dry-run before real submission.

Route missing resource declarations or dynamic resource functions to `../workflow-authoring/`.

## Stale Locks

Symptoms:

- Snakemake reports the working directory is locked.
- A previous process was interrupted.
- A user wants to delete `.snakemake` manually.

Safe recovery:

```bash
snakemake --cores 1 --dry-run
snakemake --unlock
snakemake --cores 1 --dry-run --printshellcmds
```

Safety checks:

- Confirm no Snakemake process is currently running in the same workdir.
- Do not remove lock files manually unless the CLI cannot run and the user understands the risk.
- `--unlock` only clears the lock; it does not repair incomplete outputs or guarantee data consistency.
- Follow with `--summary` and `--rerun-incomplete` if the interrupted run wrote partial files.

## Incomplete Outputs and Missing Files After Successful Jobs

Symptoms:

- Snakemake reports incomplete outputs after an interrupted run.
- A job succeeded but Snakemake cannot see output immediately.
- Networked filesystems produce intermittent missing-output errors.

Commands:

```bash
snakemake --summary
snakemake --cores 4 --rerun-incomplete --dry-run --printshellcmds
snakemake --cores 4 --rerun-incomplete --printshellcmds
snakemake --cores 4 --latency-wait 60 --printshellcmds
```

Interpretation:

- Use `--rerun-incomplete` for outputs Snakemake marked incomplete.
- Use `--latency-wait SECONDS` when output appears shortly after job completion on a slow filesystem.
- Avoid `--ignore-incomplete` unless the user is intentionally bypassing Snakemake’s safety checks.
- Avoid `--touch` for recovery unless files truly exist and the user accepts altered provenance.

## Rerun and Force Misuse

Symptoms:

- Too much of the workflow reruns.
- A forced run recomputes expensive upstream jobs unexpectedly.
- Batch execution becomes inconsistent.

Diagnostic commands:

```bash
snakemake target.txt --cores 1 --dry-run --printshellcmds
snakemake --summary
snakemake --list-changes code
snakemake --list-input-changes
snakemake --list-params-changes
```

Choose the narrowest tool:

- `--forcerun RULE_OR_FILE` for selected rules or outputs.
- `--force` for selected targets or the first rule.
- `--forceall` only for deliberate full reachable-DAG recomputation.
- `--rerun-triggers mtime` only when the user wants legacy modification-time behavior.
- `--rerun-incomplete` for interrupted outputs.
- Never combine `--batch` with `--forceall`; Snakemake rejects it.

## Scheduler or ILP Issues

Symptoms:

- DAG construction succeeds but scheduling is slow.
- ILP-related errors appear.
- Ready-job sets are huge.
- Runtime profile points at scheduler overhead.

Commands:

```bash
snakemake --cores 8 --scheduler greedy --dry-run --quiet
snakemake --cores 8 --scheduler ilp --dry-run --printshellcmds
snakemake --cores 8 --scheduler-subsample 1000 --dry-run --quiet
snakemake --cores 8 --runtime-profile runtime-profile.prof
```

Interpretation:

- Built-in scheduler choices include `greedy` and `ilp`.
- Use `greedy` as a practical fallback when ILP setup or overhead blocks progress.
- Use `--scheduler-subsample N` for very large sets of ready jobs.
- `--runtime-profile FILE` profiles Snakemake internals and requires `yappi`; it does not profile job payload commands.

## Grouping Surprises

Symptoms:

- `--groups` appears to do nothing locally.
- Group jobs request unexpected resources.
- Group components do not combine as expected.

Checks:

```bash
snakemake --cores 8 --groups trim=preprocess map=preprocess --dry-run --printshellcmds
snakemake --executor slurm --jobs 50 --local-cores 2 --groups trim=preprocess --group-components preprocess=5 --dry-run
```

Rules:

- Local execution ignores grouping.
- Cluster/cloud execution submits group jobs together.
- Groups normally span connected DAG components only.
- `--group-components GROUP=N` allows up to `N` connected components for a group.
- Group resources can be sums or maxima depending on whether jobs run in parallel or series; `runtime` is handled inversely for parallel vs serial layers.

## Legacy `--reason` Flag Removal

Symptoms:

- Command fails with an argparse error for `--reason`.
- An old profile includes `reason: true`.
- Existing automation uses `--dry-run --reason --printshellcmds`.

Fix:

```bash
snakemake --cores 1 --dry-run --printshellcmds
```

Remove `--reason` from commands and remove `reason: true` from profiles. In Snakemake 9.23.1, dry-run job output already includes reasons for selected jobs, so the flag is unnecessary and invalid.

## Safe Smoke Check Failure Interpretation

Use the bundled script before blaming a user workflow:

```bash
python scripts/snakemake_smoke_check.py --snakemake snakemake --show-output
python scripts/snakemake_smoke_check.py --snakemake "python -m snakemake" --show-output
```

Signals:

- Pass: the executable can parse and dry-run a tiny workflow with `--cores 1 --dry-run --printshellcmds`.
- Failure before Snakemake starts: command lookup, quoting, or environment activation issue.
- Failure with Snakemake usage text: CLI option mismatch or incompatible version.
- Failure after DAG construction: installation is present, but runtime dependencies or filesystem permissions may be broken.

The script does not use repository examples, network access, plugin executors, conda, containers, or user data.
