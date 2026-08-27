# Debugging reference

This reference covers Snakemake 9.23.1 diagnostics that inspect workflow structure or runtime signals without changing workflow outputs unless explicitly noted.

## Safe diagnostic sequence

Run from the workflow directory unless a different working directory is intentional.

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --lint
snakemake --lint json > diagnostics/lint.json
snakemake --summary > diagnostics/summary.tsv
snakemake --detailed-summary > diagnostics/detailed-summary.tsv
snakemake --dag > diagnostics/dag.dot
snakemake --rulegraph > diagnostics/rulegraph.dot
snakemake --filegraph > diagnostics/filegraph.dot
snakemake --debug-dag --cores 1 --dry-run > diagnostics/debug-dag.txt 2>&1
```

Signals to expect:

- A successful dry-run exits zero and prints planned jobs, shell commands with `--printshellcmds`, and reasons for selected jobs. Do not add `--reason`; it is not a valid Snakemake 9.23.1 flag.
- `--lint` exits non-zero when lint findings exist; treat this as a quality signal rather than a parser failure if lint messages are present.
- `--lint json` returns structured entries containing the linted item and each lint title/body/link.
- `--dag` and `--rulegraph` default to DOT and also accept Snakemake's configured graph formats such as `mermaid-js` where the CLI allows choices. `--filegraph` prints DOT.
- `--debug-dag` logs candidate and selected jobs, including rule names and wildcards. It is useful when wildcard resolution or unexpected target selection is the problem.

## Linting workflow quality

Use linting before editing syntax or deployment settings. Common findings in 9.23.1 include:

- Missing `log:` directive on rules that execute work, which makes distributed failures hard to inspect.
- Direct use of external variables in `shell:` instead of passing values through `input`, `output`, `params`, `wildcards`, `threads`, `resources`, or `log`.
- Positional `input[0]` or `output[0]` in shell commands where named fields such as `{input.reads}` would be clearer.
- Long `run:` blocks that should move into `script:` or `notebook:` directives.
- Rules without `conda:` or `container:` software definitions.
- Absolute paths, `os.environ[...]` without an `envvars:` assertion, tab indentation, deprecated `singularity:`, and string path composition with `+`.

False-positive handling:

1. Confirm whether the warning describes a portability or provenance issue rather than a hard error.
2. Prefer targeted Snakefile edits only when the lint matches the user's execution goal.
3. If a warning is intentional, record why in project notes or CI allow-list logic outside the runtime skill; do not suppress all lint output blindly.
4. Use `--lint json` for machine-readable allow-listing by lint title and item.

## DAG, rulegraph, and filegraph debugging

Choose the graph by question:

- `snakemake --dag`: job-level DAG for a concrete target set; crowded for many wildcard jobs.
- `snakemake --rulegraph`: rule dependency graph with each rule shown once; easier for architecture review but can appear cyclic when the same rule participates in multiple steps.
- `snakemake --filegraph`: rule and file dependency view; use when missing or unexpected files drive the issue.
- `snakemake --dag mermaid-js` or `snakemake --rulegraph mermaid-js`: text diagrams suitable for Markdown tools when supported by the installed CLI choices.

Render DOT outside Snakemake when Graphviz is available:

```bash
snakemake --dag > diagnostics/dag.dot
dot -Tsvg diagnostics/dag.dot > diagnostics/dag.svg
snakemake --rulegraph > diagnostics/rulegraph.dot
dot -Tpng diagnostics/rulegraph.dot > diagnostics/rulegraph.png
```

If graph output is polluted, inspect the Snakefile for top-level `print()` calls. Snakemake warns that print statements can interfere with graph visualization.

## Summaries and provenance signals

Use summaries after a workflow has produced outputs:

```bash
snakemake --summary
snakemake --detailed-summary
```

Interpret columns as follows:

- `filename`: output file tracked by the workflow.
- `modification time`: current filesystem timestamp.
- `rule version`: rule version recorded when the file was created, if the workflow uses rule versions.
- `status`: missing, input newer, rule implementation changed, params changed, or other provenance-derived stale state.
- `plan`: whether Snakemake would update or create the file in the next run.
- Detailed summaries also include input files and shell command information.

Snakemake stores provenance metadata under `.snakemake` by default. For very large workflows or network filesystems, `--persistence-backend db` can move metadata into a database-backed store, but infrastructure decisions belong with deployment/storage guidance.

## Failed logs and runtime logs

Useful runtime flags:

```bash
snakemake --cores 1 --printshellcmds --show-failed-logs
snakemake target/file.txt --cores 1 --printshellcmds --show-failed-logs
snakemake --cores 1 --debug
snakemake --cores 1 --skip-script-cleanup
```

Signals:

- Snakemake run logs are written under `.snakemake/log/` and mirror console output.
- `--show-failed-logs` prints rule `log:` files for failed jobs when those files exist.
- `--debug` drops into Python's debugger for `run:` blocks and Python scripts that contain `breakpoint()`.
- `--skip-script-cleanup` preserves generated wrapper scripts under `.snakemake/scripts/` for inspection.
- For Python scripts, redirect STDERR into `snakemake.log[0]` with line buffering when a rule has a `log:` directive. For R scripts, use sinks or save an `.RData` workspace before the failing statement.

## Runtime profiling

Use runtime profiling to inspect Snakemake process overhead, not individual tool performance:

```bash
snakemake --cores 1 --runtime-profile diagnostics/runtime-profile.txt target
```

Signals:

- Requires `yappi` to be installed in the active Python environment.
- The profile file describes Python call-time behavior inside the Snakemake process.
- If the profile is dominated by DAG construction, inspect wildcard constraints, input functions, checkpoints, and filesystem metadata calls.
- If the profile is dominated by executor or plugin callbacks, route plugin-specific analysis to deployment/storage or Python API/plugin guidance.

## Benchmarks

Declare benchmarks in rules and run the workflow normally:

```python
rule bench_example:
    output: "results/out.txt"
    benchmark: "benchmarks/example.tsv"
    shell: "tool > {output}"
```

For repeated measurements:

```python
benchmark:
    repeat("benchmarks/example.tsv", 3)
```

For JSON lines output, use a `.jsonl` benchmark path:

```python
benchmark: "benchmarks/example.jsonl"
```

Run with extended metrics when desired:

```bash
snakemake --cores 1 --benchmark-extended target
```

Signals:

- Non-`.jsonl` benchmark outputs are tab-separated with a header.
- `.jsonl` benchmark outputs contain one JSON object per record.
- Extended metrics can include additional resource fields when the platform and dependencies expose them.
- Missing or `NA` memory fields can be platform-specific; do not assume the job did no work solely from one unavailable memory metric.

## CI smoke validation

A conservative CI diagnostic job should avoid heavy execution:

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --lint json > lint.json
snakemake --dag > dag.dot
```

For workflows with safe tiny fixtures, add:

```bash
snakemake --cores 1 --notemp --show-failed-logs
snakemake --generate-unit-tests .tests/unit
pytest -q .tests/unit
```

Keep CI report generation separate from full production runs unless the report inputs are small and already materialized.
