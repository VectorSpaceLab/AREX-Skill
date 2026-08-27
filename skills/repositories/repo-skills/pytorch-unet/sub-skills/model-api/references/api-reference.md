# Pytorch-UNet model API reference

This reference distills the public model and checkpoint contracts for Pytorch-UNet semantic segmentation. It is self-contained and does not require opening the original repository.

## Primary import surface

```python
from unet import UNet
```

The package-level `unet` module exports the full model class:

```python
model = UNet(n_channels=3, n_classes=2, bilinear=False)
```

Constructor signature and meaning:

| Argument | Type | Meaning |
| --- | --- | --- |
| `n_channels` | `int` | Number of input image channels. Use `3` for RGB images, `1` for grayscale or single-channel medical images, and match this to the channel dimension of tensors passed to `forward`. |
| `n_classes` | `int` | Number of per-pixel output channels/classes. Use `1` for a single sigmoid/BCE foreground mask workflow; use `2` or more for mutually exclusive classes with softmax/cross-entropy. Carvana pretrained weights use `2`. |
| `bilinear` | `bool` | `False` uses learned transposed-convolution upsampling. `True` uses bilinear interpolation followed by convolutions and halves the deepest channel width with an internal factor. |

Runtime attributes copied from constructor arguments:

- `model.n_channels`
- `model.n_classes`
- `model.bilinear`

The forward pass returns raw logits, not probabilities and not discrete masks:

```python
x = torch.randn(batch, n_channels, height, width)
logits = model(x)
assert logits.shape == (batch, n_classes, height, width)
```

A verified CPU smoke fact is that `UNet(3, 2, bilinear=False)` maps a tensor with shape `(1, 3, 32, 32)` to `(1, 2, 32, 32)`.

## Architecture block classes

Advanced users may import the block classes from the internal parts module when they need to inspect or extend the architecture:

```python
from unet.unet_parts import DoubleConv, Down, Up, OutConv
```

| Class | Constructor | Forward contract | Role |
| --- | --- | --- | --- |
| `DoubleConv` | `DoubleConv(in_channels, out_channels, mid_channels=None)` | one tensor `x -> double_conv(x)` | Two `3x3` convolutions with batch norm and in-place ReLU. If `mid_channels` is omitted, it equals `out_channels`. |
| `Down` | `Down(in_channels, out_channels)` | one tensor `x -> maxpool_conv(x)` | MaxPool2d by factor 2 followed by `DoubleConv`. |
| `Up` | `Up(in_channels, out_channels, bilinear=True)` | two tensors `x1, x2 -> conv(cat(skip, upsampled))` | Upsamples decoder tensor `x1`, pads it to the skip tensor `x2` spatial size, concatenates on channel dimension, then applies `DoubleConv`. |
| `OutConv` | `OutConv(in_channels, out_channels)` | one tensor `x -> 1x1 conv(x)` | Final `1x1` projection to `n_classes` logits. |

The full `UNet` assembly is:

1. `inc = DoubleConv(n_channels, 64)`
2. `down1 = Down(64, 128)`
3. `down2 = Down(128, 256)`
4. `down3 = Down(256, 512)`
5. `down4 = Down(512, 1024 // factor)` where `factor = 2 if bilinear else 1`
6. `up1 = Up(1024, 512 // factor, bilinear)`
7. `up2 = Up(512, 256 // factor, bilinear)`
8. `up3 = Up(256, 128 // factor, bilinear)`
9. `up4 = Up(128, 64, bilinear)`
10. `outc = OutConv(64, n_classes)`

`Up.forward` pads the upsampled decoder activation before concatenation. This makes odd spatial sizes more tolerant than a purely crop-based U-Net, but using input sizes divisible by 16 remains the safest choice because the encoder downsamples four times.

## Binary versus multiclass output conventions

The same `UNet` class is used for both binary and multiclass segmentation. Downstream loss/metric/prediction code chooses the interpretation based on `model.n_classes`:

