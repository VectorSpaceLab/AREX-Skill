# Snakemake 9.23.1 CLI Reference

This reference focuses on running, inspecting, scaling, and troubleshooting existing workflows from the `snakemake` command line. It assumes Snakemake is installed and the workflow syntax itself is already valid.

## Version-Specific Ground Rules

- CLI entrypoints: `snakemake` maps to `snakemake.cli:main`; `python -m snakemake` is also valid.
- Default built-in executors visible in a minimal install are `local`, `dryrun`, and `touch`; plugin executors add more choices and often add plugin-specific flags to `snakemake --help`.
- Snakemake 9.23.1 does not accept the legacy `--reason` flag. Omit it; dry-run output still reports reasons such as missing outputs, updated inputs, or changed code/params.
- A real run generally needs `--cores N` or `--cores all`; local-only `--jobs N` is accepted as an alias for `--cores`, but `--cores` is clearer.
- Use `--dry-run --quiet` for very large workflows when detailed job output is too verbose and only a DAG summary is needed.

## Entrypoints and Workflow Location

Default workflow discovery searches for `workflow/Snakefile` or `Snakefile` under the working directory. Use explicit paths when diagnosing an unfamiliar layout:

```bash
snakemake --snakefile workflow/Snakefile --directory . --cores 1 --dry-run --printshellcmds
python -m snakemake --snakefile Snakefile --cores 1 --dry-run
```

Targets are positional and may be rules or files:

```bash
snakemake results/report.txt --cores 4 --dry-run --printshellcmds
snakemake all qc/sampleA.html --cores 8 --printshellcmds
```

Use `--directory DIR` when relative paths in the workflow should resolve from a specific workdir. If a remote `--snakefile` URL is used, only Snakefiles and directly referenced files are retrieved; full workflow deployments with configs/profiles need a deployment approach, not an ad-hoc CLI run.

## Non-Mutating Inspection Commands

Start with commands that do not change data:

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --cores 1 --dry-run --quiet
snakemake --list-rules
snakemake --list-target-rules
snakemake --summary
snakemake --detailed-summary
```

Useful signals:

- Dry-run prints the jobs that would execute and why they are selected.
- `--printshellcmds` shows shell commands for jobs that would run.
- `--summary` reports known workflow outputs, status, and whether Snakemake plans to create or update them.
- `--detailed-summary` adds input files and shell commands to the summary.
- `--list-changes code|input|params`, `--list-input-changes`, and `--list-params-changes` diagnose provenance-triggered reruns.

## DAG and Graph Inspection

Graph commands do not execute jobs. Redirect output before post-processing with Graphviz or Mermaid-compatible tools:

```bash
snakemake --cores 1 --dag > dag.dot
snakemake --cores 1 --dag mermaid-js > dag.mmd
snakemake --cores 1 --rulegraph > rules.dot
snakemake --cores 1 --filegraph > files.dot
snakemake --forceall --dag > full-dag.dot
```

Caveats:

- `--dag` shows the job DAG that would be executed under current filesystem state.
- `--forceall --dag` is useful when existing outputs hide parts of the full workflow graph.
- `--rulegraph` is less crowded but shows each rule once and may display cycles when a rule appears in several workflow stages.
- `print()` statements in a Snakefile can corrupt DOT output; route syntax cleanup to `../workflow-authoring/`.

## Cores, Jobs, and Local Cores

Local execution:

```bash
snakemake --cores 4
snakemake --cores all
snakemake --cores 1 --dry-run
```

Remote or plugin execution:

```bash
snakemake --executor slurm --jobs 100 --local-cores 2 --default-resources mem_mb=4000 runtime=60
snakemake --executor dryrun --jobs 10 --local-cores 1 --dry-run
```

Semantics:

- `--cores N` or `-c N` limits CPU cores/jobs in parallel. `--cores all` uses detected cores.
- `--jobs N` or `-j N` limits cluster/cloud submitted jobs; in local mode it aliases `--cores`. `--jobs unlimited` is valid for submitted jobs.
- `--local-cores N` limits host-machine cores used for local rules in cluster/cloud mode and is ignored outside cluster/cloud mode.
- Rule `threads:` requests must fit within the effective core budget. Use `--set-threads RULE=N` or `--max-threads N` for execution-time overrides.

## Resources, Threads, and Scopes

Global resource limits constrain scheduling similarly to cores:

```bash
snakemake --cores 8 --resources mem_mb=32000 disk_mb=200000 gpu=1
snakemake --cores 8 --set-threads align=4 call_variants=2
snakemake --cores 8 --set-resources align:mem_mb=12000 align:runtime=180 align:partition="long"
snakemake --cores 8 --default-resources mem_mb=2000 runtime=30 disk_mb=10000
```

Important details:

- `--resources NAME=INT` defines total available resources for scheduling. Values must be integers for this flag.
- `--set-resources RULE:RESOURCE=VALUE` overrides rule resources; values may be positive integers or strings. Quote shell-sensitive strings.
- `--default-resources` supplies resource values for rules that omit them. It accepts integers and Python expressions over input size, for example `mem_mb=max(2*input.size_mb,1000)`.
- If `--default-resources` is not specified at all, Snakemake still applies a default `tmpdir` resource and default memory/disk behavior in supported contexts.
- `--set-resource-scopes RESOURCE=global|local` controls how a resource constraint is counted in cluster execution. By default, `mem_mb` and `disk_mb` are local; most other resources are global. CPU cores are always local.
- Dynamic resources in profile YAML should be quoted so the YAML parser does not treat the expression as invalid syntax.

## Profiles and Workflow Profiles

Profile YAML keys are command-line option names without leading dashes:

```yaml
executor: slurm
jobs: 110
cores: 220
printshellcmds: true
default-resources:
  mem_mb: 1024
