# Task Implementation Guide

MTEB task contributions combine a task class, a complete `TaskMetadata` object, optional dataset transformation logic, descriptive statistics, and a smoke evaluation. For metadata-field semantics and filtering behavior, cross-check `tasks-and-benchmarks`; this guide focuses on contribution implementation.

## Choose the Abstract Task

Common choices:

- `AbsTaskClassification`: embeddings feed a classifier; common scores include `accuracy` and related classification metrics.
- `AbsTaskClustering`: embeddings are clustered; common score is `v_measure`.
- `AbsTaskRetrieval`: query/corpus retrieval; common score is `ndcg_at_10`.
- `AbsTaskReranking`: rerank top candidates; requires candidate sets or top-ranked documents.
- `AbsTaskSTS`: pair similarity; common score is `spearman`.
- `AbsTaskPairClassification`: pair relation classification; common multimodal pattern uses `input1_column_name` and `input2_column_name` mappings.
- Multimodal/audio/video abstract tasks: set `modalities` and `category` consistently, then validate model modality support before smoke evaluation.

Minimal classification shape:

```python
import mteb
from mteb.abstasks import AbsTaskClassification

class MyClassificationTask(AbsTaskClassification):
    metadata = mteb.TaskMetadata(
        name="MyClassificationTask",
        description="Concise dataset description.",
        reference="https://example.org/paper-or-dataset",
        dataset={"path": "org/dataset", "revision": "pinned-revision"},
        type="Classification",
        category="t2c",
        modalities=["text"],
        eval_splits=["test"],
        eval_langs=["eng-Latn"],
        main_score="accuracy",
        date=("2024-01-01", "2024-12-31"),
        domains=["Written"],
        task_subtypes=["Topic classification"],
        license="mit",
        annotations_creators="human-annotated",
        dialect=[],
        sample_creation="found",
        bibtex_citation="",
    )
    input_column_name = "text"
    label_column_name = "label"
```

## Required Metadata Fields

`TaskMetadata` forbids unknown fields and validates language codes. New public tasks should fill these fields unless the PR explicitly asks maintainers about an uncertain value:

- `name`: exported task name, usually class-aligned and versioned when superseding old data.
- `description`: concise but specific dataset/task description.
- `reference`: paper, dataset page, or other stable reference.
- `dataset`: dictionary passed to `datasets.load_dataset`; include `path` and non-null `revision`; keep `trust_remote_code` absent or false.
- `type`: MTEB task type such as `Classification`, `Retrieval`, `Reranking`, `Clustering`, `STS`, `PairClassification`, or multimodal-specific task type.
- `category`: modality direction such as `t2t`, `t2c`, `t2i`, `i2t`, `a2t`, or `v2t`.
- `modalities`: list such as `["text"]`, `["image", "text"]`, `["audio"]`, or `["video", "text"]`.
- `eval_splits`: split names used for evaluation.
- `eval_langs`: list like `["eng-Latn"]` or mapping from Hugging Face subsets to lists for multilingual datasets.
- `main_score`: metric key used as primary result, for example `accuracy`, `v_measure`, `ndcg_at_10`, `spearman`, or `max_ap`.
- `date`, `domains`, `task_subtypes`, `license`, `annotations_creators`, `dialect`, `sample_creation`, and `bibtex_citation`: required for `is_filled()` to pass.
- Optional routing fields: `adapted_from`, `is_public`, `contributed_by`, `superseded_by`, and `is_beta`.

## Multilingual and Retrieval Gotchas

- For multilingual tasks with multiple Hub subsets, set `eval_langs` as `{subset_name: ["eng-Latn", "..."]}` so `metadata.hf_subsets_to_langscripts` is correct.
- Aggregate tasks should generally use only the `default` subset mapping.
- Retrieval datasets need corpus entries with stable `id` plus text/image/audio fields, query entries with stable `id`, and qrels shaped as `dict[query_id][document_id] = relevance_score`.
- If `prompt` is a dictionary, use only `query` and `passage` keys and reserve dict prompts for retrieval-like tasks unless there is a known special case.
- For multimodal pair classification, column names can map columns to modalities, for example `input1_column_name = {"video": "video"}` and `input2_column_name = {"text": "text"}`.

## Descriptive Statistics

Descriptive statistics are a release-quality gate for non-aggregate tasks. They help reviewers detect duplicates, tiny evaluation sets, very short documents, and suspicious split composition.

Run after the task can load data:

```python
task = MyClassificationTask()
task.load_data()
task.calculate_descriptive_statistics()
```

Use `task.calculate_descriptive_statistics(overwrite_results=True)` only when deliberately replacing stale statistics. After generation, expected checks are:

- `task.metadata.descriptive_stats is not None`.
- `task.metadata.n_samples is not None`.
- each split/subset has plausible sample counts and length statistics.
- very small or heavily filtered datasets are justified in the PR.

## Safe Metadata Preflight

Before dataset access, validate class-level metadata or a JSON fixture:

```bash
python scripts/check_task_metadata.py --task-class my_package.my_task:MyTask --require-filled
python scripts/check_task_metadata.py --metadata-json task_metadata.json --require-filled --require-descriptive-stats
```

The helper checks the same high-value conditions used by native tests: `TaskMetadata` construction, `_validate_metadata()`, `is_filled()`, `dataset.path`, `dataset.revision`, `trust_remote_code`, prompt dictionary keys, multilingual `eval_langs` shape, public/beta/superseded flags, and optional descriptive stats presence.

## Smoke Evaluation

After metadata and data loading pass, run a small smoke evaluation. Python form:

```python
import mteb

model = mteb.get_model("mteb/baseline-random-encoder")
task = MyClassificationTask()
result = mteb.evaluate(
    model,
    task,
    cache=mteb.ResultCache(cache_path="mteb-results-cache"),
    co2_tracker=False,
    raise_error=True,
)
print(result.task_results[0].get_score())
```

CLI form:

```bash
mteb run -m mteb/baseline-random-encoder -t MyClassificationTask
```

If the random baseline is perfect or exactly matches a strong model, investigate label leakage, duplicate pairs, train/test contamination, qrels construction, or an overly small dataset before submission.

## Review Checklist

- Task class inherits the right abstract base and matches `metadata.type`.
- Dataset revision is pinned and remote code is not trusted.
- Language/script codes use BCP-47-like MTEB forms such as `eng-Latn`.
- `main_score` exists in task output for every evaluated split/subset.
- Descriptive statistics exist for non-aggregate tasks.
- Citations are valid BibTeX when a paper exists, otherwise `bibtex_citation=""` is intentional.
- Private tasks set `is_public=False` and document access expectations.
- Beta tasks set `is_beta=True` only for a deliberate temporary reason.
- Superseded tasks set `superseded_by` and new versions use clear versioned naming.
