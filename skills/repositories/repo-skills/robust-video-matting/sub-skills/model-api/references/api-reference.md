# MattingNetwork API Reference

## When to read

Read this when you need exact RVM PyTorch model call contracts: constructor
arguments, accepted tensor ranks, output shapes, recurrent states, variants,
refiners, and segmentation-pass behavior.

## Verified signatures

The public model class is imported from `model`:

```python
from model import MattingNetwork
```

Verified constructor signature:

```python
MattingNetwork(
    variant: str = "mobilenetv3",
    refiner: str = "deep_guided_filter",
    pretrained_backbone: bool = False,
)
```

Accepted values from source assertions:

- `variant`: `"mobilenetv3"` or `"resnet50"`.
- `refiner`: `"deep_guided_filter"` or `"fast_guided_filter"`.
- `pretrained_backbone=True` asks TorchVision to download ImageNet backbone
  weights; keep it `False` for offline smoke tests.

Verified forward signature:

```python
MattingNetwork.forward(
    src: torch.Tensor,
    r1: Optional[torch.Tensor] = None,
    r2: Optional[torch.Tensor] = None,
    r3: Optional[torch.Tensor] = None,
    r4: Optional[torch.Tensor] = None,
    downsample_ratio: float = 1,
    segmentation_pass: bool = False,
)
```

## Input contract

`src` must be RGB in channel-first order and normalized to `0..1`.

| Mode | Accepted rank | Shape | Notes |
| --- | --- | --- | --- |
| Single frame or batch | 4D | `[B, C, H, W]` | `C` should be 3 for RGB. |
| Chunked video | 5D | `[B, T, C, H, W]` | The model flattens time for encoder/refiner steps, then returns only the final recurrent state for each ConvGRU layer. |

Do not pass channel-last `[H,W,C]` or `[B,H,W,C]` tensors directly. Convert
from PIL/NumPy/video readers with channel-first tensor transforms.

`downsample_ratio` controls the low-resolution stage. If it is not `1`, the
model downsamples `src`, runs the backbone/decoder at that lower scale, then
uses the refiner to return outputs at the original input resolution.

## Output contract

Default matting mode (`segmentation_pass=False`) returns:

```python
fgr, pha, r1o, r2o, r3o, r4o = model(src, r1, r2, r3, r4, downsample_ratio)
```

| Output | Meaning | Shape pattern | Range |
| --- | --- | --- | --- |
| `fgr` | Estimated foreground RGB | same batch/time/spatial shape as `src`, channel count 3 | clamped to `0..1` |
| `pha` | Alpha matte | same batch/time/spatial dimensions, channel count 1 | clamped to `0..1` |
| `r1o..r4o` | Recurrent states from the four ConvGRU blocks | rank-4 tensors | carry into the next frame or chunk |

In a verified CPU smoke with `mobilenetv3`, input `[1,3,32,32]`, and
`downsample_ratio=0.5`, the recurrent state shapes were:

```text
r1: [1, 16, 8, 8]
r2: [1, 20, 4, 4]
r3: [1, 40, 2, 2]
r4: [1, 64, 1, 1]
```

State channel/spatial sizes depend on the variant, input size, and downsample
ratio. Treat the returned tensors as opaque memory; do not manually reshape or
slice them unless debugging internals.

Segmentation mode (`segmentation_pass=True`) returns:

```python
seg, r1o, r2o, r3o, r4o = model(src, r1, r2, r3, r4, downsample_ratio, segmentation_pass=True)
```

`seg` is a single-channel segmentation logit tensor, not an alpha matte. Apply
an appropriate sigmoid/loss only in training or diagnostic contexts.

## Model variants and components

`mobilenetv3` uses a MobileNetV3 Large encoder, LR-ASPP, recurrent decoder, and
guided-filter refiner. It is the recommended model for most tasks.

`resnet50` uses a ResNet-50 encoder with dilation in later stages, LR-ASPP,
recurrent decoder, and guided-filter refiner. It is larger and can improve
quality slightly at higher compute cost.

The recurrent decoder contains four ConvGRU locations. This is why every normal
call accepts and returns exactly four recurrent states. For independent images,
initial states can be `[None] * 4`, but for video matting recycle the returned
states in order.

## Minimal model loop

```python
import torch
from model import MattingNetwork

model = MattingNetwork("mobilenetv3").eval().to("cuda")
rec = [None] * 4

with torch.no_grad():
    for src in frames:  # src: [B,3,H,W], RGB, float 0..1
        src = src.to("cuda")
        fgr, pha, *rec = model(src, *rec, downsample_ratio=0.25)
```

For chunked frames:

```python
src = batch_of_frames  # [B,T,3,H,W]
fgr, pha, *rec = model(src, *rec, downsample_ratio=0.25)
# carry rec into the next chunk; do not keep all intermediate states yourself
```

## Safe validation

Use the bundled script from this sub-skill:

```bash
python scripts/rvm_model_smoke.py --repo-root /path/to/RobustVideoMatting --variant mobilenetv3 --device cpu
```

The script prints JSON containing input, output, and recurrent-state shapes. It
is a functional smoke test, not a quality or speed benchmark.
