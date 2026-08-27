# Execution Patterns

Use these patterns to build safe Snakemake 9.23.1 commands. Replace paths, targets, rules, resources, and profile names with workflow-specific values. Do not include the removed `--reason` flag.

## Pattern 1: Safe First Inspection

Goal: inspect an unfamiliar workflow without changing files.

```bash
snakemake --snakefile workflow/Snakefile --directory . --cores 1 --dry-run --printshellcmds
snakemake --snakefile workflow/Snakefile --directory . --cores 1 --summary
snakemake --snakefile workflow/Snakefile --directory . --cores 1 --rulegraph > rulegraph.dot
```

Checklist:

1. Confirm the Snakefile path and workdir are what the user expects.
2. Confirm targets and planned jobs match the request.
3. Read dry-run reasons in the job output; Snakemake 9.23.1 prints them without `--reason`.
4. Confirm no destructive cleanup, broad force, or unexpected profile is active.
5. If an implicit `profiles/default/` may be interfering, rerun with `--workflow-profile none`.

## Pattern 2: Real Local Run After Dry-Run

Goal: execute locally after the dry-run plan is plausible.

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --cores 4 --printshellcmds
```

Scale gradually:

- Start with `--cores 1` for reproducibility and clearer logs.
- Increase `--cores` only after the target set and shell commands are plausible.
- Add `--keep-going` only if independent jobs should continue after runtime failures.
- Add `--latency-wait 60` when successful jobs produce files slowly on a networked filesystem.

## Pattern 3: Explicit Target Run

Goal: build only requested files or rules.

```bash
snakemake results/qc/sampleA.html --cores 4 --dry-run --printshellcmds
snakemake results/qc/sampleA.html --cores 4 --printshellcmds
```

If a target name is ambiguous, inspect rule names first:

```bash
snakemake --list-rules
snakemake --list-target-rules
```

Route target-rule design or missing `rule all` behavior to `../workflow-authoring/`.

## Pattern 4: Profile Plus CLI Override Audit

Goal: understand why a profile-driven run differs from expectations.

```bash
snakemake --profile shared --workflow-profile default --cores 1 --dry-run --printshellcmds
snakemake --profile shared --workflow-profile none --cores 1 --dry-run --printshellcmds
snakemake --profile shared --workflow-profile default --cores 2 --default-resources mem_mb=1000 --dry-run
```

Audit rules:

- Later `--profile` entries override earlier profiles at top-level YAML keys.
- A workflow profile overrides global profiles at top-level keys.
- CLI options override profile values for the same top-level option.
- If a later profile specifies `default-resources`, it replaces the entire earlier `default-resources` map.
- Use `--workflow-profile none` to prove whether implicit `profiles/default/` is changing the run.

## Pattern 5: Workflow Profile, Config Overrides, Resources, and Batch

Goal: dry-run a large workflow using workflow-specific resource overrides and one batch.

Example workflow profile `workflow/profiles/shared/profile.yaml`:

```yaml
cores: 8
jobs: 50
local-cores: 2
printshellcmds: true
default-resources:
  mem_mb: 2000
  disk_mb: 10000
set-resources:
  aggregate:
    mem_mb: 16000
set-resource-scopes:
  mem_mb: local
```

Dry-run one batch with explicit CLI overrides:

```bash
snakemake --snakefile workflow/Snakefile \
  --workflow-profile shared \
  --cores 4 \
  --resources mem_mb=32000 disk_mb=200000 \
  --batch aggregate=1/4 \
  --dry-run --printshellcmds
```

Expected signals:

- The CLI `--cores 4` overrides profile `cores: 8`.
- The profile `set-resources` affects the named rule unless the CLI overrides the same top-level option.
- `--batch aggregate=1/4` restricts DAG construction to the first batch of `aggregate` inputs.
- Dry-run prints selected jobs and reasons; there is no `--reason` flag.

## Pattern 6: Resource Tuning Before Scaling

Goal: keep jobs inside CPU, memory, disk, runtime, and custom limits.

```bash
snakemake --cores 8 \
  --resources mem_mb=32000 disk_mb=500000 gpu=1 \
  --default-resources mem_mb=2000 runtime=60 disk_mb=10000 \
  --set-threads align=4 call_variants=2 \
  --set-resources align:mem_mb=12000 align:partition="long" \
  --dry-run --printshellcmds
