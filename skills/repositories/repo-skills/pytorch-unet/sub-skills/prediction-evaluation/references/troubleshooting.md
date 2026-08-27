# Pytorch-UNet prediction and evaluation troubleshooting

Use this reference when prediction, mask conversion, evaluation, or Dice metrics fail or produce surprising outputs.

## Checkpoint loading fails with unexpected `mask_values`

### Symptom

`load_state_dict` reports an unexpected key named `mask_values`.

### Cause

Training checkpoints store `mask_values` alongside model parameters. It is metadata, not a neural-network parameter.

### Fix

Pop it before loading and keep it for output conversion:

```python
state_dict = torch.load(path, map_location=device)
mask_values = state_dict.pop("mask_values", [0, 1])
net.load_state_dict(state_dict)
```

Do not delete it permanently from your workflow; `mask_to_image` needs it to reconstruct the original mask values or colors.

## Checkpoint class or architecture mismatch

### Symptom

- `RuntimeError` from `net.load_state_dict` with size mismatches.
- Prediction output channel count is unexpected.
- CLI works with one checkpoint but not another.

### Likely causes

- `--classes` does not match the checkpoint's `n_classes`.
- `--bilinear` differs from the checkpoint's training setting.
- The checkpoint was trained with a different input channel count.
- The file is not a raw U-Net `state_dict`.

### Fix

- Recreate the model with the same `n_channels`, `n_classes`, and `bilinear` used during training.
- For stock CLI prediction, remember it always constructs `UNet(n_channels=3, ...)`; use the API path for grayscale or non-RGB checkpoints.
- Use `model-api` if you need deeper architecture/checkpoint compatibility guidance.

## `--mask-threshold` appears to do nothing

### Symptom

Changing `--mask-threshold` does not change saved masks.

### Cause

The threshold is used only when `net.n_classes == 1`. The default CLI uses `--classes 2`, which takes `argmax` over output channels instead.

### Fix

- Use `--classes 1` only with a one-output-channel binary checkpoint.
- For `--classes 2` or greater, tune logits/probabilities outside the stock CLI if you need non-argmax decision logic.

## Output mask is black, low contrast, or wrong colors

### Symptom

The saved mask opens but appears all black, nearly black, or with unexpected colors.

### Likely causes

- Checkpoint `mask_values` is `[0, 1]`, producing boolean/low-value pixels rather than display-friendly `0` and `255`.
- `mask_values` does not match the dataset palette used during training.
- Predicted class IDs exceed the length of `mask_values`, leaving those pixels at zero.
- RGB-like `mask_values` entries have inconsistent channel lengths or unexpected values.

### Fix

- Inspect the loaded `mask_values` metadata after popping it from the checkpoint.
- For binary display-only masks, convert to `0/255` after prediction if needed, but do not claim that is the original training palette unless it is.
- For multiclass masks, ensure `len(mask_values) >= net.n_classes` and that each palette entry has the intended scalar or RGB values.
- Validate with a small synthetic mask passed to `mask_to_image` before running full prediction.

## Saved mask has wrong filename or no file appears

### Symptom

- Expected output file is missing.
- Output file appears beside the input with `_OUT.png` suffix.
- Batch prediction fails with `IndexError`.

### Cause

- If `--output` is omitted, the CLI generates `<input_stem>_OUT.png`.
- If `--no-save` is set, no output masks are saved even when `--output` is provided.
- If explicit outputs are fewer than inputs, the loop eventually indexes past the output list.
- Parent directories are not created automatically.

### Fix

- Supply one output path per input or omit all outputs to use generated names.
- Remove `--no-save` when files should be written.
- Create output directories first.
- Use API prediction for stricter preflight validation of input/output list lengths.

## Scale errors and tiny images

### Symptom

- Assertion says resized image dimensions are zero.
- U-Net forward fails on very small synthetic images.
- Output shape surprises after using a non-default scale.

### Cause

Preprocessing computes `int(scale * width)` and `int(scale * height)`, and both must be positive. The U-Net downsamples four times, so extremely small effective sizes are unsafe even if nonzero. Prediction then interpolates logits back to the original image size.

### Fix

- Use `--scale 1.0` for tiny images.
- Prefer image dimensions at least `32x32` for smoke checks; larger dimensions are safer for real models.
- Remember that saved mask size should match the original input image size, not the scaled inference size.

## Image channel mismatch

### Symptom

The model's first convolution reports a channel mismatch, or grayscale prediction fails with the stock CLI.

### Cause

The CLI constructs `UNet(n_channels=3, ...)`. `predict_img` preprocessing turns grayscale images into one-channel arrays, which cannot feed a three-channel model.

