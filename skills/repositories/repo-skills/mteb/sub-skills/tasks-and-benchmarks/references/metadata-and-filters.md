# Metadata and Filters

## Key Task Metadata

Task objects carry structured metadata under `task.metadata`. Common fields used for discovery and validation include:

- `name`: canonical task name used by `get_task` and `get_tasks(tasks=[...])`.
- `type`: task family, such as `Retrieval`, `Classification`, `Clustering`, `STS`, `PairClassification`, `Reranking`, `Summarization`, `InstructionRetrieval`, `BitextMining`, or multimodal task types.
- `category`: high-level input/output category, such as text-to-text or text-to-image categories.
- `languages`: ISO 639-3 language codes, such as `eng`, `deu`, `fra`, or `spa`.
- `scripts`: ISO 15924 script codes, such as `Latn` or `Cyrl`.
- `domains`: topic/domain tags such as `Legal`, `Medical`, `Scientific`, `Fiction`, or `Non-fiction`.
- `modalities`: modality tags such as `text`, `image`, `audio`, or `video` depending on task support.
- `eval_splits`: dataset splits that can be evaluated, commonly `test` and sometimes `validation` or other task-specific splits.
- `is_public`: whether the dataset is public; default discovery excludes private datasets.
- `is_beta`: whether the task is beta; default discovery excludes beta tasks.
- `superseded_by`: replacement task name when the task is superseded; default discovery excludes superseded tasks.

## Filter Semantics

`get_tasks(...)` and `filter_tasks(...)` combine different filter fields with AND semantics. Values within a single field usually behave as OR matches.

```python
# English OR German tasks, AND Latin script, AND Classification type.
tasks = mteb.get_tasks(
    languages=["eng", "deu"],
    script=["Latn"],
    task_types=["Classification"],
)
```

Important differences:

- `get_tasks(...)` starts from the global MTEB registry and initializes matching tasks.
- `filter_tasks(...)` starts from an existing iterable, such as a benchmark or a prior selection.
- When `get_tasks(tasks=[...])` is supplied, `domains`, `task_types`, and `categories` are ignored; use `filter_tasks(...)` afterward if those filters must also apply.
- `eval_splits` is applied while initializing tasks, not as a metadata-only predicate.

## Languages vs Scripts

- `languages=["eng"]` filters by ISO 639-3 language code.
- `script=["Latn"]` filters by ISO 15924 script code.
- Language-like values with script suffixes, such as `eng-Latn`, may appear in multilingual task internals, but `languages` expects base language codes and `script` expects script codes.
- Invalid language codes raise `ValueError` and point users to `mteb.languages.ISO_TO_LANGUAGE`.
- Invalid script codes raise `ValueError` and point users to `mteb.languages.ISO_TO_SCRIPT`.

For multilingual tasks, language filtering can narrow task subsets. Use `exclusive_language_filter=True` when a multilingual subset should be kept only if it contains exactly the requested language constraints rather than any subset that includes them.

Validation snippet:

```python
from mteb.languages import ISO_TO_LANGUAGE, ISO_TO_SCRIPT

assert "eng" in ISO_TO_LANGUAGE
assert "Latn" in ISO_TO_SCRIPT
```

## Modality Filters

By default, modality filters are inclusive:

```python
# Keep tasks containing text OR image.
tasks = mteb.get_tasks(modalities=["text", "image"])
```

Set `exclusive_modality_filter=True` to require an exact modality set:

```python
# Keep only tasks whose modalities are exactly {"text", "image"}.
tasks = mteb.get_tasks(
    modalities=["text", "image"],
    exclusive_modality_filter=True,
)
```

Expected signals:

- Non-exclusive: every returned task has at least one requested modality.
- Exclusive: every returned task has `set(task.modalities) == set(requested_modalities)`.

## Default Exclusions

`get_tasks(...)` is conservative by default:

- `exclude_superseded=True`: hides tasks replaced by newer alternatives.
- `exclude_private=True`: hides private/closed datasets.
- `exclude_beta=True`: hides beta tasks.
- `exclude_aggregate=False`: keeps aggregate tasks unless explicitly excluded.

`filter_tasks(...)` defaults are less restrictive for existing lists:

- `exclude_superseded=False`
- `exclude_private=False`
- `exclude_beta=False`
- `exclude_aggregate=False`

Be explicit when reproducibility matters:

```python
tasks = mteb.get_tasks(
    task_types=["Retrieval"],
    exclude_superseded=True,
    exclude_private=True,
    exclude_beta=True,
    exclude_aggregate=True,
)
```

## Typo and Rename Handling

- Unknown task names raise `KeyError` and may include a `Did you mean: ...?` suggestion from close-name matching.
- Some renamed tasks warn and map to a newer name. Prefer the new canonical name in scripts and reports.
- Unknown benchmark names raise `KeyError` and may include a close-match suggestion.
- Benchmark aliases resolve directly to canonical benchmark objects; compare `benchmark.name` to see the canonical form.

## Recommended Selection Checklist

1. Decide whether the user wants a predefined benchmark, named tasks, or metadata discovery.
2. Use `scripts/inspect_task_selection.py` or a short Python snippet to inspect names, types, languages, scripts, domains, modalities, and splits.
3. Make beta/private/superseded decisions explicit in code and logs.
4. For benchmark subsets, call `mteb.filter_tasks(benchmark, ...)` rather than rebuilding from global task names unless benchmark-specific language/split choices are not needed.
5. Hand the selected task objects or benchmark to evaluation only after the selection table matches the user’s intent.
