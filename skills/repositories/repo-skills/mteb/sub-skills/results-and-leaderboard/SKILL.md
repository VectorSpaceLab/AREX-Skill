---
name: results-and-leaderboard
description: "Load, inspect, validate, submit, and display MTEB result caches,
  BenchmarkResults/TaskResult objects, model-card result metadata, and local
  leaderboards."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Results and Leaderboard

Use this sub-skill when the user already has MTEB results and needs to inspect cached JSON files, load results into Python objects or dataframes, validate folder layout, prepare model-card result tables, submit results, or run a local leaderboard.

## Route First

- To produce new result files with `mteb.evaluate(...)`, `ResultCache`, overwrite strategies, prediction folders, or failure-tolerant evaluation, use `../evaluation-workflows/SKILL.md`.
- For shell automation around `mteb create-model-results`/model-card metadata generation, `mteb leaderboard`, and result-producing `mteb run`, use `../cli-and-automation/SKILL.md`.
- For official contribution process, result PR expectations, suspicious-score review, and repository contribution etiquette, use `../contributing-to-mteb/SKILL.md`.
- For choosing tasks, benchmarks, task filters, private/beta/superseded defaults, or legal-domain retrieval task selection, use `../tasks-and-benchmarks/SKILL.md` before loading or comparing results.
- For model metadata, revisions, model cards, custom model wrappers, or missing `model_meta.json`, use `../models-and-encoders/SKILL.md`.

## Common Workflows

- **Inspect a result folder offline:** Run `python scripts/inspect_mteb_results.py mteb-results-cache --require-model-meta` to summarize model/revision folders, task JSON files, missing metadata, and malformed scores without network access.
- **Load cached results:** Create `cache = mteb.ResultCache(cache_path="mteb-results-cache")`, then call `cache.load_results(models=[...], tasks=[...], require_model_meta=True, include_remote=True)`.
- **Build a dataframe:** Use `BenchmarkResults.to_dataframe(aggregation_level="task", format="long")` for one row per model/task, or `format="wide"` for a comparison matrix.
- **Compare benchmark scores:** Load with a benchmark object or benchmark name, then call `results.get_benchmark_result()`; this requires results to be associated with one `Benchmark`.
- **Recover model/revision folders without metadata:** Retry loading with `require_model_meta=False` for diagnostics, but add or regenerate `model_meta.json` before publication/submission.
- **Submit results:** Use `ResultCache.submit_results(models=[...], create_pr=False)` for manual review first; `create_pr=True` requires GitHub dependencies and authentication.
- **Run a local leaderboard:** Use the CLI `mteb leaderboard --cache-path mteb-results-cache --port 7860`; add `--rebuild` when cached leaderboard data is stale.

## References

- `references/results-cache.md` covers cache layout, `ResultCache` APIs, loading options, result objects, dataframe conversion, and validation signals.
- `references/leaderboard-and-results.md` covers local/remote results, benchmark tables, model-card result metadata, submission flow, and local leaderboard caveats.
- `references/troubleshooting.md` maps common install/import, optional-extra, dataset access, CLI/API, cache-path, and filtering failures to fixes.
- `scripts/inspect_mteb_results.py` is a safe offline cache/result-folder inspector for CI, handoff checks, and missing-metadata diagnosis.

## Quick Validation

```bash
python -c "import mteb; print(mteb.__version__)"
python scripts/inspect_mteb_results.py mteb-results-cache --require-model-meta
mteb leaderboard --cache-path mteb-results-cache --rebuild --port 7860
```

Expected healthy signals: `import mteb` succeeds, `pip check` is clean, result folders contain task JSON files under model/revision directories, publishable result folders include `model_meta.json`, and dataframe outputs have non-empty `model_name`, `task_name`, and `score` columns.
