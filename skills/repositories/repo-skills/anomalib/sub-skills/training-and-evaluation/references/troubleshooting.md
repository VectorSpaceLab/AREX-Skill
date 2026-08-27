# Troubleshooting

This page collects the most common training/evaluation mistakes for the Anomalib engine surface.

## Metric field mismatches

### Symptom

You see errors such as:

- `instance is missing required field`
- `instance does not have a value for field`
- duplicated metric names in Lightning logs

### Likely cause

The metric `fields` do not match the batch dataclass fields, or two metrics of the same class share the same name.

### Fix

- Check the batch schema first.
- Match `fields` to the exact batch attributes.
- Add `prefix=` when you use the same metric class for image-level and pixel-level outputs.
- Use `strict=False` for optional fields such as missing masks.

Example:

```python
from anomalib.metrics import F1Score

image_f1 = F1Score(fields=["pred_label", "gt_label"], prefix="image_")
pixel_f1 = F1Score(fields=["pred_mask", "gt_mask"], prefix="pixel_")
```

## Barebones mode confusion

### Symptom

- checkpoint files are missing
- `self.log(...)` appears to do nothing
- `trainer.test()` returns an empty dict

### Likely cause

`Trainer(barebones=True)` disables Lightning logging and the default checkpoint path. A plain Lightning module that relies only on `self.log(...)` will not surface metrics in barebones mode.

### Fix

- Use barebones only when you want the low-overhead path.
- Keep Anomalib's `Evaluator` callback attached if you still need returned metrics.
- Do not expect the default auto-inserted checkpoint callback in barebones mode.
- If you need checkpoints, pass an explicit checkpoint callback and make the choice intentional.

## Callback ordering and checkpoint behavior

### Symptom

- a callback appears to be ignored
- checkpoint files are written in an unexpected place
- the wrong logger or graph hook is active

### Likely cause

Callbacks come from the model, Engine, and explicit trainer config. The same callback class may also be duplicated or overridden.

### Fix

- Check `AnomalibModule.configure_callbacks()` first.
- Remember that Engine injects its own checkpoint/timer/progress callbacks.
- If you use `get_callbacks(config)`, confirm whether `trainer.ckpt_path` or NNCF settings are adding more callbacks.
- The default checkpoint path is inside `weights/lightning` below the versioned run directory.

## Validation runs before test or predict

### Symptom

`Engine.test()` or `Engine.predict()` runs validation first.

### Likely cause

The model is zero-shot or few-shot, and the engine is collecting normalization or threshold state.

### Fix

- Provide a `ckpt_path` if you want to skip that pre-validation step.
- Otherwise, keep the validation data available so thresholds can be computed.

## Pre/post-processing shape issues

### Symptom

- resize or normalization errors at batch start
- missing `pred_label` or `pred_mask`
- `PostProcessor` raises because it has no score or anomaly map

### Likely cause

The batch shape or the available fields do not match the callback's expectations.

### Fix

- `PreProcessor` expects image batches in `(B, C, H, W)` and masks in `(B, H, W)`.
- `PostProcessor` needs at least one of `pred_score` or `anomaly_map`.
- `MEBinPostProcessor` accepts 3D or 4D anomaly maps and handles the channel dimension internally.
- If the validation pass never ran, the thresholds may still be unset.

## Optional logger dependency failures

### Symptom

Importing `anomalib.loggers` fails or warns about missing backend packages.

### Likely cause

The backend is optional and not installed in the minimum environment.

### Fix

- Use `logger=False` for the minimum CPU path.
- Keep TensorBoard as the default local logger if you need one.
- Install W&B, Comet, or MLflow only when you actually need them.
- For image logging, remember that TensorBoard and Comet require `global_step`.

## GPU-only notes

### Symptom

Optional tests such as PRO device consistency or buffer-list device placement are not runnable on the current host.

### Likely cause

Those checks are CUDA-specific and intentionally optional for the CPU/OpenVINO inspection environment.

### Fix

- Treat them as future optional coverage.
- Do not block the CPU training/evaluation skill on them.

## When to suspect the metric pipeline

If your scores look plausible but the returned metrics are empty or inconsistent, check the order of operations:

1. validation populated thresholds and normalization
2. post-processing converted raw scores to labels/masks
3. evaluator consumed the final batch fields
4. Lightning logging was actually enabled, or Anomalib's evaluator filled metrics back in barebones mode
