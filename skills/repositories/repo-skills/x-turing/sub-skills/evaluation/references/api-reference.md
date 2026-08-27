# API reference

## `EvalMetric`

Signature:
`EvalMetric(name: str, value: float, higher_is_better: bool = True)`

Fields:
- `name`: metric label.
- `value`: numeric score.
- `higher_is_better`: direction flag for downstream consumers.

`as_dict()` returns:
```python
{
  "name": name,
  "value": value,
  "higher_is_better": higher_is_better,
}
```

## `EvalRunResult`

Dataclass fields:
`EvalRunResult(adapter_name: str, task_name: str, status: str, metrics: list[EvalMetric] = field(default_factory=list), metadata: dict = field(default_factory=dict), started_at: str | None = None, finished_at: str | None = None, duration_seconds: float | None = None)`

Fields:
- `adapter_name`: origin adapter id.
- `task_name`: requested task name.
- `status`: run state string such as `planned` or `completed`.
- `metrics`: list of `EvalMetric` objects.
- `metadata`: arbitrary run metadata.
- `started_at`, `finished_at`: ISO-8601 timestamps or `null`.
- `duration_seconds`: elapsed wall-clock seconds or `null`.

`as_dict()` returns a top-level mapping with exactly these keys:
- `adapter_name`
- `task_name`
- `status`
- `metrics`
- `metadata`
- `started_at`
- `finished_at`
- `duration_seconds`

Each metric is serialized with `EvalMetric.as_dict()`. `None` values remain `null` in JSON.

## `BaseEvalAdapter`

Signature:
`run(*, model: Any, dataset: Any, task_name: str, metadata: dict | None = None) -> EvalRunResult`

Behavior:
- Abstract interface only.
- Subclasses decide how `model`, `dataset`, and `task_name` are interpreted.
- Use this when wrapping a future benchmark backend or a local evaluator.

## `LMEvalAdapter`

Signature:
`LMEvalAdapter(tasks: list[str] | None = None, num_fewshot: int = 0, batch_size: int = 1)`

Behavior:
- `adapter_name = "lm_eval"`.
- Stores `tasks`, `num_fewshot`, and `batch_size` on the instance.
- `run(...)` returns an `EvalRunResult` with:
  - `status = "planned"`
  - `metrics = []`
  - `metadata = {"tasks": ..., "requested_task": task_name, "num_fewshot": ..., "batch_size": ..., "integration_status": "scaffold_only"}`
- Caller metadata is merged after the scaffold metadata.

Important limitation:
- It does not invoke lm-evaluation-harness yet.
- It does not compute benchmark scores yet.

## `run_eval_adapter(...)`

Signature:
`run_eval_adapter(adapter, *, model, dataset, task_name, output_path=None, metadata=None) -> EvalRunResult`

Behavior:
1. Record wall-clock `started_at` and monotonic start time.
2. Call `adapter.run(model=model, dataset=dataset, task_name=task_name, metadata=metadata)`.
3. Record wall-clock `finished_at` and `duration_seconds`.
4. Fill missing timing fields on the returned `EvalRunResult`.
5. If `output_path` is not `None`, persist the result with `persist_eval_result(...)`.
6. Return the `EvalRunResult` object.

Notes:
- The wrapper preserves adapter-supplied timing fields if they are already set.
- The wrapper does not alter the metrics list.
- The wrapper returns the result, not the output path.

## `persist_eval_result(...)`

Signature:
`persist_eval_result(result: EvalRunResult, output_path: Path) -> Path`

Behavior:
- Creates parent directories as needed.
- Serializes `result.as_dict()` to UTF-8 JSON.
- Uses `indent=2` and `ensure_ascii=False`.
- Returns the final `Path`.

## Evaluation result shape at a glance

```json
{
  "adapter_name": "string",
  "task_name": "string",
  "status": "string",
  "metrics": [{"name": "string", "value": 0.0, "higher_is_better": true}],
  "metadata": {},
  "started_at": null,
  "finished_at": null,
  "duration_seconds": null
}
```
