# Troubleshooting MTEB Contributions

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'mteb'`
- `ImportError` from a model implementation module
- `pip check` reports incompatible dependencies

Fixes:

- Verify the active environment with `python -c "import mteb; print(mteb.__version__)"`.
- Run `python -m pip check` before debugging contribution code.
- Avoid adding mandatory dependencies for provider-specific or modality-specific models unless they are already core dependencies.
- For optional model dependencies, add an optional dependency group and set `ModelMeta(extra_requirements_groups=["group-name"])`.
- Move optional imports inside the loader or wrapper constructor so `import mteb` and metadata discovery work without the extra installed.

## Optional Dependency Breaks Model Discovery

Symptom:

- Adding a model requiring a provider SDK causes `import mteb` or `mteb.get_model_metas()` to fail for users without that SDK.

Fix:

```python
class ProviderModel:
    def __init__(self, model_name: str, revision: str | None = None, **kwargs):
        import provider_sdk
        self.client = provider_sdk.Client(...)
```

Then set `extra_requirements_groups=["provider"]` in `ModelMeta` and document that users install `mteb[provider]` before loading that model.

## Dataset Download or Access Fails

Symptoms:

- Hugging Face `RepositoryNotFoundError`, `GatedRepoError`, or authentication errors.
- Private task unexpectedly skipped or unavailable.
- Dataset loads locally for the contributor but not for reviewers.

Fixes:

- Confirm `metadata.dataset["path"]` points to the intended Hub dataset and `metadata.dataset["revision"]` is a stable commit or tag.
- Keep `metadata.dataset.get("trust_remote_code", False) is False`; MTEB tests reject trusted remote code for datasets.
- For closed datasets, set `is_public=False`, document token/access requirements, and do not expect default public-only workflows to run it.
- If the dataset is still being checked, set `is_beta=True`; remember default task discovery excludes beta tasks.
- Do not use local files or checkout-relative paths in public task metadata.

## Metadata Validation Fails

Symptoms:

- `ValidationError` during `TaskMetadata(...)` construction.
- `metadata._validate_metadata()` raises a language-code error.
- `metadata.is_filled()` is false.
- Native metadata tests complain about missing descriptive stats.

Fixes:

- Ensure `dataset` contains both `path` and a non-null `revision`.
- Use language/script tags such as `eng-Latn`; for multilingual subsets, use a mapping like `{ "en-fr": ["eng-Latn", "fra-Latn"] }`.
- Fill required public metadata fields: `reference`, `date`, `domains`, `task_subtypes`, `license`, `annotations_creators`, `dialect`, `sample_creation`, and `bibtex_citation`.
- Use `dialect=[]` when no dialect applies and `bibtex_citation=""` only when no citation is available.
- Generate descriptive statistics with `task.calculate_descriptive_statistics()` after data loading works.
- Run `python scripts/check_task_metadata.py --task-class module:Class --require-filled --require-descriptive-stats` to isolate metadata issues before full tests.

## CLI or API Misuse

Symptoms:

- `mteb run` cannot find a task or model.
- Python code passes task names where task objects are expected, or vice versa.
- Cache-only evaluation fails with missing results.

Fixes:

- For task discovery, inspect `mteb.get_tasks(...)`, `mteb.get_task(...)`, and `mteb available-tasks` before evaluation.
- For benchmark selection, use `mteb.get_benchmark("Benchmark Name")` and pass the benchmark or its tasks to evaluation.
- For direct evaluation, pass a model object or `ModelMeta` and a task object, list of tasks, or benchmark.
- Set an explicit `mteb.ResultCache(cache_path="mteb-results-cache")` for reproducible runs.
- Use `overwrite_strategy="only-missing"` for normal resumable runs; use `"only-cache"` only when the cache is known to contain complete results.

## Cache or Result Path Mistakes

Symptoms:

- Results appear missing between runs.
- Submission picks up stale files.
- Prediction files are written somewhere unexpected.

Fixes:

- Set `ResultCache(cache_path="...")` explicitly and keep one cache per review scenario when comparing implementations.
- Use `overwrite_strategy="always"` only when intentionally replacing results.
- Use `prediction_folder="predictions"` only for tasks where prediction files are needed and keep it outside source packages.
- Before submission, inspect cached result JSON and model metadata for the intended model name, revision, task name, split, subset, and MTEB version.

## Beta, Superseded, or Private Task Filtering Surprises

Symptoms:

- A new task does not appear in `mteb.get_tasks()`.
- A benchmark is missing tasks after filtering.
- A user can load a task by name but it is absent from default lists.

Fixes:

- Default discovery excludes private tasks, beta tasks, and superseded tasks.
- Use `mteb.get_tasks(exclude_private=False, exclude_beta=False, exclude_superseded=False)` while debugging intentional non-default tasks.
- Use `exclude_aggregate=False` when aggregate tasks are intentionally part of a check.
- For language filtering, distinguish ISO language-only filters such as `languages=["eng"]` from script-aware metadata fields such as `eval_langs=["eng-Latn"]`.
- If a benchmark uses beta or private tasks, document that users must opt into those tasks and may need access credentials.

## Difficult Contribution Scenarios

### Multilingual Retrieval Missing Key Metadata

Problem: a multilingual retrieval task has `eval_langs` as a flat list, no dataset revision, and `main_score` omitted.

Expected recovery:

- Use a subset-to-language mapping for `eval_langs` when Hugging Face subsets encode language pairs.
- Add a pinned `dataset.revision`.
- Set `main_score="ndcg_at_10"` or another metric emitted by the retrieval evaluator.
- Generate descriptive statistics after data loads.
- Smoke-evaluate with `mteb/baseline-random-encoder` before adding benchmark results.

### Optional Model Dependency Imported at Top Level

Problem: a provider SDK import at module top-level breaks all users without that SDK.

Expected recovery:

- Move `import provider_sdk` inside the model loader constructor or method that actually needs it.
- Add the package under optional dependencies.
- Set `extra_requirements_groups=["provider"]` in `ModelMeta`.
- Verify `import mteb` and `mteb.get_model_meta("model-name")` work without the optional extra, while `mteb.get_model("model-name")` gives a clear install message if the extra is absent.
