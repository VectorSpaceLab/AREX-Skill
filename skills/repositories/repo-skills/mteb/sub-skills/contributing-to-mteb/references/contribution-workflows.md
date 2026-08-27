# Contribution Workflows

This reference covers safe contribution workflows for adding MTEB tasks, benchmarks, model metadata, and result submissions. It assumes the active Python environment can import `mteb` and that `pip check` is clean.

## Add a Dataset or Task

1. Pick the closest abstract task class from `mteb.abstasks`, such as `AbsTaskClassification`, `AbsTaskClustering`, `AbsTaskRetrieval`, `AbsTaskReranking`, `AbsTaskSTS`, `AbsTaskPairClassification`, or a multimodal/audio/video variant.
2. Create a task class with a `metadata = mteb.TaskMetadata(...)` or `TaskMetadata(...)` class attribute.
3. Pin the dataset source with `dataset={"path": "org/dataset", "revision": "commit-or-tag"}` and do not set `trust_remote_code=True`.
4. Add task-specific column configuration, for example `input_column_name`, `label_column_name`, `column_names`, `input1_column_name`, `input2_column_name`, or retrieval corpus/query/qrels shapes.
5. Prefer the default `load_data()` when the Hub dataset is already in MTEB shape; otherwise keep transforms deterministic and consider pushing the transformed dataset with `task.push_dataset_to_hub(repo_name)`.
6. Run metadata preflight before downloads: `python scripts/check_task_metadata.py --task-class my_package.my_task:MyTask --require-filled`.
7. Load the dataset only when access is expected: `python -c "from my_package.my_task import MyTask; t=MyTask(); t.load_data(); print(t.metadata.name, t.metadata.eval_splits)"`.
8. Calculate descriptive statistics with `task.calculate_descriptive_statistics()`; use `overwrite_results=True` when intentionally replacing stale stats.
9. Smoke-evaluate with a tiny model, then a representative small model, and include non-random/non-trivial signal in the PR description.

Expected signals:

- `task.metadata._validate_metadata()` returns without language-code errors.
- `task.metadata.is_filled()` is true for new public tasks unless the PR intentionally discusses an unresolved field.
- `task.metadata.descriptive_stats` and `task.metadata.n_samples` exist after statistics generation for non-aggregate tasks.
- `task.metadata.dataset.get("trust_remote_code", False) is False`.
- A smoke run returns a result whose `get_score()` is finite and plausible for the task.

## Add a Benchmark

Use benchmarks when the contribution groups tasks to measure a clear capability rather than adding a new dataset format.

```python
import mteb
from mteb import Benchmark

custom_benchmark = Benchmark(
    name="MTEB(custom, v1)",
    tasks=mteb.get_tasks(
        tasks=["TaskOne", "TaskTwo"],
        languages=["eng"],
    ),
    description="What capability this benchmark is meant to measure.",
)
```

Validation checklist:

- Ensure each task exists via `mteb.get_tasks(tasks=[...])` or `mteb.get_task(...)`.
- Review `task.metadata.description`, `domains`, `task_subtypes`, `license`, `sample_creation`, and `descriptive_stats` for quality, duplicates, leakage, and dataset size.
- Decide whether the benchmark is development-only or suitable for leaderboard display; not every benchmark should appear on the leaderboard.
- After adding it to the benchmark registry, check retrieval with `mteb.get_benchmark("MTEB(custom, v1)")`.
- If adding to a leaderboard menu, validate that the benchmark appears in the intended menu group and has submitted results.

## Add a Model Implementation

For SentenceTransformers-compatible models, a `ModelMeta` is often enough:

```python
from mteb.models import ModelMeta, SentenceTransformerEncoderWrapper

my_model = ModelMeta(
    name="org/model-name",
    loader=SentenceTransformerEncoderWrapper,
    languages=["eng-Latn"],
    open_weights=True,
    revision="pinned-model-revision",
    release_date="2025-01-01",
    n_parameters=100_000_000,
    memory_usage_mb=400,
    embed_dim=768,
    license="mit",
    max_tokens=512,
    reference="https://huggingface.co/org/model-name",
    similarity_fn_name="cosine",
    framework=["Sentence Transformers", "PyTorch"],
    use_instructions=False,
)
```

Model workflow:

- Generate a first draft with `ModelMeta.from_hub("org/model-name")` or, for loaded SentenceTransformers models, `ModelMeta.from_sentence_transformer_model(model)`.
- For cross-encoders, use `ModelMeta.from_cross_encoder(model)` when applicable and route protocol details through `models-and-encoders`.
- If a custom loader is needed, implement one of MTEB's encoder, cross-encoder, or search protocols and set it as `loader`.
- Put optional imports inside the loader or wrapper constructor, not at module top-level.
- Add the optional dependency group in package metadata and set `extra_requirements_groups=["group-name"]` on `ModelMeta`.
- Verify `mteb.get_model("org/model-name", revision="...")` and `mteb.get_model_meta("org/model-name", revision="...")`.
- Test the model on representative public tasks and include at least one reproduced or sanity-checked result in the PR.

## Submit Results

Use `ResultCache` to avoid recomputation and to prepare submissions:

```python
import mteb

cache = mteb.ResultCache(cache_path="mteb-results-cache")
model_meta = mteb.get_model_meta("sentence-transformers/all-MiniLM-L6-v2")
task = mteb.get_task("ArguAna")

mteb.evaluate(model_meta, task, cache=cache, co2_tracker=False)
submission = cache.submit_results(models=[model_meta.name], create_pr=False)
print(submission["path"])
```

Use `create_pr=True` only when Git, GitHub CLI, authentication, and the `mteb[github]` extra are installed. Manual submission is safer for reviewing generated result files before opening a PR.

## Commands Worth Running

- `python -c "import mteb; print(mteb.__version__)"` confirms package import.
- `python -m pip check` confirms dependency consistency.
- `mteb available-tasks --help` confirms CLI task discovery is installed.
- `mteb run -m mteb/baseline-random-encoder -t TaskName` smoke-runs a new task through the CLI.
- `python scripts/check_task_metadata.py --task-class module:ClassName --require-filled --require-descriptive-stats` catches metadata defects before review.
