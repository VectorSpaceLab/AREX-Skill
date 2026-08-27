---
name: result-analysis
description: "Routes evo_res workflows, saved-result comparison, table export,
  and result-label hygiene."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# result-analysis

Use this sub-skill for saved evo result archives, result comparison, and tabular exports.

## Route here when the user asks for
- `evo_res` or saved-result comparison
- merging, plotting, or exporting `.zip` result files
- `load_res_file`, `save_res_file`, `load_results_as_dataframe`, or `merge_results`
- `save_df_as_table`, pandas conversion, or result-table generation
- renaming `est_name` in a result archive

## Do not route here when the task is mainly about
- APE/RPE metric computation
- raw trajectory loading/conversion or bag routes
- package settings, logs, or IPython shell setup
- notebook plotting or custom Python embedding unless the task is specifically about saved result files

## Start with
1. [references/cli-reference.md](references/cli-reference.md)
2. [references/api-reference.md](references/api-reference.md)
3. [references/workflows.md](references/workflows.md)
4. [references/troubleshooting.md](references/troubleshooting.md)
5. [scripts/result_smoke.py](scripts/result_smoke.py)

## Rules of thumb
- A valid evo result archive always has `info.json` and `stats.json`.
- `.npy`/`.npz` members hold result arrays; trajectory backups are optional.
- `merge_results` averages arrays when lengths match and appends when they differ.
- `--ignore_title` is the safe escape hatch when comparing results from different metric titles.
- `--use_filenames` is helpful when the embedded `est_name` labels collide.
- The safe rename helper in this sub-skill writes to an explicit output file unless you intentionally choose an in-place overwrite.
