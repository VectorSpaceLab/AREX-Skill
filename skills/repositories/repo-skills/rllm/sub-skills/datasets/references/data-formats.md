# Data Formats and Task Layouts

## Direct dataset files

`Dataset.load_data(path)` supports:

- `.json`: JSON list or object accepted by the loader;
- `.jsonl`: one JSON object per line;
- `.csv`: loaded through pandas into records;
- `.parquet`: loaded through pandas into records;
- `.arrow`: Arrow IPC files, with optional `_verl.parquet` companion for Verl.

Rows become `dict` records. When rows are wrapped as `Task` objects, rLLM prefers `instruction`, then `question`, and uses `id`/`task_id`/row index as the stable task id.

## Task object

```python
from rllm import Task

Task(
    id="stable-id",
    instruction="prompt or multimodal blocks",
    metadata={...},
    dataset_dir=Path("..."),
    sub_dir=None,
)
```

`task.task_dir` is `dataset_dir / sub_dir` for per-task directories and `dataset_dir` for shared-verifier row datasets.

## Two physical benchmark shapes

### Rows with shared verifier

A dataset directory contains a data file plus shared verifier/config files. Each row becomes one `Task`; all rows share `dataset_dir/tests/` or a verifier declared in metadata.

Typical signals:

- `dataset.toml` at the dataset root;
- data file per split;
- shared `tests/` or named reward/evaluator metadata.

### Task-per-directory / Harbor-style

Each task subdirectory is one problem instance. The loader merges task metadata from `task.toml`, and the task's verifier/environment can live under that task directory.

Typical signals:

- `task-NNN/task.toml` or analogous per-task subdirectories;
- `tests/test.sh`, Python verifier modules, or declared verifier config;
- optional `environment/` directories that cause sandbox requirements.

## Verifier metadata

Evaluation/training can resolve evaluators from:

- explicit CLI `--evaluator` override;
- dataset-level or task-level `[verifier]` metadata;
- catalog `reward_fn` entries;
- per-task sandbox tests for Harbor-style tasks.

If a verifier requires the task sandbox, do not replace it with a host-side evaluator unless the user intentionally wants a different scoring policy.
