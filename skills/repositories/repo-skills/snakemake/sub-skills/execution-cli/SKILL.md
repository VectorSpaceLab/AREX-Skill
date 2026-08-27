---
name: execution-cli
description: "Run, inspect, scale, and troubleshoot Snakemake workflows from the
  command line, including dry-runs, targets, resources, profiles, batching,
  grouping, DAG inspection, schedulers, reruns, locks, and smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Execution CLI

Use this sub-skill when an agent needs to construct or diagnose Snakemake 9.23.1 CLI commands for an existing workflow: dry-runs, target selection, cores/jobs/local cores, resources, profiles, batches, groups, DAG/rulegraph/summary inspection, scheduler tuning, runtime profiling, reruns, locks, and safe smoke checks.

## Fast Routing

1. Confirm the executable and entrypoint with `snakemake --help`, `python -m snakemake --help`, or `scripts/snakemake_smoke_check.py` when the environment is uncertain.
2. Build a non-mutating command first: explicit `--snakefile` if needed, explicit targets if requested, `--cores 1`, `--dry-run`, and `--printshellcmds`.
3. Add scale controls only after the plan is plausible: `--cores`, `--jobs`, `--local-cores`, `--resources`, `--default-resources`, `--set-threads`, `--set-resources`, and `--set-resource-scopes`.
4. Add profiles, batches, groups, rerun/force flags, scheduler flags, or lock cleanup only when the user’s execution goal needs them.
5. In Snakemake 9.23.1, do not add the legacy `--reason` flag; dry-run output already includes job-selection reasons.

## References

- Use [references/cli-reference.md](references/cli-reference.md) for option semantics, command templates, profile precedence, DAG/summary commands, scheduler/runtime flags, and API settings names.
- Use [references/execution-patterns.md](references/execution-patterns.md) for end-to-end execution recipes: first run, target runs, profile/resource overrides, batching, grouping, reruns, locks, and smoke checks.
- Use [references/troubleshooting.md](references/troubleshooting.md) for install/import mismatches, missing cores, profile merge surprises, resource-scope errors, stale locks, incomplete outputs, force/rerun misuse, scheduler/ILP issues, and the removed `--reason` flag.
- Use [scripts/snakemake_smoke_check.py](scripts/snakemake_smoke_check.py) for a safe temporary-workflow probe that does not depend on repository examples or user data.

## Boundaries

- Route Snakefile syntax, rules, checkpoints, wildcards, and shell/script directive authoring to `../workflow-authoring/`.
- Route config files, `--config`, `--configfile`, tabular inputs, and sample-sheet semantics to `../configuration-data/`.
- Route conda, containers, executor plugin installation, remote storage, default storage, and deployment packaging to `../deployment-storage/`.
- Route linting, HTML reports, unit tests, notebook/report flags, and deep debugging reports to `../debugging-reporting/`.
- Route Python API equivalents, plugin development, and programmatic embedding to `../python-api-plugins/`.

## Safety Defaults

Prefer inspectable, reversible commands: dry-run before mutation, explicit targets before broad runs, low cores before scaling, profile overrides only after checking precedence, `--unlock` only after confirming no Snakemake process is active, and `--forceall` only when the user explicitly accepts recomputing the reachable workflow.
