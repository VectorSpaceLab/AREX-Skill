# Core API Troubleshooting

## Purpose

Read this when core TorchMetrics usage fails before a domain-specific metric issue is clear. Start with the bundled smoke script, then match the symptom below.

```bash
python scripts/core_metric_smoke.py --device auto
```

## Failure surfaces

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'torch'` | PyTorch is not installed in the active Python environment. | Install a PyTorch build appropriate for the host, then rerun the smoke script. TorchMetrics core APIs require PyTorch. |
| `ModuleNotFoundError: No module named 'torchmetrics'` | TorchMetrics is not installed in the active Python environment. | Install `torchmetrics`, then run the import command or bundled smoke script. |
| Optional metric import fails for `numpy`, `matplotlib`, image/audio/text packages, or model libraries | The selected metric family needs optional dependencies. | For core API work, avoid optional domain metrics. For plotting, route to `collections-wrappers-plotting`; for model-download metrics, route to `model-based-metrics`; for domain metrics, use the sibling domain sub-skill that owns the needed extra. |
| No `torchmetrics` command exists in the shell | TorchMetrics is a library package and has no verified console entry point. | Use Python imports and bundled skill scripts rather than searching for a CLI. |
| `ValueError: Unexpected keyword arguments: ...` | A base `Metric` kwarg or metric-specific kwarg is misspelled or not supported by the installed version. | Separate base kwargs from metric-specific kwargs. Verified base kwargs include `compute_on_cpu`, `dist_sync_on_step`, `process_group`, `dist_sync_fn`, `distributed_available_fn`, `sync_on_compute`, and `compute_with_cache`. Check the installed version if older code used different names. |
| `ValueError: Expected keyword argument ... to be a bool/callable` | A base kwarg has the wrong type. | Pass booleans for `compute_on_cpu`, `dist_sync_on_step`, `sync_on_compute`, and `compute_with_cache`; pass a callable or `None` for `dist_sync_fn`. |
| Repeated `compute()` returns the same value after state was changed manually | `compute()` caches results and normal cache invalidation only happens through `update()` or `reset()`. | Move all state mutation into `update()`, call `reset()` before a new stream, or instantiate with `compute_with_cache=False` for unusual mutable-state metrics. |
| Epoch, validation, or test numbers include old data | The same metric instance was reused without `reset()`, or one instance was shared across train/validation/test/dataloaders. | Call `reset()` at logical boundaries. Prefer separate metric instances for each stage and dataloader. In Lightning, logging metric objects lets Lightning reset them; manual `compute()` logging requires manual reset. |
| Error mentions different devices or says the metric is not on the same device as input | Metric state is on CPU while input tensors are on CUDA/MPS, or the metric was hidden in an unregistered Python container. | Move the metric with `metric.to(device)`, or define it as an `nn.Module`/Lightning child module. Replace plain lists/dicts with `nn.ModuleList`, `nn.ModuleDict`, or `MetricCollection`. |
| `.half()`, `.float()`, or `module.half()` did not change metric state dtype | Metric dtype conversion is guarded. | Use `metric.set_dtype(torch.float64)` or another explicit dtype. Do not rely on normal module dtype conversion methods for metric states. |
| `state_dict()` is empty or a loaded metric did not restore accumulated state | Metric states are not persistent by default. | Call `metric.persistent(True)` before saving, or set `persistent=True` on selected custom `add_state` calls. Load with `map_location` when moving across devices. |
| List-state metric memory grows over evaluation | List states append tensors from every update and are not constant-memory. | Use fixed tensor states when possible, call `reset()` promptly, use functional metrics for one-shot calculations, or set `compute_on_cpu=True` for list states on GPU. |
| Lightning `self.log` or `self.log_dict` rejects a metric output | Lightning scalar logging only accepts scalar tensors; some metrics return matrices, curves, dicts, lists, or nested structures. | Log scalar metrics as objects, or manually flatten/reduce complex outputs to scalar keys. Send plotting/wrapper-specific output handling to the sibling wrapper/plotting route. |
| Lightning logs wrong values or resets before manual epoch logging | Object logging and manual `compute()` logging were mixed for the same metric stream. | Choose one pattern per metric: either log the metric object and let Lightning compute/reset, or log computed tensors and reset manually. |
| `sync_dist=True` on `self.log` did not change a TorchMetrics object result | Metric objects use TorchMetrics' own synchronization, not Lightning's `sync_dist` flags. | Configure the metric with `sync_on_compute`, `dist_sync_on_step`, `process_group`, or `dist_sync_fn`. Functional metrics need manual distributed reduction. |
| DDP job hangs when a metric is updated only on rank zero | Other ranks wait for metric synchronization that rank zero alone is performing. | If only rank zero updates/computes, instantiate the metric with `sync_on_compute=False`; otherwise update/compute on all ranks. |
| Final DDP test metric is slightly biased | Distributed sampling padded an uneven dataset with repeated samples. | For final test reporting, evaluate on one process or use a DDP join strategy that avoids padding bias. Record this caveat in experiment notes. |
| `MetricCollection` raises about duplicate names or invalid inputs | A list contains two metrics with the same class name, or a collection member is not a `Metric`/`MetricCollection`. | Use a dictionary with explicit unique keys for duplicate metric classes, and make sure every value is a module metric. |
| `compute()` before any update warns or returns a default value | No data has been accumulated since initialization or reset. | Call `update(...)` or `metric(...)` before `compute()`, unless the default empty-state result is intentionally being checked. |

## Debugging sequence

1. Run `python scripts/core_metric_smoke.py --device auto` to separate install/device problems from task-specific metric code.
2. Print `type(metric)`, `metric.device`, `metric.dtype`, and `metric.metric_state` before and after one update.
3. Confirm that the metric object is registered as a child module if it lives inside a model.
4. Confirm that `reset()` boundaries match the desired train/validation/test/dataloader boundaries.
5. In DDP or Lightning, decide whether the metric object or the training framework owns synchronization and resetting; do not mix both ownership models for the same stream.
