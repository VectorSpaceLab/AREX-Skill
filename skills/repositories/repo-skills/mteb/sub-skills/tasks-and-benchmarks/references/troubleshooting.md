# Troubleshooting Task and Benchmark Selection

## Import or Installation Fails

Symptoms:

- `ModuleNotFoundError: No module named 'mteb'`
- `ImportError` from optional libraries during task inspection.
- `pip check` reports incompatible dependencies.

Actions:

- Verify import with `python -c "import mteb; print(mteb.__version__)"`.
- Install the public package with the extras required by the target workflow if evaluation later needs optional backends or datasets.
- Keep task/benchmark inspection separate from model evaluation; `get_tasks`, `get_benchmark`, and `filter_tasks` should not require model inference.

## Dataset Downloads or Private Access Surprises

Symptoms:

- Hugging Face authentication errors.
- Dataset download starts unexpectedly during evaluation.
- A private or closed task is missing from discovery.

Actions:

- Use metadata inspection first; the bundled `scripts/inspect_task_selection.py` does not call `load_data()` or `mteb.evaluate(...)`.
- Remember `get_tasks(exclude_private=True)` is the default; pass `exclude_private=False` only when the user intentionally wants private/closed datasets and has access.
- Route actual run planning to `evaluation-workflows`, where cache, result paths, credentials, and dataset download expectations can be handled explicitly.

## Beta or Superseded Tasks Are Missing

Symptoms:

- A known task name is absent from broad `get_tasks(...)` results.
- Counts differ from examples or older reports.
- Including beta tasks emits a warning.

Actions:

- Broad discovery defaults to `exclude_superseded=True`, `exclude_private=True`, and `exclude_beta=True`.
- Include older or beta coverage only with explicit flags:

```python
tasks = mteb.get_tasks(
    exclude_superseded=False,
    exclude_private=False,
    exclude_beta=False,
)
```

- For existing benchmark lists, set the same flags on `mteb.filter_tasks(...)` if you want consistent behavior.
- Prefer canonical, non-superseded tasks for new evaluations unless the user needs historical comparability.

## Task Name Typos

Symptoms:

- `KeyError: '<name>' not found. Did you mean: '<similar>'?`
- `get_tasks(tasks=[...])` returns fewer tasks than requested after applying language filters.

Actions:

- Use the close-match suggestion in the exception.
- List candidate names with `scripts/inspect_task_selection.py --names CandidateName --format json` or discover by metadata first.
- If names are correct but the list shrinks, remove or relax `languages`, `script`, `hf_subsets`, or `exclusive_language_filter`.
- Remember that `get_tasks(tasks=[...])` ignores `domains`, `task_types`, and `categories`; use `mteb.filter_tasks(...)` on the resulting list for those constraints.

## Language and Script Confusion

Symptoms:

- `ValueError: Invalid language code` for values like `en` or `eng-Latn`.
- `ValueError: Invalid script code` for values like `latin`.
- Multilingual task subsets include more languages than expected.

Actions:

- Use ISO 639-3 codes in `languages`, such as `eng`, `deu`, `fra`, `spa`.
- Use ISO 15924 codes in `script`, such as `Latn` or `Cyrl`.
- Validate codes with `from mteb.languages import ISO_TO_LANGUAGE, ISO_TO_SCRIPT`.
- Use `exclusive_language_filter=True` when subsets must not include extra paired languages.

## Modality Filter Mismatch

Symptoms:

- `modalities=["text", "image"]` returns tasks that are text-only or image-only.
- A multimodal-only selection returns more tasks than expected.

Actions:

- Default modality filtering means any requested modality can match.
- Use `exclusive_modality_filter=True` for exact modality-set matching.
- Inspect `task.metadata.modalities` or `task.modalities` in the output table before evaluation.

## Benchmark Name or Alias Problems

Symptoms:

- `KeyError` from `mteb.get_benchmark(...)`.
- An alias resolves but reports a different name.
- A benchmark is not shown in leaderboard-filtered lists.

Actions:

- Use `mteb.get_benchmarks()` to enumerate canonical names.
- Check `benchmark.aliases` and `benchmark.name`; aliases intentionally resolve to a canonical benchmark object.
- Use `mteb.get_benchmarks(display_on_leaderboard=True)` only for leaderboard-visible benchmarks; pass `False` to inspect non-leaderboard benchmarks.

## CLI/API Misuse

Symptoms:

- `mteb available-tasks` output differs from a Python filter.
- A shell command lists tasks, but Python evaluation uses another set.

Actions:

- Route CLI-specific questions to `cli-and-automation`.
- Reproduce the same filters in Python before evaluation and persist the selected task names in logs or result metadata.
- Use the bundled inspection script to produce JSON for automation and Markdown for human review.

## Cache or Result Path Mistakes

Symptoms:

- Task selection looks correct, but evaluation overwrites or reuses unexpected results.
- Results are missing after evaluation.

Actions:

- Selection utilities do not manage result caches; route to `evaluation-workflows` for `mteb.evaluate(...)` parameters such as `cache`, `overwrite_strategy`, `prediction_folder`, and output handling.
- Before running evaluation, log the selected task names and benchmark name separately from cache/result paths.
- Keep inspection scripts read-only with respect to result directories.
