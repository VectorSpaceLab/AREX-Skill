# Troubleshooting debugging and reporting

## Lint exits non-zero but the workflow dry-runs

Likely cause: `--lint` reports quality suggestions and returns failure when findings exist.

Actions:

- Read the lint body before editing. Many findings are portability/provenance warnings, not parser errors.
- Use `snakemake --lint json > lint.json` when CI needs to distinguish known warnings from new ones.
- Prioritize missing `log:`, missing software definitions, absolute paths, undeclared environment variables, and direct shell use of external variables.
- Route substantive Snakefile refactors to `../../workflow-authoring/SKILL.md`.

## Graph output cannot render

Likely causes: top-level `print()` output is mixed into DOT/Mermaid text, Graphviz is not installed, or the selected graph type is too crowded.

Actions:

- Save raw graph output first: `snakemake --dag > dag.dot`.
- Inspect the first lines for non-DOT text from the Snakefile.
- Switch from `--dag` to `--rulegraph` for high-cardinality wildcard workflows.
- Use `--debug-dag --cores 1 --dry-run` to inspect selected jobs and wildcards when topology is unexpected.

## Report is missing runtime statistics

Likely cause: report rendering depends on provenance/runtime metadata stored under `.snakemake`.

Actions:

- Run the workflow successfully before `snakemake --report report.html`.
- Avoid deleting `.snakemake` metadata before rendering reports.
- Use `snakemake --summary` to verify tracked outputs and stale/missing status.
- For large or networked metadata stores, route persistence-backend choices to deployment/storage guidance.

## Report output is absent, uncategorized, or poorly grouped

Likely causes: outputs were not wrapped with `report()`, category/subcategory functions returned invalid values, directory patterns did not match files, or labels were omitted.

Actions:

- Confirm the Snakefile uses `output: report("path", caption="...", category="...")` for each desired result.
- For directory outputs, add `patterns=["{name}.txt"]` or `htmlindex="index.html"` as appropriate.
- Ensure `category`, `subcategory`, and `labels` functions return strings/numbers or dictionaries of string keys to string/number values.
- Prefer labels for sample/model/condition dimensions instead of relying on raw filenames.

## Report captions or metadata fail

Likely causes: invalid reStructuredText, missing caption paths, Jinja2/YTE template errors, or private/nonportable metadata.

Actions:

- Resolve caption paths relative to the Snakefile.
- Reduce the failing caption to plain text, regenerate, then reintroduce links/math/Jinja2 gradually.
- Keep `--report-metadata` values portable; do not embed private paths, interpreter paths, or machine-specific locations.
- Check references such as `Rules_`, `Statistics_`, category names, and reported basenames for spelling.

## Custom report stylesheet does not apply

Likely causes: CSS path is wrong, assets referenced by CSS are not portable, or the wrong report entry point is opened.

Actions:

- Run `snakemake --report report.html --report-stylesheet custom.css` from the workflow directory.
- Prefer self-contained CSS or data URI assets for logos.
- For ZIP reports, unpack the archive and open its contained `report.html`.

## Notebook rule fails before user code runs

Likely causes: missing Jupyter/nbconvert/papermill dependencies, unsupported notebook extension, duplicate Snakemake preamble cells, or an environment mismatch.

Actions:

- Confirm the notebook path ends in `.ipynb`.
- Inspect the notebook for multiple cells tagged `snakemake-job-properties`; keep at most one.
- Add `log: notebook="logs/rule.ipynb"` so the executed notebook is preserved.
- Use `--show-failed-logs` and `--printshellcmds` for the failing target.
- Route environment and deployment dependency installation to `../../deployment-storage/SKILL.md` when execution backends are involved.

## Generated unit tests skip rules

Likely cause: Snakemake only generates a test for a rule when a representative job has all input files present.

Actions:

- Execute a tiny fixture workflow first: `snakemake --cores 1 --notemp --show-failed-logs`.
- Then run `snakemake --generate-unit-tests .tests/unit`.
- Check generator warnings for rules with no complete job inputs.
- Do not generate tests from large production data; use small fixtures and review copied files.

## Generated unit tests fail output comparison

Likely causes: nondeterministic outputs, timestamps, compressed files with different metadata, or binary formats needing semantic comparison.

Actions:

- Inspect `.tests/unit/common.py` and the failing `test_<rule>.py`.
- Override comparison commands for specific suffixes in the generated test.
- For text outputs, use `diff` options that ignore accepted volatile lines.
- For domain formats, call a semantic comparator such as a table diff or BAM comparator if available in the test environment.

## Failed logs are not shown

Likely causes: rules lack `log:` directives, the failing command does not write STDERR to the log file, or executor-specific logs live elsewhere.

Actions:

- Add `log:` entries to rules that execute commands.
- Run with `--show-failed-logs --printshellcmds`.
- For Python scripts, redirect `sys.stderr` to `snakemake.log[0]` with line buffering.
- For R scripts, sink messages to the log and consider saving `workspace.RData` near the failure.
- Route remote executor log locations to deployment/storage guidance.

## Runtime profile is empty or unavailable

Likely causes: `yappi` is not installed, the run failed before profiling wrote data, or the profile is being interpreted as per-tool benchmarking.

Actions:

- Install/enable `yappi` in the active Snakemake environment if allowed by the user.
- Run a narrow target: `snakemake target --cores 1 --runtime-profile runtime-profile.txt`.
- Interpret it as Snakemake Python-process profiling, not as shell tool CPU/memory benchmarking.
- Use rule `benchmark:` outputs for per-job runtime/resource measurement.

## Benchmark output has unexpected shape

Likely causes: benchmark path suffix controls format, `repeat()` creates multiple records, or extended fields depend on platform support.

Actions:

- Use `.jsonl` benchmark paths when downstream tooling expects JSON lines.
- Use `.tsv` or another non-`.jsonl` suffix when a tabular header is desired.
- Add `--benchmark-extended` for additional metrics, but tolerate unavailable fields on platforms that cannot expose them.
- Treat `NA` memory metrics as unavailable data, not necessarily zero usage.

## CI smoke check is flaky or too slow

Likely causes: CI executes production targets, generates tests from large data, or requires optional notebook/report dependencies.

Actions:

- Keep default smoke to `--dry-run`, `--lint json`, and `--rulegraph`.
- Add real execution only for tiny fixtures.
- Generate unit tests only after a successful tiny run with `--notemp`.
- Skip notebook/report checks explicitly when extras are unavailable instead of failing unrelated CI.
