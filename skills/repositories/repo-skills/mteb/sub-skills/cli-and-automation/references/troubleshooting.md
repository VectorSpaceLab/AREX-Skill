# CLI Troubleshooting

Use this guide to diagnose MTEB CLI failures without confusing command-line issues with task, model, dataset, or result-cache problems.

## Install Or Import Issues

Symptoms:

- `mteb: command not found`
- `python -m mteb --help` fails
- `ModuleNotFoundError: No module named 'mteb'`
- `pip check` reports incompatible installed packages

Checks and fixes:

```bash
python -c "import mteb; print(mteb.__version__)"
python -m pip check
python -m mteb --help
mteb --help
```

- If `python -m mteb --help` works but `mteb --help` does not, the console script is not on `PATH`; call `python -m mteb` or fix the active environment path.
- If import fails, install the public `mteb` package into the environment that will run the command.
- If `pip check` fails, repair dependency conflicts before trusting evaluation results.

## Optional Dependency Extras

Symptoms:

- `mteb leaderboard` fails with an import error mentioning missing packages.
- CO₂ tracking or model backend integrations fail only when a specific feature is enabled.

Checks and fixes:

- Install the relevant package extra when available, such as the leaderboard extra for `mteb leaderboard`.
- Disable optional features when they are not required, for example `--no-co2-tracker`.
- Use `mteb <subcommand> --help` after installing extras to confirm command parsing before launching long-running jobs.

## Dataset Downloads And Private Access

Symptoms:

- `mteb run` parses successfully but fails while loading a dataset.
- Hugging Face access errors appear for gated or private datasets.
- Air-gapped or offline jobs fail after command validation succeeds.

Checks and fixes:

- Confirm the task inventory with `mteb available-tasks` before running.
- Prefer public stable tasks in automation unless credentials and dataset access are intentionally configured.
- For private, beta, superseded, aggregate, modality, or script-specific filtering, use Python `mteb.get_tasks(...)` options described in `tasks-and-benchmarks`; the CLI exposes only a subset of those filters.
- Treat help-command success as CLI validation only, not proof that datasets can be downloaded.

## CLI/API Misuse

Symptoms:

- `argparse` reports unrecognized arguments.
- A broad task-filter run evaluates a different set of tasks than expected.
- A benchmark run logs a warning that task filters are ignored.

Checks and fixes:

- Re-run `mteb <command> --help` in the active environment and use exactly the command names shown there.
- Use hyphenated command names such as `available-tasks`, `available-benchmarks`, and current metadata command names shown by `mteb --help`.
- Do not combine `--benchmarks` with `--tasks`, `--languages`, `--task-types`, `--categories`, or `--eval-splits`; benchmark selection owns the task list and those filters are ignored.
- Prefer `--overwrite-strategy always` instead of deprecated `--overwrite`.
- Prefer `--prediction-folder` instead of deprecated `--save_predictions`.

## Cache And Result Path Mistakes

Symptoms:

- `create-model-results` cannot find expected scores.
- A generated model card is missing tasks that were run.
- `leaderboard` launches but does not show the expected model.
- A rerun appears to skip tasks unexpectedly.

Checks and fixes:

- Distinguish the output root from the model/revision folder. `mteb run --output-folder results` writes under a model-name and revision-specific hierarchy; metadata generation usually needs the folder that contains the task JSON files for that model/revision.
- Verify result files exist before creating metadata:

```bash
find results -name 'model_meta.json' -o -name '*.json' | head
```

- If a revision folder is wrong, point `--results-folder` at the exact revision folder that contains `model_meta.json` and task result JSON files.
- If a rerun should update existing results, choose an explicit `--overwrite-strategy`; `only-missing` will not rerun completed splits just because dataset revision or MTEB version changed.
- Keep predictions separate with `--prediction-folder` so prediction files are not mistaken for result metadata.

## Beta, Superseded, Private, And Aggregate Filtering

Symptoms:

- CLI task listings include or omit tasks differently than a Python workflow.
- A user expects private, beta, superseded, aggregate, script, domain, or modality filters from the CLI.

Checks and fixes:

- The Python `mteb.get_tasks(...)` API includes filters such as `exclude_superseded=True`, `exclude_private=True`, `exclude_beta=True`, `exclude_aggregate=False`, `script`, `domains`, `modalities`, and exclusive language/modality filters.
- The CLI task selection exposes common filters such as `--tasks`, `--languages`, `--task-types`, `--categories`, and, for runs, `--eval-splits`.
- For exact reproducibility involving beta/private/superseded filtering, use Python API automation and document the filter values.

## Hard Cases To Test

- **Benchmark plus filters warning**: User runs `mteb run --benchmarks "MTEB(eng, v1)" --tasks Banking77Classification --languages eng`. Expected guidance: explain that benchmark selection wins and task/language filters are ignored; propose either a benchmark-only command or a task-filter-only command.
- **Wrong metadata cache revision**: User runs metadata generation against `results/<model>` instead of `results/<model>/<revision>` and sees missing or incomplete model-card data. Expected guidance: inspect for `model_meta.json` and task JSON files, identify the exact revision folder, then rerun `mteb create-model-results --results-folder <model-revision-folder> --output-path model_card.md --overwrite`.