set-threads:
  align: 8
set-resources:
  align:
    mem_mb: 16000
```

Use profiles from the CLI:

```bash
snakemake --profile shared --cores 8 --dry-run --printshellcmds
snakemake --profile base --profile user-override --cores 4 --dry-run
snakemake --workflow-profile default --cores 4 --dry-run
snakemake --workflow-profile none --cores 1 --dry-run
```

Precedence and lookup rules:

- `--profile PATH_OR_NAME` configures the compute environment. It can be passed multiple times; later profiles override earlier profiles at top-level YAML keys.
- `--workflow-profile PATH_OR_NAME` configures a workflow instance. It is parsed after global profiles and also overrides them at top-level keys.
- CLI arguments override profile settings for the same top-level option.
- If `--workflow-profile` is omitted, Snakemake searches for an implicit `profiles/default/` relative to the Snakefile and current directory. Use `--workflow-profile none` to suppress that implicit profile.
- Profile file names are commonly `profile.yaml`, `config.yaml`, or version-gated forms such as `profile.v9+.yaml`. Direct YAML file paths may use arbitrary file names.
- Environment-variable profile defaults can be convenient for users, but explicit `--profile`/`--workflow-profile` commands are easier to audit in automation.

## Targets, Force, Until, Omit, and Batches

Targeted run:

```bash
snakemake results/a.txt results/b.txt --cores 4 --dry-run
snakemake results/a.txt --cores 4 --printshellcmds
```

Force selected work:

```bash
snakemake results/a.txt --cores 4 --force --dry-run
snakemake --cores 4 --forcerun align quantify --dry-run
snakemake --cores 4 --forceall --dry-run
```

Bound a DAG:

```bash
snakemake --cores 4 --until aggregate --dry-run
snakemake --cores 4 --omit-from expensive_rule --dry-run
```

Batch a large target rule:

```bash
snakemake --cores 4 --batch aggregate=1/3 --dry-run --printshellcmds
snakemake --cores 4 --batch aggregate=1/3
snakemake --cores 4 --batch aggregate=2/3
snakemake --cores 4 --batch aggregate=3/3
```

Batch rules:

- `--batch RULE=N/M` computes batch `N` of `M` for the selected rule’s input files.
- Choose an aggregating rule with many input files and upstream jobs.
- Run every batch to complete the target rule. The final batch continues beyond the batch rule once all input batches have been produced.
- `--batch` may not be combined with `--forceall`; Snakemake rejects that combination because recomputed upstream jobs can invalidate earlier batches.

## Rerun Triggers and Incomplete Outputs

Snakemake tracks provenance and may rerun jobs when code, params, inputs, software environments, or modification times change:

```bash
snakemake --cores 4 --dry-run --printshellcmds
snakemake --summary
snakemake --list-changes code
snakemake --list-input-changes
snakemake --list-params-changes
```

Change rerun policy only when the user understands the consistency trade-off:

```bash
snakemake --cores 4 --rerun-triggers mtime
snakemake --cores 4 --rerun-triggers code params input software-env mtime
snakemake --cores 4 --rerun-incomplete
```

Use cases:

- Old workflows that intentionally rely only on file mtimes: `--rerun-triggers mtime`.
- Interrupted run left incomplete markers: `--rerun-incomplete`.
- Explicit rerun of a rule/output: `--forcerun RULE_OR_FILE...`.
- Avoid `--touch` unless the user intentionally wants to mark existing files up to date without preserving true provenance.

## Executors, Monitoring, and Runtime Profiling

Executor examples:

```bash
snakemake --executor local --cores 8
snakemake --executor dryrun --cores 8 --dry-run
snakemake --executor touch --cores 1
snakemake --executor slurm --jobs 200 --local-cores 2
```

Operational notes:

- `local` runs jobs as local processes.
- `dryrun` and `touch` are built-in executors for planning and timestamp workflows.
- Plugin executors require installed packages named like `snakemake_executor_<name>` and may add flags shown in `snakemake --help`.
- Distributed execution usually needs a profile, explicit `--jobs`, sensible `--local-cores`, and resource defaults.
- Storage, containers, and conda flags are deployment/storage concerns; route them to `../deployment-storage/`.

Monitoring and profiling:

```bash
snakemake --logger <plugin-name> --cores 4
snakemake --logger plugin_a --logger plugin_b --cores 4
snakemake --cores 4 --runtime-profile runtime-profile.prof
snakemake --cores 4 --verbose --latency-wait 60
```

`--runtime-profile FILE` profiles Snakemake itself and requires the `yappi` package. Use it for scheduler/DAG overhead, not for measuring individual shell commands.

## Grouping

CLI grouping assigns rules to execution groups for cluster/cloud mode:

```bash
snakemake --cores 8 --groups trim=preprocess map=preprocess --dry-run
snakemake --cores 8 --groups map=sample_group_{sample} --group-components sample_group_{sample}=5 --dry-run
```

Key behavior:

- Local execution ignores group definitions.
- Groups submit connected jobs together in cluster/cloud execution.
- `--groups RULE=GROUP` overrides workflow group definitions for those rules.
- `--group-components GROUP=N` allows a group to span up to `N` connected DAG components.
- Group resources are summed for parallel layers and maximized for serial layers, except `runtime`, where parallel layers take the max and serial layers sum. If constraints are too small, Snakemake stacks parallel layers in series.

## Locks and Cleanup Utilities

Use lock cleanup cautiously:

```bash
snakemake --unlock
snakemake --cores 1 --dry-run
```

Only run `--unlock` after checking that no Snakemake process is active for the same working directory. Other useful non-mutating cleanup/inspection commands include:

```bash
snakemake --list-untracked
snakemake --delete-all-output --dry-run
snakemake --delete-temp-output --dry-run
```

Deletion commands should stay in dry-run mode until the user explicitly approves destructive cleanup.

## Python Settings Names for API Mapping

When translating CLI intent to Python API/plugin settings, these dataclasses are the relevant anchors:

- `ExecutionSettings`: execution behavior such as latency wait, keep-going, locks, incomplete handling, retries, and shadow settings.
- `DAGSettings`: targets, batches, force flags, rerun triggers, DAG printing, strict DAG evaluation, and omitted/until targets.
- `ResourceSettings`: cores, nodes/jobs, local cores, resource limits, thread/resource overrides, default resources, and resource scopes.
- `SchedulingSettings`: scheduler plugin, greediness, and scheduler subsampling.
- `GroupSettings`: rule-to-group assignments and group component limits.
- `OutputSettings`: shell command printing, verbosity, quietness, DAG debugging, and related output behavior.

Route implementation-level API calls to `../python-api-plugins/`; keep this sub-skill focused on command construction and CLI diagnosis.
