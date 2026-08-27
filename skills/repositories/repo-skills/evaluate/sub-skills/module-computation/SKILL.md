---
name: module-computation
description: "Compute evaluate metrics, comparisons, and measurements with
  direct or streaming inputs; combine modules; configure cache/distributed runs;
  save results; and debug input validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Module Computation

Use this sub-skill when a user has already selected or loaded an `evaluate` module and needs to run it correctly. Route module discovery, Hub/local loading, revisions, and `evaluate.load(...)` decisions to `../module-loading/`. Route evaluator pipeline orchestration around datasets/models/pipelines to `../evaluator-pipelines/`. Route authoring or sharing new modules to `../hub-and-cli/`.

## Start Here

1. Inspect the loaded module before computing: check `module.features`, `module.inputs_description`, `module.module_type`, and `module.info` so input names and shapes match the module contract.
2. Choose a computation style:
   - Direct: `module.compute(predictions=[...], references=[...], **module_kwargs)` for all inputs at once.
   - Streaming examples: call `module.add(prediction=..., reference=...)` repeatedly, then `module.compute()`.
   - Streaming batches: call `module.add_batch(predictions=[...], references=[...])` for each batch, then `module.compute()`.
3. For non-standard modules, use the input names shown in `features`, such as `inputs=` and `targets=`, instead of assuming `predictions`/`references`.
4. For multiple modules, use `evaluate.combine(...)`; pass `force_prefix=True` or a name-to-module dict when output keys may collide.
5. For distributed runs, set the same `cache_dir`, `num_process`, and `experiment_id` on every worker, a unique `process_id` per worker, and read the result only from `process_id == 0`.
6. Save finished result dictionaries with `evaluate.save(path_or_file, **result, **metadata)` when the user needs a JSON record.

## Core References

- `references/computation-workflows.md`: direct compute, streaming, combined evaluations, distributed/cache patterns, result saving, and integration examples.
- `references/api-reference.md`: signatures, accepted inputs, result shapes, and constructor/settings table for computation APIs.
- `references/troubleshooting.md`: validation, shape, cache, distributed, casting, and combined-key failure modes.
- `scripts/compute_smoke.py`: safe smoke helper for tiny computations against a named module or local module path.

## Fast Patterns

```python
import evaluate

metric = evaluate.load("accuracy")
result = metric.compute(predictions=[0, 1, 1, 0], references=[0, 1, 0, 1])
```

```python
metric = evaluate.load("accuracy")
for predictions, references in [([0, 1], [0, 1]), ([1, 0], [0, 1])]:
    metric.add_batch(predictions=predictions, references=references)
result = metric.compute()
```

```python
combined = evaluate.combine({"acc": "accuracy", "f1_binary": "f1"}, force_prefix=True)
result = combined.compute(predictions=[0, 1, 0], references=[0, 1, 1])
```

## Guardrails

- `compute`, `add`, and `add_batch` are keyword-oriented for `EvaluationModule`; do not rely on positional calls for normal modules.
- `features` describes one example; `add_batch` and `compute` usually receive lists, arrays, or tensors of those examples.
- `add` takes singular aliases (`prediction`, `reference`) for standard modules; use custom feature names directly for non-standard modules.
- `compute()` returns `None` on non-zero distributed processes; only process `0` returns the final result dict.
- `keep_in_memory=True` is single-process only; do not combine it with `num_process > 1`.
- `evaluate.save` records metadata including interpreter information in the JSON output; avoid publishing sensitive local paths from saved files without review.

