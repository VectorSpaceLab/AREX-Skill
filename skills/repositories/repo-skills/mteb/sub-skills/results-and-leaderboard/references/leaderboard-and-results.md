# Leaderboard, Model Cards, and Result Submission

## Local and Remote Result Sources

MTEB can combine local evaluation output with public remote results.

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
cache.download_from_remote()  # requires Git and network access
results = cache.load_results(include_remote=True)
```

Key distinctions:

- Local results are under `<cache>/results/` and are usually created by `mteb.evaluate(...)` or `mteb run`.
- Public results downloaded from the official results repository are under `<cache>/remote/results/`.
- `include_remote=True` includes both local and downloaded remote files; `include_remote=False` restricts loading to local result files.
- `prioritize_remote=True` on `load_task_result(...)` prefers the remote copy when both local and remote results exist.
- `download_from_remote(download_latest=True, revision=None)` updates or clones the public repository; pin `revision` only when reproducibility requires a specific results snapshot.

## Benchmark Tables

Create benchmark summary tables only after loading with a `Benchmark` object or benchmark name.

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
benchmark = mteb.get_benchmark("MTEB(eng, v2)")
results = cache.load_results(
    models=["intfloat/e5-small", "intfloat/multilingual-e5-small"],
    tasks=benchmark,
)
summary = results.get_benchmark_result()
```

Expected signals:

- `summary` is a pandas dataframe.
- Rank columns may include `Rank (Borda)`, `Rank (Mean Task)`, or benchmark-specific rank columns.
- Score columns are benchmark-dependent and may be task-type columns, task columns, language columns, or aggregate means.
- Calling `get_benchmark_result()` without a benchmark raises a value error; reload with `tasks=mteb.get_benchmark(...)`.
- Loading multiple benchmarks at once is supported for dataframes, but `get_benchmark_result()` expects one benchmark.

## Local Leaderboard

CLI pattern:

```bash
mteb leaderboard --cache-path mteb-results-cache --host 0.0.0.0 --port 7860
```

Useful options:

- `--cache-path PATH`: cache folder containing `results/`, `remote/`, and `leaderboard/` data.
- `--rebuild`: bypasses precomputed leaderboard parquet cache and rebuilds from result JSON files.
- `--host HOST`: server host, default `0.0.0.0`.
- `--port PORT`: server port, default `7860`.
- `--share`: asks Gradio for a public share URL.

Python pattern:

```python
from mteb import ResultCache
from mteb.leaderboard import get_leaderboard_app

cache = ResultCache(cache_path="mteb-results-cache")
app = get_leaderboard_app(cache=cache, rebuild=True)
app.launch(server_name="0.0.0.0", server_port=7860)
```

Caveats:

- The leaderboard requires optional UI dependencies; install the leaderboard extra if importing `mteb.leaderboard` fails.
- Startup can be expensive when `--rebuild` is set or no local parquet cache exists.
- The app can load precomputed benchmark parquet data when available; use `--rebuild` after adding new local JSON results.
- Missing task metadata, malformed result JSON, or missing model metadata can reduce displayed rows even when files exist.
- Public share links expose the running app; do not use `--share` for private model or benchmark data unless intentional.

## Model-Card Result Metadata

The CLI exposes model-card result generation through the `create-meta` workflow. Check `mteb create-meta --help` before scripting exact flags because model-card metadata options can vary by installed MTEB release.

```bash
mteb create-meta \
  --model-name sentence-transformers/all-MiniLM-L6-v2 \
  --results-folder mteb-results-cache \
  --tasks STS12 Banking77Classification \
  --output-path model_card.md \
  --overwrite
```

Common option names to verify against `--help`:

- `--model-name`: model identifier to summarize.
- `--tasks`: task names to include; omit to use all matching task results.
- `--benchmarks`: benchmark names to use for benchmark-aware sections when supported.
- `--results-folder` or equivalent cache/results option: folder containing cached results.
- `--output-path` or equivalent output option: markdown path to write.
- `--from-existing`: path or model id for merging with an existing README/model card when supported.
- `--overwrite`: replace an existing output file when supported.

When using the root skill or CLI reference, route this as the `create-meta`/model-card metadata workflow and verify the installed subcommand with `mteb --help`.

## Submitting Results

Start with manual submission unless the user explicitly wants automated PR creation.

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
submission = cache.submit_results(
    models=["sentence-transformers/all-MiniLM-L6-v2"],
    create_pr=False,
)
print(submission["status"], submission.get("path"))
```

Return statuses include:

- `ready_for_submission`: files were copied into a submission branch in the downloaded remote repository and manual push/PR instructions were logged.
- `pr_created`: automated PR creation succeeded; response may include `pr_url`, `pr_number`, and `fork_url`.
- `no_changes`: no unsubmitted local results were found for the selected models.

Manual submission requirements:

- Git installed and usable.
- Local result files under `<cache>/results/`.
- A valid `model_meta.json` with model name and revision for each submitted model/revision.
- Review of generated diff before opening a PR.

Automated submission requirements:

- Git installed and usable.
- GitHub CLI or credentials configured, depending on the chosen auth flow.
- MTEB GitHub optional dependencies installed, commonly with the GitHub extra.
- User consent to create branches/forks/PRs from the active environment.

Submission review expectations:

- Fill out the PR checklist.
- Be ready to explain suspicious scores or possible data leakage.
- Ensure results were produced with the intended task splits, subsets, model revision, and MTEB version.
- Prefer `create_pr=False` for dry-run/manual review in CI workflows or internal benchmark processes.

## Local/Remote Comparison Recipe

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
cache.download_from_remote()

tasks = mteb.get_tasks(task_types=["Retrieval"], languages=["eng", "fra"], domains=["Legal"])
results = cache.load_results(
    models=["GritLM/GritLM-7B", "intfloat/multilingual-e5-large"],
    tasks=tasks,
    include_remote=True,
    validate_and_filter=True,
)

df = results.to_dataframe(aggregation_level="task", format="long")
print(df.sort_values(["task_name", "score"], ascending=[True, False]).head())
```

Expected signals:

- Selected task objects reflect the requested task type, language, and domain filters.
- `validate_and_filter=True` removes scores outside current default splits/subsets for those task objects.
- The dataframe may be empty if no selected model has results for the selected tasks; inspect `cache.get_task_names(...)` and `cache.get_models(...)` to diagnose.

## Offline Sanity Checks

Before sharing reports or opening submissions:

- Load a small local cache with `ResultCache(...).load_results(require_model_meta=False)` and confirm the returned `BenchmarkResults` contains the expected task names.
- Convert selected `BenchmarkResults` to long and wide dataframes and confirm required columns such as `model_name`, `task_name`, and `score` are present.
- Use `select_models`, `select_tasks`, and `join_revisions` when a cache contains multiple model revisions.
- Avoid remote downloads while diagnosing local folders; inspect downloaded public results separately under `remote/results/`.
- Start a leaderboard only in an environment with `mteb[leaderboard]`; prefer dataframe checks when a long-running UI server is unnecessary.
