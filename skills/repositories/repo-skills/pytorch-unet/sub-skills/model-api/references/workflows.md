# model-api workflows

This reference summarizes the practical ways to use the Pytorch-UNet model API safely.

## 1. Create a model for a custom segmentation task

Choose the model shape from the data and label space first:

- `n_channels=3` for RGB imagery.
- `n_channels=1` for grayscale or single-channel inputs.
- `n_classes=1` for a binary foreground-vs-background mask if the downstream code expects a sigmoid output.
- `n_classes>1` for multiclass semantic segmentation with mutually exclusive classes.
- `bilinear=False` unless you intentionally want interpolation-based upsampling.

Minimal construction:

```python
from unet import UNet

net = UNet(n_channels=3, n_classes=2, bilinear=False)
```

After construction, confirm the forward shape with a tiny tensor:

```python
x = torch.randn(1, 3, 32, 32)
y = net(x)
assert y.shape == (1, 2, 32, 32)
```

If you change either the input channels or the class count, update all downstream checkpoints, losses, and prediction logic to match.

## 2. Select bilinear or transposed-convolution upsampling

Use `bilinear=False` when you want the default learned decoder path. This is the configuration used by the pretrained Carvana hub model and the repository's baseline training path.

Use `bilinear=True` when you want interpolation-based upsampling in each `Up` block. This reduces the deepest decoder width by a factor of two inside the architecture. Important consequences:

- Parameter shapes differ from the default model.
- Checkpoints saved from the default architecture will not load into a `bilinear=True` model unless they were trained with the same flag.
- Reverse compatibility is also false.

Rule of thumb: if you are loading a checkpoint, reuse the exact `bilinear` setting that produced it.

## 3. Load a training checkpoint

Training checkpoints are plain `state_dict`s with one extra key: `mask_values`.

Recommended load flow:

```python
state_dict = torch.load(path, map_location=device)
mask_values = state_dict.pop("mask_values", [0, 1])
net.load_state_dict(state_dict)
```

If the checkpoint was created for a different architecture, loading will fail with missing or unexpected key errors. Before retrying, verify all of the following:

- `n_channels` matches the saved model.
- `n_classes` matches the saved model.
- `bilinear` matches the saved model.
- You are not trying to load a prediction-only artifact that was not saved as a model `state_dict`.

The `mask_values` entry is not optional metadata; it preserves the original label palette and is needed when you later convert predicted class IDs back to image masks.

## 4. Use the torch.hub Carvana model

The repository publishes a torch.hub helper named `unet_carvana`.

Recommended usage:

```python
import torch
net = torch.hub.load("milesial/Pytorch-UNet", "unet_carvana", pretrained=True, scale=0.5)
```

Facts to remember:

- Supported pretrained scales are `0.5` and `1.0` only.
- The returned network is always `UNet(3, 2, bilinear=False)`.
- Pretrained loading may fetch a remote checkpoint from GitHub release storage.
- If `pretrained=False`, the function still returns the correctly configured model but skips the download.

Use the pretrained model when you want a known-good binary segmentation baseline for Carvana-like imagery. Do not use it as a generic pretraining source for unrelated class counts or channel counts.

## 5. Run a CPU smoke check

Use the bundled smoke script when you need a quick confidence check that the model imports and produces the expected tensor shape.

Expected checks:

- `UNet` imports successfully.
- A tiny CPU input tensor runs through the model.
- The output shape matches `(1, n_classes, H, W)`.
- JSON status is printed for automated tooling.

This is the safest validation path when CUDA is not available or when you only need API-level confirmation.

## 6. Run a CUDA smoke check when available

If a CUDA device is present and the local PyTorch build supports it, you can run the same smoke path on GPU.

Use CUDA only for an optional confirmation that the model moves to the device and still returns the expected tensor shape. The model API does not require CUDA to be functional.

Be aware of these accelerator-specific issues:

- A device mismatch error usually means the model or tensor was not moved to the same device.
- CUDA out-of-memory during smoke checks usually means the input is too large for the test machine; reduce the tensor size.
- AMP is not necessary for a forward-only smoke check.

## 7. Handle checkpointing fallback

The model includes a checkpointing fallback for memory pressure during training or heavy backward passes.

Workflow:

1. Try the normal training or backward pass.
2. Catch `torch.cuda.OutOfMemoryError`.
3. Call `model.use_checkpointing()`.
4. Retry the same step with a smaller memory footprint.

This is a recovery path, not a first-choice configuration. It exists because the model is deep enough that some devices may not fit the default decoder memory cost.

## 8. Pick the right downstream path

If you are working on data loading, dataset folder layout, or mask preprocessing, use the data-training skill.

If you are working on `predict.py`, `evaluate.py`, mask image conversion, or CLI behavior, use the prediction-evaluation skill.

If your task is only about creating the right model object, matching checkpoint shapes, or verifying a forward pass, this sub-skill is the correct entry point.
