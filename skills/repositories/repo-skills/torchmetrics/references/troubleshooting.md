# TorchMetrics cross-cutting troubleshooting

Use this reference when the problem is not yet tied to one metric family.
For family-specific symptoms, read the owning sub-skill's `references/troubleshooting.md` after checking the route map in `SKILL.md`.

## First checks

1. Run `python scripts/check_torchmetrics_environment.py --device auto`.
2. Confirm the metric family and optional extra you actually need.
3. Check that `torch`, `torchmetrics`, and the chosen optional dependencies are installed in the same environment.
4. Verify that metric inputs, metric state, and any model or tensor device all match.

## Cross-cutting symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | PyTorch is not installed in the active environment. | Install a compatible PyTorch build, then rerun the smoke script. TorchMetrics requires PyTorch. |
| `ModuleNotFoundError: No module named 'torchmetrics'` | TorchMetrics is not installed in the active environment. | Install `torchmetrics`, then rerun the import or smoke check. |
| The package imports, but a specific metric class is missing | The selected optional dependency for that metric family is not installed. | Install the route-specific extra or the exact dependency named by the owning sub-skill. |
| A `Metric` constructor says unexpected keyword arguments | The installed version does not accept that kwarg or the kwarg name is misspelled. | Separate metric-specific kwargs from base `Metric` kwargs and check spelling against the installed API. |
| `compute()` keeps returning the same value | The result is cached, or the metric was not updated again after the last compute. | Move all state changes into `update()`, or call `reset()` before the next stream. |
| Old data leaks into a new epoch, split, or dataloader | The metric instance was reused without a reset, or one instance was shared across streams. | Use separate metric instances per logical stream and call `reset()` at boundaries. |
| A metric stays on CPU while tensors are on CUDA or another accelerator | The metric was not moved with the model or was hidden in a plain Python container. | Register metrics as module children and move the model/metric with `.to(device)`. |
| Lightning `self.log()` or `self.log_dict()` rejects a metric output | The metric returns a non-scalar tensor, dict, list, or nested structure. | Log the object only when Lightning can reduce it to a scalar, or flatten/reduce the result before logging. |
| `sync_dist=True` on Lightning logging did not change a TorchMetrics object | TorchMetrics manages its own synchronization, not Lightning's logging flags. | Configure the metric with `sync_on_compute`, `dist_sync_on_step`, `process_group`, or `dist_sync_fn`. |
| A DDP job hangs when only rank 0 updates a metric | Other ranks are waiting for synchronization that never happens. | If only rank 0 computes the metric, set `sync_on_compute=False` for that metric stream. |
| A final evaluation score looks biased in DDP | The distributed sampler padded the dataset with repeated examples. | For final evaluation, use one process or a DDP join strategy that avoids padding bias. |
| `MetricCollection` complains about duplicate names | A list of metrics contains duplicate class names, or output keys collide. | Use a dict with explicit names or rename metrics with `prefix`/`postfix`. |
| A plot call fails in a headless session | Matplotlib is missing or the backend is interactive-only. | Install the plotting extra and use a non-interactive backend such as Agg in scripts. |
| A metric that needs a model or tokenizer tries to download assets | The metric belongs in the model-based route and the cache is empty. | Use the model-based sub-skill to decide whether to prefetch assets, use a cached path, or choose a non-model alternative. |

## Optional dependency triage

- Image and detection metrics often need `torchvision`, `pycocotools`, `faster_coco_eval`, `torch_fidelity`, or `piq`.
- Audio metrics often need `pesq`, `pystoi`, `torchaudio`, `gammatone`, `librosa`, `onnxruntime`, or `requests`.
- Text metrics often need `nltk`, `regex`, `sentencepiece`, `transformers`, `mecab-python3`, `ipadic`, or `mecab_ko` packages.
- Clustering and some retrieval workflows may need `torch_linear_assignment` or other small extras.

If the missing package is optional for the chosen task, switch to the route that does not need it. If it is required for the chosen task, install the missing dependency or narrow the request.
