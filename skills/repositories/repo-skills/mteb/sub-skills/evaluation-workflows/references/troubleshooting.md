# Evaluation Troubleshooting

## Import or Installation Fails

Symptoms:

- `ModuleNotFoundError: No module named 'mteb'`
- `pip check` reports incompatible dependencies
- `mteb.evaluate` signature does not include expected options such as `overwrite_strategy` or `prediction_folder`

Recovery:

1. Verify the active environment: `python -c "import mteb, inspect; print(mteb.__version__); print(inspect.signature(mteb.evaluate))"`.
2. Install or upgrade the public package: `pip install -U mteb`.
3. Add optional extras only when needed, for example `mteb[codecarbon]` for CO2 tracking, `mteb[image]` for image tasks, or `mteb[xet]` for faster Hugging Face downloads.
4. Re-run `pip check` after dependency changes.

## CO2 Tracking Raises an Import Error

Symptom:

- `ImportError` says CodeCarbon is required when `co2_tracker=True`.

Recovery:

- Install the optional extra that provides CodeCarbon, or set `co2_tracker=False` for deterministic smoke tests and CI.
- Leave `co2_tracker=None` only when it is acceptable for behavior to depend on whether CodeCarbon is installed.

## Dataset Download or Private Access Fails

Symptoms:

- `DatasetNotFoundError`
- Warning text similar to `Dataset for private task ... not found`
- Empty `task_results` for a private task
- Authentication or permission errors from Hugging Face datasets

Recovery:

1. Confirm the task is intended to be private or public with task metadata or `mteb.get_tasks(..., exclude_private=True)`.
2. For public-only runs, filter before evaluation with `exclude_private=True`, `exclude_beta=True`, and `exclude_superseded=True`; pass `public_only=True` for clarity.
3. For intentionally private runs, authenticate with the dataset host and pass `public_only=False` so access problems raise immediately.
4. If a task is beta or superseded, decide explicitly whether to include it; otherwise keep default filtering in task selection.
5. If downloads are slow rather than failing, install download acceleration extras when appropriate and retry with a stable cache directory.

## `only-cache` Raises `ValueError`

Symptom:

- `overwrite_strategy is set to 'only-cache' but no results found in cache...`
- Error reports missing splits/subsets even though a result file exists.

Meaning:

`only-cache` is a strict read path. It will not evaluate missing normal-task work. It requires a compatible cache entry for the exact task, model name, model revision, experiment kwargs, split, and subset combination.

Recovery:

1. Run the same model and task once with `overwrite_strategy="only-missing"` or `"always"` to populate cache.
2. Reuse the same `ResultCache(cache_path=...)` on the cache-only run.
3. Check whether `embed_dim`, model loader kwargs, revision, or `encode_kwargs` changed and therefore altered cache paths or experiment metadata.
4. If the cache intentionally contains only part of a task, use `only-missing` to complete it before switching to `only-cache`.

## Cache Reuse Looks Wrong

Symptoms:

- Results do not rerun after code/model changes.
- Results rerun unexpectedly.
- Cache files appear under an unexpected directory.

Recovery:

- Use an explicit `mteb.ResultCache(cache_path="...")` instead of relying on the default cache or environment variables.
- Use `overwrite_strategy="always"` after changing model code, preprocessing, task revisions, or important encode settings.
- Use `overwrite_strategy="never"` when preserving existing results matters more than updating them.
- Use `overwrite_strategy="only-missing"` to resume partial evaluations.
- Remember that MTEB saves intermediate cache entries during subset evaluation; a crashed run may leave partial results that are valid for resume but invalid for strict cache-only loading.

## `raise_error=False` Hides a Failure

Symptoms:

- Evaluation exits normally but fewer task results than expected are present.
- `results.task_results` is shorter than the selected task list.

Recovery:

```python
results = mteb.evaluate(model, tasks, raise_error=False)
print("successful", [r.task_name for r in results.task_results])
print("failed", [(e.task_name, e.exception) for e in results.exceptions])
```

Then rerun the failed task alone with `raise_error=True` for a full traceback.

## Encoder Arguments Are Ignored or Break the Model

Symptoms:

- Unexpected batch size, precision, prompt, or backend behavior.
- Encoder raises because it does not accept a provided kwarg.

Recovery:

- Keep `encode_kwargs` minimal and match the model wrapper's `encode` signature.
- Start with `encode_kwargs={"batch_size": 32}` and add one option at a time.
- If using SentenceTransformer prompts or task-specific prompt keys, verify that prompt configuration belongs in model construction rather than `encode_kwargs`.
- If `show_progress_bar=False` is needed globally, pass it explicitly in `encode_kwargs` when other kwargs are also supplied.

## Prediction Folder Is Empty

Symptoms:

- `prediction_folder` was passed, but no expected file appears.
- File name does not match downstream code.

Recovery:

- Confirm the task type supports prediction export.
- Look for `{task_name}_predictions.json` under the exact folder passed to `prediction_folder`.
- Ensure the evaluation actually ran; a complete cache hit may return cached results without regenerating predictions.
- Use `overwrite_strategy="always"` when prediction files need to be regenerated.

## Multiprocessing or Download Workers Fail

Symptoms:

- Dataset transform errors involving pickling, multiprocessing, worker crashes, or platform-specific process startup.
- Hangs during data loading.

Recovery:

- Retry with `num_proc=1` or `num_proc=None`.
- Keep model objects and task transforms simple when multiprocessing is enabled.
- Use a persistent cache path so a retry does not repeat already-completed work.

## Model/Task Modality Mismatch

Symptoms:

- `ValueError` says model modalities do not overlap with task modalities.
- Image, audio, video, or image-text tasks fail before scoring.

Recovery:

- Choose tasks whose modalities match the model, or use the `models-and-encoders` sub-skill to pick a compatible model wrapper.
- Install modality extras before evaluating non-text tasks.
- Use `mteb.get_tasks(modalities=[...], exclusive_modality_filter=...)` to select compatible tasks deliberately.

## Quick Diagnostic Commands

```bash
python -c "import inspect, mteb; print(mteb.__version__); print(inspect.signature(mteb.evaluate))"
python scripts/smoke_evaluate_with_mock.py
```

Expected smoke output includes `ok` plus checks for `only-cache` failure on empty cache and cache-only success after a populated run.