### Fix

- Convert grayscale images to RGB before using the stock CLI with RGB checkpoints.
- Or use the API route with `UNet(n_channels=1, ...)` and a one-channel checkpoint.
- Do not load a three-channel checkpoint into a one-channel model or vice versa.

## Visualization blocks or fails in headless environments

### Symptom

- Prediction hangs waiting for a plot window.
- Matplotlib errors because no display is available.

### Cause

`--viz` calls a matplotlib display helper and blocks until the user closes the window.

### Fix

- Omit `--viz` for automation.
- Use `--no-save` without `--viz` for a pure no-write prediction run.
- If visualization is required on a server, configure a noninteractive matplotlib backend or adapt the API workflow to save figures instead of showing them.

## Evaluation asserts mask label range

### Symptom

- Binary evaluation raises `True mask indices should be in [0, 1]`.
- Multiclass evaluation raises `True mask indices should be in [0, n_classes[`.

### Cause

`evaluate` expects mask tensors to contain class IDs, not arbitrary raw RGB or grayscale values. For multiclass, every label must be less than `net.n_classes`.

### Fix

- Use dataset preprocessing that maps raw mask values through `mask_values` into class IDs.
- For custom dataloaders, convert palettes to integer labels before evaluation.
- Match `net.n_classes` to the maximum class ID plus one.
- Inspect `mask.min()` and `mask.max()` on a batch before calling `evaluate`.

## Dice shape assertion fails

### Symptom

`dice_coeff` raises an assertion because input and target sizes differ.

### Cause

Dice helpers require identical shapes. Common mistakes include comparing logits `(N,C,H,W)` with labels `(N,H,W)`, forgetting to squeeze binary channel dimensions, or forgetting one-hot conversion for multiclass targets.

### Fix

Binary:

```python
pred = torch.sigmoid(logits.squeeze(1)) > 0.5
target = labels.float()
score = dice_coeff(pred.float(), target, reduce_batch_first=False)
```

Multiclass:

```python
probs = torch.softmax(logits, dim=1).float()
target = torch.nn.functional.one_hot(labels, num_classes).permute(0, 3, 1, 2).float()
score = multiclass_dice_coeff(probs[:, 1:], target[:, 1:], reduce_batch_first=False)
```

## Multiclass Dice seems to ignore background

### Symptom

Validation Dice does not reward class-0/background agreement.

### Cause

`evaluate` explicitly slices `[:, 1:]` before `multiclass_dice_coeff`, so class 0 is treated as background and excluded from the reported multiclass Dice.

### Fix

This is expected repository behavior. If the user needs background-inclusive Dice, compute it directly with `multiclass_dice_coeff` without the `[:, 1:]` slice and document that it differs from the repository evaluation score.

## `evaluate` leaves the model in training mode

### Symptom

After calling `evaluate`, `net.training` is `True` even though evaluation set it to eval mode internally.

### Cause

The function calls `net.train()` before returning. This is intended for use inside the training loop.

### Fix

If you need the model to remain in eval mode after validation, call `net.eval()` again after `evaluate`.

## CUDA, CPU, and AMP issues

### Symptom

- Device mismatch errors.
- CUDA out-of-memory.
- AMP behavior differs from expectations.

### Cause

Prediction and evaluation move tensors to a chosen device, but model/tensor mismatches or large images can exceed memory. AMP is an optional autocast setting; it does not change masks, checkpoints, or class mapping.

### Fix

- Use CPU for functional smoke checks.
- Move the model to the same device passed into `predict_img` or `evaluate`.
- Lower `--scale`, input size, or validation batch size for memory pressure.
- Set `amp=False` unless acceleration is required and supported.
- CUDA-capable PyTorch on A100 was verified in the source environment, but GPU is optional for this sub-skill.

## Dependency/import problems

### Symptom

- `ModuleNotFoundError` for `torchvision`, `PIL`, `matplotlib`, `wandb`, `unet`, `predict`, or `evaluate`.
- Importing training code fails due to old `wandb`/`pkg_resources` compatibility.

### Cause

The runtime dependencies include PyTorch/torchvision plus NumPy, Pillow, matplotlib, tqdm, and wandb. The repository has no package metadata entry point, so top-level imports require the checkout/package location to be importable. Older `wandb` can need setuptools compatibility providing `pkg_resources`.

### Fix

- Install the runtime requirements in the active environment.
- Ensure the repository/package root is on `PYTHONPATH` or run from a checkout root for source-style usage.
- If `wandb 0.13.5` complains about `pkg_resources`, install a setuptools version that still provides it.
- Prediction-only imports do not need Kaggle credentials and should not run the data download helper.