```

Before a real run:

- Confirm resource names match the Snakefile and executor profile.
- Confirm integer-only limits are passed to `--resources`.
- Quote string resources in shell commands and profile YAML.
- Confirm thread overrides do not exceed `--cores` or `--max-threads`.
- For cluster/cloud execution, decide whether custom resources are `global` or `local` via `--set-resource-scopes`.

## Pattern 7: Batch a Large Aggregation Rule

Goal: reduce DAG construction and execution scope for a large target rule.

```bash
snakemake --cores 8 --batch aggregate=1/3 --dry-run --printshellcmds
snakemake --cores 8 --batch aggregate=1/3 --printshellcmds
snakemake --cores 8 --batch aggregate=2/3 --printshellcmds
snakemake --cores 8 --batch aggregate=3/3 --printshellcmds
```

Rules:

- Use a central aggregating rule with many input files.
- Keep the same workflow version and config across all batches.
- Run every batch; the final batch can continue beyond the batching rule once all inputs exist.
- Do not combine batching with `--forceall`; Snakemake rejects this combination.
- Dry-run each batch when diagnosing partitioning.

## Pattern 8: Group Jobs for Cluster or Cloud Execution

Goal: submit connected small jobs as group jobs in non-local execution.

```bash
snakemake --executor slurm --jobs 100 --local-cores 2 \
  --groups trim=preprocess map=preprocess \
  --group-components preprocess=10 \
  --default-resources mem_mb=2000 runtime=30 \
  --dry-run --printshellcmds
```

Guidance:

- Local execution ignores grouping; use grouping for cluster/cloud scheduling overhead.
- Use group names that reflect resource and scheduling behavior, not just rule names.
- Dry-run before real submission because group resource aggregation can change requested memory/runtime.
- `--group-components group=5` groups up to five disconnected components for that group.
- If group resources exceed limits, Snakemake may serialize layers within the group.

## Pattern 9: Rerun After Changed Code, Params, or Inputs

Goal: choose a rerun strategy after partial outputs exist.

Inspect first:

```bash
snakemake final/report.html --cores 4 --dry-run --printshellcmds
snakemake --summary
snakemake --list-changes code
snakemake --list-input-changes
snakemake --list-params-changes
```

Surgical rerun:

```bash
snakemake final/report.html --cores 4 --forcerun normalize --dry-run --printshellcmds
snakemake final/report.html --cores 4 --forcerun normalize --printshellcmds
```

Traditional mtime-only policy:

```bash
snakemake final/report.html --cores 4 --rerun-triggers mtime --dry-run
```

Interrupted outputs:

```bash
snakemake final/report.html --cores 4 --rerun-incomplete --dry-run --printshellcmds
snakemake final/report.html --cores 4 --rerun-incomplete --printshellcmds
```

Safety notes:

- Use `--forcerun RULE_OR_FILE` for surgical recomputation.
- Use `--forceall` only when the user explicitly accepts recomputing the whole reachable DAG.
- Use `--rerun-triggers` to change stale-output criteria, not to mask missing inputs.
- Use `--touch` only as a last resort for existing outputs because it can make provenance misleading.

## Pattern 10: Stale Lock or Incomplete Output Diagnosis

Goal: recover from interrupted execution without deleting useful data.

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --unlock
snakemake --cores 1 --dry-run --printshellcmds
snakemake --cores 1 --rerun-incomplete --dry-run --printshellcmds
```

Procedure:

1. Confirm no Snakemake process is currently running in the same workdir.
2. Run `--unlock` only to remove a stale lock, not to resolve active concurrent writes.
3. Use `--summary` to identify incomplete, missing, or stale outputs.
4. Prefer `--rerun-incomplete` over manual deletion.
5. Avoid broad `--delete-all-output` unless the user explicitly approves after a dry-run listing.

## Pattern 11: Scheduler and Large-DAG Performance

Goal: reduce overhead or diagnose scheduling issues.

```bash
snakemake --cores 8 --scheduler greedy --dry-run --quiet
snakemake --cores 8 --scheduler ilp --dry-run --printshellcmds
snakemake --cores 8 --scheduler-subsample 1000 --dry-run --quiet
snakemake --cores 8 --runtime-profile runtime-profile.prof
```

Guidance:

- Built-in scheduler choices include `greedy` and `ilp`; `ilp` aims for high-quality resource-aware scheduling, while `greedy` is often faster.
- If ILP solver setup fails or scheduling is slow, try `--scheduler greedy` before changing workflow logic.
- Use `--scheduler-subsample N` for very large ready-job sets when scheduling itself is expensive.
- Use `--runtime-profile FILE` to profile Snakemake internals; it requires `yappi`.

## Pattern 12: Safe Smoke Check for an Uncertain Executable

Goal: prove the selected Snakemake executable can parse and dry-run a tiny workflow.

```bash
python scripts/snakemake_smoke_check.py --snakemake snakemake
python scripts/snakemake_smoke_check.py --snakemake "python -m snakemake" --show-output
```

The script creates a temporary Snakefile, runs `--cores 1 --dry-run --printshellcmds`, verifies the tiny target appears in output, and deletes the tempdir unless `--keep-tempdir` is set.
