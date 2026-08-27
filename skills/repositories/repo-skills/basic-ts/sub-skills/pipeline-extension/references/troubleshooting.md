# Troubleshooting

## Purpose

Use this reference when a BasicTS callback, metric, scaler, or taskflow behaves unexpectedly.

## Common failures

### 1) A callback hook never fires

**Symptoms**
- the callback seems to do nothing
- logs show no evidence of the expected hook

**Likely cause**
- the hook name does not match a `BasicTSCallback` method
- the callback was not added to the config

**Recovery**
- Check the exact method name.
- Confirm the callback is in `cfg.callbacks`.
- Compare the hook name with `src/basicts/runners/callback/callback.py`.

### 2) Metric computation fails with missing keys

**Symptoms**
- metric errors mention `prediction` or `targets`
- a custom metric receives the wrong kwargs

**Likely cause**
- the metric signature does not match the keys in the forward return
- the model did not return the expected field names

**Recovery**
- Make the metric signature match the keys you return.
- Keep `prediction` and `targets` in the forward return when the metric needs them.

### 3) `targets_mask` is missing or wrong

**Symptoms**
- forecasting loss weighting is wrong
- imputation behaves as if everything were valid

**Likely cause**
- the taskflow did not create the mask you expected
- the model or metric assumes a mask key that is not there

**Recovery**
- Use the taskflow that creates the needed mask.
- Confirm whether the mask is produced during preprocess or by the model.

### 4) The scaler fails during fit

**Symptoms**
- the training setup crashes before the first epoch
- scaler code complains about missing statistics or unsupported data

**Likely cause**
- the dataset does not expose a valid `data` property
- the property returns the wrong shape or type

**Recovery**
- Make sure the dataset class returns the array view the scaler should learn from.
- Check the training split data shape before fitting the scaler.

### 5) `num_epochs`, `num_steps`, or checkpoint strategy conflict

**Symptoms**
- `ValueError` about `num_epochs` and `num_steps`
- checkpoint retention does not match the validation interval

**Likely cause**
- incompatible training-unit settings
- a checkpoint save strategy that does not align with `val_interval`

**Recovery**
- Use one training unit at a time.
- Make the checkpoint save strategy compatible with validation frequency.

### 6) The config looks right but the run still uses CPU

**Symptoms**
- no GPU is used
- `torch.cuda.is_available()` is false in the environment

**Likely cause**
- `gpus=None`
- the current environment is intentionally CPU-only

**Recovery**
- Treat CPU smoke as a contract check, not as GPU verification.
- Move to a GPU-capable environment only when the task truly needs it.

### 7) Selective learning is misconfigured

**Symptoms**
- the callback fails to initialize
- estimator loading fails

**Likely cause**
- the estimator checkpoint path is missing
- the estimator model or config does not match the checkpoint

**Recovery**
- Confirm the estimator checkpoint exists.
- Verify that the estimator model and its config match the saved weights.

## What to check first

1. The hook name.
2. The metric signature.
3. The keys returned by the model or taskflow.
4. Whether the dataset exposes the right `data` view.
5. Whether your training-unit settings are compatible.

## When to switch sub-skills

- If the issue is about model `forward` shape or outputs, go to `model-development`.
- If the issue is about dataset folders or split files, go to `data-preparation`.
- If the issue is about launcher usage or checkpoints, go to `training-evaluation`.
