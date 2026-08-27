# Results and Leaderboard Troubleshooting

## Import or Install Issues

Symptoms:

- `ModuleNotFoundError: No module named 'mteb'`.
- `ImportError` when importing `mteb.leaderboard`.
- `pip check` reports incompatible packages.

Actions:

- Confirm the active environment with `python -c "import mteb; print(mteb.__version__)"`.
- Run `pip check` before debugging result logic; dependency conflicts can break pandas, polars, pydantic, datasets, or Gradio paths.
- Install optional extras only for needed workflows: leaderboard UI needs the leaderboard extra, automated GitHub submission needs GitHub-related extras, CO2 tracking needs the codecarbon extra.
- If only inspecting local JSON, use `scripts/inspect_mteb_results.py`; it avoids importing MTEB and does not need optional extras.

## Optional Dependency Extras

Symptoms:

- `mteb leaderboard` says dependencies are missing.
- Importing `gradio`, `polars`, `datasets`, or GitHub submission dependencies fails.
- Automated PR submission fails before creating a PR.

Actions:

- For local leaderboard UI, install the leaderboard extra, then retry `mteb leaderboard --cache-path <cache>`.
- For automated submission with `create_pr=True`, install GitHub extras and configure credentials first.
- For safer review, use `cache.submit_results(..., create_pr=False)`; this still requires Git but avoids authenticated PR automation.
- Keep result loading and dataframe inspection separate from UI/submission flows so optional-extra issues do not block basic diagnostics.

## Dataset Downloads and Private Access

Symptoms:

- Loading or validating selected task results triggers dataset access errors.
- Private or gated datasets fail in evaluation, but cached JSON files exist.
- Expected tasks are absent after task selection.

Actions:

- Loading raw JSON with `ResultCache.load_results(validate_and_filter=False)` should not require dataset downloads for existing files.
- `validate_and_filter=True` needs current task objects and can surface task metadata/access issues; use it when checking publishability or benchmark consistency.
- For task selection, remember current defaults exclude private and beta tasks and exclude superseded tasks unless filters are changed in task discovery.
- If private task results are intentional, verify the user has dataset access and avoid exposing private result folders through `mteb leaderboard --share`.
- Use the task-selection sub-skill for `exclude_private`, `exclude_beta`, `exclude_superseded`, language, modality, and benchmark filter decisions.

## CLI and API Misuse

Symptoms:

- `mteb create-model-results` flags differ from an example or the subcommand is not found.
- `get_benchmark_result()` raises `No benchmark associated with these results`.
- `load_task_result(...)` returns `None` for a file that appears to exist.
- `mteb leaderboard --cache-path results` shows no rows.

Actions:

- Check installed CLI subcommands with `mteb --help`; current entry point includes `run`, `available-tasks`, `available-benchmarks`, `create-model-results`, and `leaderboard`.
- Check model-card metadata flags with `mteb create-model-results --help` before scripting because result-folder/output option names can vary by release.
- Load benchmark summaries with `benchmark = mteb.get_benchmark("MTEB(eng, v2)")` and `cache.load_results(tasks=benchmark)`, then call `results.get_benchmark_result()`.
- Pass a `ModelMeta` or both a model string and the correct revision to `load_task_result(...)`; folder-normalized names can differ from canonical names.
- For CLI `mteb run`, `--output-folder` is a `ResultCache` root; do not point later loaders at `<cache>/results` unless the API specifically expects the inner folder.

## Cache and Result Path Mistakes

Symptoms:

- `cache.get_cache_paths()` returns an empty list.
- `require_model_meta=True` hides many files.
- Inspector reports task JSON files outside model/revision directories.
- Folder has `model_name/revision/task.json` but the loader cannot identify the model.

Actions:

- Point `ResultCache(cache_path=...)` at the cache root containing `results/`, not directly at one model directory.
- Use `include_remote=False` to confirm local files before submission; use `include_remote=True` to include downloaded public results.
- Retry `cache.get_cache_paths(require_model_meta=False)` to discover legacy/incomplete folders.
- Add valid `model_meta.json` before model-card generation, leaderboard publication, or `submit_results(...)`.
- Inspect with `python scripts/inspect_mteb_results.py <cache> --require-model-meta --json` to identify missing metadata and malformed task JSON.
- Remember model folder names may use `__` where canonical model names use `/`; prefer `ModelMeta` objects when exact revision matching matters.

## Beta, Superseded, Private, and Filter Surprises

Symptoms:

- Results exist in cache but selected tasks exclude them.
- A `.v2` result appears while the user asked for the older task name.
- Public leaderboard rows differ from local ad hoc dataframes.

Actions:

- `mteb.get_tasks(...)` defaults normally exclude private, beta, and superseded tasks and can filter aggregate tasks depending on parameters.
- Use exact task names, including version suffixes such as `.v2`, when loading task-specific result files.
- Use `validate_and_filter=True` when comparing against current task metadata; use `False` when diagnosing historical JSON files.
- If a task was renamed or superseded, compare `cache.get_task_names(require_model_meta=False)` with the current task registry before concluding results are missing.
- For benchmark tables, load the benchmark object and let MTEB filter splits/subsets according to that benchmark rather than manually slicing file names.

## Malformed or Incomplete Result JSON

Symptoms:

- `TaskResult.from_disk(...)` raises validation errors.
- Dataframes are empty or `score` values are missing.
- Inspector reports missing `scores`, no split entries, or missing `main_score`.

Actions:

- Confirm each task JSON has `task_name`, `dataset_revision`, `mteb_version`, `scores`, and `evaluation_time` where available.
- Each `scores` split should contain a list of score dictionaries; each dictionary should usually include `main_score`, `hf_subset`, and `languages`.
- Re-run evaluation for malformed files rather than hand-editing scores unless the user is only recovering metadata.
- If merging partial subsets, use `TaskResult.is_mergeable(...)` and `TaskResult.merge(...)` rather than manual JSON concatenation.
- Use `only_main_score=True` in `load_results(...)` to reduce payload when downstream code only needs aggregate scores.

## Submission Failures

Symptoms:

- `submit_results(...)` returns `no_changes`.
- Git errors mention dirty repository, detached HEAD, or failed branch creation.
- Automated PR creation fails after copying files.

Actions:

- Confirm local, not remote, result files exist with `cache.get_cache_paths(include_remote=False, require_model_meta=True)`.
- Confirm selected model names/revisions match `model_meta.json`; use `cache.get_models(include_remote=False)` for a quick list.
- Use `create_pr=False` first to prepare a manual submission branch and inspect the copied diff.
- Clean or reset the downloaded remote results repository only with user approval; submission code performs pre-flight checks to avoid overwriting work.
- For automated PRs, authenticate with the required GitHub flow and install GitHub extras before retrying.

## Leaderboard Failures

Symptoms:

- App starts slowly or appears stuck during initialization.
- New local results do not appear.
- UI dependency import fails.
- The app exposes private results unexpectedly.

Actions:

- Use `mteb leaderboard --cache-path <cache> --rebuild` after adding or changing result JSON files.
- Avoid `--rebuild` for routine startup when the local parquet cache is valid.
- Install the leaderboard extra when Gradio or UI imports fail.
- Confirm the cache root contains the expected `results/` or `remote/results/` directories.
- Do not pass `--share` when the cache includes private, internal, or unreviewed results.
- For automated tests, prefer dataframe-level checks over launching a long-running UI server.
