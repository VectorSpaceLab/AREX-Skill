# model-api troubleshooting

## Channel, class, and shape mismatch

### Symptom
- `RuntimeError` when loading a checkpoint.
- Unexpected output channel count from the model.
- Loss or metric code complains about label ranges.

### Cause
The model was constructed with the wrong `n_channels`, `n_classes`, or `bilinear` flag for the checkpoint or downstream pipeline.

### Fix
- Match `n_channels` to the input tensor channel count.
- Match `n_classes` to the training and prediction interpretation.
- Reuse the checkpoint's original `bilinear` flag.
- Check that binary tasks expecting one output channel are not being fed a two-class checkpoint, and vice versa.

### Quick check
Run the bundled smoke script and confirm the output shape equals `(1, n_classes, H, W)`.

## `mask_values` metadata error

### Symptom
- `load_state_dict` fails because of an unexpected key named `mask_values`.
- Predicted masks cannot be converted back to the original label palette.

### Cause
The training checkpoint stores `mask_values` alongside the model weights.

### Fix
Pop `mask_values` from the checkpoint before `load_state_dict`, then keep the popped value for later mask reconstruction.

```python
state_dict = torch.load(path, map_location=device)
mask_values = state_dict.pop("mask_values", [0, 1])
net.load_state_dict(state_dict)
```

If `mask_values` is absent from an older checkpoint, default to `[0, 1]` only when you know the task is binary.

## Bilinear versus transposed-convolution incompatibility

### Symptom
- Loading a checkpoint into the same class but with a different `bilinear` setting fails.

### Cause
The architecture changes internal channel widths and upsampling layers when `bilinear` changes.

### Fix
- Use the same `bilinear` value that was used during checkpoint creation.
- Do not expect pretrained Carvana weights to load into a `bilinear=True` network.

## Torch Hub download failure

### Symptom
- `torch.hub.load` stalls, errors, or cannot resolve the pretrained model.
- Network-restricted environments fail when requesting pretrained weights.

### Cause
The hub helper fetches the repository definition and, when `pretrained=True`, downloads a release checkpoint from GitHub storage.

### Fix
- Use `pretrained=False` when you only need the architecture.
- Pre-seed the cache or allow network access when you need the pretrained weights.
- Use one of the supported pretrained scales only: `0.5` or `1.0`.

## CUDA or memory pressure

### Symptom
- `torch.cuda.OutOfMemoryError` during forward/backward passes.
- A device mismatch error when moving the model or input.

### Cause
The local GPU does not have enough memory, or the model and tensor were not moved to the same device.

### Fix
- For smoke checks, use CPU.
- For training, lower the batch size or image scale.
- Move both model and inputs to the same device.
- As a fallback, call `model.use_checkpointing()` after catching OOM and retry.

## AMP confusion

### Symptom
- Expecting AMP to change model architecture or checkpoint format.

### Cause
Automatic mixed precision is a training/evaluation execution choice, not part of the model API.

### Fix
Treat AMP as optional execution tooling. It does not change `UNet`, `DoubleConv`, `Down`, `Up`, `OutConv`, or hub weights.

## Import failures

### Symptom
- `ImportError` or `ModuleNotFoundError` when importing `UNet`.

### Cause
The package is not installed or the checkout is not on `PYTHONPATH`.

### Fix
Run the smoke script from an environment that can import the package. If you are validating a checkout directly, make sure the repository root is on the Python path or the package is installed in the active environment.