- `n_classes == 1`: output shape is `(N, 1, H, W)`. Apply `torch.sigmoid(logits)` and a threshold such as `0.5` for a binary foreground mask. Training uses a BCE-with-logits style objective plus Dice loss.
- `n_classes > 1`: output shape is `(N, C, H, W)`. Apply `argmax(dim=1)` for class IDs or `softmax(dim=1)` for class probabilities. Training uses cross entropy plus multiclass Dice loss.

For the bundled Carvana model and the repo's default CLI paths, `n_channels=3` and `n_classes=2` are the expected values.

## Upsampling choice

`bilinear=False` is the default and uses learned `ConvTranspose2d` upsampling inside each `Up` block. This is also the configuration used by the Carvana torch.hub model.

`bilinear=True` switches each `Up` block to `nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)` followed by a `DoubleConv` whose intermediate channels reduce from `in_channels` to `in_channels // 2`. The top of the encoder also uses `1024 // 2` channels in this mode. This can reduce parameters and may be useful when avoiding transpose-convolution artifacts, but checkpoint weights are not interchangeable with the default architecture.

## Checkpoint state_dict convention

Training saves a raw PyTorch `state_dict`, not a wrapper object. The saved dictionary contains the model parameters plus an extra metadata key:

```python
state_dict = model.state_dict()
state_dict["mask_values"] = dataset.mask_values
torch.save(state_dict, checkpoint_path)
```

When loading a checkpoint into `UNet`, remove `mask_values` before `load_state_dict` because it is not a model parameter:

```python
state_dict = torch.load(checkpoint_path, map_location=device)
mask_values = state_dict.pop("mask_values", [0, 1])
model.load_state_dict(state_dict)
```

Keep `mask_values` for prediction output conversion: it maps integer class indices back to the original mask pixel values or RGB tuples. Typical binary Carvana masks use `[0, 1]`, but custom datasets can have other values discovered from training masks.

Checkpoint compatibility requires these construction choices to match the checkpoint:

- `n_channels`
- `n_classes`
- `bilinear`
- any manual architecture modifications

A common failure is trying to load a `n_classes=2` checkpoint into `UNet(n_classes=1)` or loading default transposed-convolution weights into a `bilinear=True` model.

## Torch Hub API

The repository exposes a torch.hub entry point named `unet_carvana`:

```python
import torch
net = torch.hub.load("milesial/Pytorch-UNet", "unet_carvana", pretrained=True, scale=0.5)
```

Distilled contract:

```python
unet_carvana(pretrained=False, scale=0.5)
```

- Always constructs `UNet(n_channels=3, n_classes=2, bilinear=False)`.
- With `pretrained=False`, no pretrained weights are downloaded.
- With `pretrained=True`, supported `scale` values are exactly `0.5` and `1.0`.
- Unsupported pretrained scales raise a runtime error.
- Downloaded pretrained state dicts may include `mask_values`; the hub function removes that key before loading.

Network caution: `torch.hub.load` and `torch.hub.load_state_dict_from_url` can access GitHub/release URLs and cache artifacts. Do not use them in offline, no-network, or hermetic checks unless the required hub repository and weights are already cached or the user explicitly permits network access.

## Optional checkpointing fallback

The model class includes `use_checkpointing()` intended as an out-of-memory fallback. It wraps the main blocks with PyTorch checkpointing so activations can be recomputed during backward rather than fully stored. Use it only after constructing the model and before retrying a memory-heavy training step:

```python
try:
    train_or_forward_backward(model)
except torch.cuda.OutOfMemoryError:
    torch.cuda.empty_cache()
    model.use_checkpointing()
    train_or_forward_backward(model)
```

This fallback trades speed for memory. It is not needed for the bundled forward smoke check.

## Device and precision notes

- CPU is enough to prove that imports, construction, and output shape are functional.
- CUDA acceleration is optional. Live verification observed CUDA-capable PyTorch 2.5.1+cu124 working on A100 hardware, but this skill does not require a GPU.
- AMP is used by training/evaluation code through `torch.autocast`. It is an accelerator option, not a different model API.
- When training with channels-last memory format, the model may be moved with `model.to(memory_format=torch.channels_last)`, and image tensors are moved with `memory_format=torch.channels_last`. This is optional for API smoke checks.
