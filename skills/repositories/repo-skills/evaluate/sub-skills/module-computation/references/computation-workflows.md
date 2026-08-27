# Computation Workflows

Use these workflows after a module is loaded. If the user still needs to find, select, pin, or load a metric/comparison/measurement, route to `../module-loading/` first.

## 1. Inspect Before Running

```python
print(metric.module_type)
print(metric.features)
print(metric.inputs_description)
```

Treat `features` as the source of truth for input names and one-example shapes. For standard metrics, feature names are usually `predictions` and `references`. Some modules use custom names such as `inputs` and `targets`; pass those exact names to `compute`, `add`, or `add_batch`.

## 2. Direct Compute

Use direct `compute` when all predictions/references are already materialized.

```python
import evaluate

accuracy = evaluate.load("accuracy")
result = accuracy.compute(
    predictions=[0, 1, 1, 0],
    references=[0, 1, 0, 1],
)
assert result == {"accuracy": 0.5}
```

Pass module-specific compute options with the same call. For example, binary classification metrics may accept options such as `pos_label` when documented by the module.

## 3. Stream One Example at a Time

Use `add` when predictions are produced one at a time and you do not want to store separate Python lists.

```python
accuracy = evaluate.load("accuracy")
for prediction, reference in zip([0, 1, 1, 0], [0, 1, 0, 1]):
    accuracy.add(prediction=prediction, reference=reference)
result = accuracy.compute()
```

For non-standard feature names, use those names directly:

```python
module.add(inputs=1, targets=1)
module.add(inputs=2, targets=3)
result = module.compute()
```

## 4. Stream Batches

Use `add_batch` for model evaluation loops and batched inference.

```python
metric = evaluate.load("accuracy")
for predictions, references in [([0, 1], [0, 1]), ([1, 0], [0, 1])]:
    metric.add_batch(predictions=predictions, references=references)
result = metric.compute()
```

In a model loop, add each inference batch and compute once at the end:

```python
metric = evaluate.load("accuracy")
for model_inputs, labels in evaluation_batches:
    predictions = model(model_inputs)
    metric.add_batch(predictions=predictions, references=labels)
result = metric.compute()
```

## 5. Combine Multiple Modules

Use `evaluate.combine` for several metrics/comparisons/measurements over the same inputs.

```python
combined = evaluate.combine(["accuracy", "f1", "precision", "recall"])
result = combined.compute(predictions=[0, 1, 0], references=[0, 1, 1])
```

When output keys may collide, prefer a dict and `force_prefix=True` for stable downstream field names:

```python
combined = evaluate.combine(
    {"acc": "accuracy", "f1_binary": "f1"},
    force_prefix=True,
)
result = combined.compute(predictions=[0, 1, 0], references=[0, 1, 1])
# Example keys: acc_accuracy, f1_binary_f1
```

`CombinedEvaluations` also supports streaming:

```python
combined = evaluate.combine(["accuracy", "f1"])
combined.add_batch(predictions=[0, 1], references=[0, 1])
combined.add_batch(predictions=[0, 1], references=[1, 1])
result = combined.compute()
```

## 6. Configure Cache and Memory

By default, evaluate writes temporary Arrow files under its metrics cache. Use `keep_in_memory=True` for small single-process jobs that should avoid cache files:

```python
metric = evaluate.load("accuracy", keep_in_memory=True)
result = metric.compute(predictions=[0, 1], references=[0, 1])
```

Use `cache_dir` to isolate temporary files or place them on a shared filesystem:

```python
metric = evaluate.load("accuracy", cache_dir="./eval-cache", experiment_id="run-001")
```

Use a unique `experiment_id` whenever multiple evaluations may run concurrently in the same cache directory, especially in distributed jobs.

## 7. Distributed Computation

Evaluate's distributed mode stores each worker's predictions/references in Arrow files and computes the final result on worker `0`.

```python
metric = evaluate.load(
    "f1",
    cache_dir="SHARED_EVALUATE_CACHE_DIR",
    num_process=world_size,
    process_id=rank,
    experiment_id="validation-epoch-3",
)
metric.add_batch(predictions=local_predictions, references=local_references)
result = metric.compute()
if rank == 0:
    print(result)
```

Rules for safe distributed jobs:

- Every process uses the same module, `cache_dir`, `num_process`, and `experiment_id`.
- Each process uses a distinct integer `process_id` between `0` and `num_process - 1`.
- `cache_dir` is visible to all processes.
- `keep_in_memory` is `False`; evaluate raises if `keep_in_memory=True` with `num_process > 1`.
- Non-zero processes should expect `compute()` to return `None`.
- Increase `timeout` if slow workers cannot create or release cache locks quickly enough.

## 8. Save Results

Use `evaluate.save` after computing to write JSON with reproducibility metadata.

```python
import evaluate

result = {"accuracy": 0.5}
output_path = evaluate.save(
    "./results",
    experiment="validation-run-001",
    model="bert-base-uncased",
    **result,
)
print(output_path)
```

Passing a directory creates a timestamped result file; passing a filename writes exactly that file. Saved JSON includes interpreter and version metadata, so inspect it before publishing to avoid leaking local machine details.

## 9. Scikit-Learn and Keras Integration Notes

For scikit-learn estimators, compute predictions first, convert pandas/NumPy outputs to compatible sequences when necessary, then call `compute`:

```python
y_pred = clf.predict(X_test).tolist()
y_true = y_test.tolist()
result = evaluate.load("accuracy").compute(predictions=y_pred, references=y_true)
```

For Keras/TensorFlow callbacks, instantiate the metric once and compute after an epoch or after training. Convert model probabilities/logits to labels expected by the metric before calling `compute`.

```python
predictions = np.round(model.predict(x_test))
result = evaluate.load("accuracy").compute(predictions=predictions, references=y_test)
```

