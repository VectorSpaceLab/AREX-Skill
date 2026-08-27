# Classification API Reference

This reference distills the public MambaVision classification package API and the source-verified model behavior. It is intended for future agents using an installed `mambavision` package; it does not require the original repository checkout.

## Installation surface

Minimum classification package install:

```bash
python -m pip install mambavision
```

For CUDA inference, install a CUDA-enabled PyTorch build compatible with the host driver before or alongside `mambavision`. The package depends on:

- `timm==1.0.15`
- `transformers==4.50.0`
- `mamba-ssm==2.2.4`
- `einops==0.8.1`
- `requests==2.32.3`
- `Pillow==11.1.0`

The source requirements also name `torch>=2.6.0+cu124` and `tensorboardX==2.6.2.2`. `tensorboardX` is training-related, not needed for basic classification inference.

## Public entry point

```python
from mambavision import create_model

model = create_model(
    model_name,
    pretrained=False,
    checkpoint_path="",
    **kwargs,
)
```

Verified signature:

```text
create_model(model_name, pretrained=False, checkpoint_path='', **kwargs)
```

Behavior:

- `model_name` must be one of the registered factory names listed below.
- `pretrained=False` constructs the architecture without downloading weights. Use this for no-network smoke tests.
- `pretrained=True` calls the selected factory with its default config. If `model_path` does not already exist, the factory downloads the checkpoint URL from the model default config to `model_path`, then loads it.
- `checkpoint_path="./checkpoints/local.pth.tar"` loads a local state dict after model construction. This is independent of the `pretrained` download path.
- Extra `**kwargs` are forwarded to the factory and/or model constructor. Common source-defined overrides include `num_classes`, `in_chans`, `depths`, `num_heads`, `window_size`, `dim`, `in_dim`, `resolution`, `drop_path_rate`, and `layer_scale` for larger models.
- The default head is `num_classes=1000`; therefore `model(x)` returns logits shaped `[B, 1000]` unless `num_classes` is overridden.

Registered factories:

```text
mamba_vision_T
mamba_vision_T2
mamba_vision_S
mamba_vision_B
mamba_vision_B_21k
mamba_vision_L
mamba_vision_L_21k
mamba_vision_L2
mamba_vision_L2_512_21k
mamba_vision_L3_256_21k
mamba_vision_L3_512_21k
```

To inspect the registry at runtime:

```python
from mambavision.models.registry import (
    list_models,
    is_model,
    is_model_pretrained,
    get_model_default_value,
)

print(list_models("mamba_vision*"))
print(is_model("mamba_vision_T"))
print(is_model_pretrained("mamba_vision_T"))
print(get_model_default_value("mamba_vision_T", "input_size"))
```

`timm` may emit deprecation warnings for `timm.models.registry` or `timm.models.layers` imports. Treat those warnings as non-fatal unless import or model construction actually fails.

## No-download classification smoke

Use `pretrained=False` and omit `model_path` for a smoke test that cannot download a checkpoint:

```python
import torch
from mambavision import create_model

model = create_model("mamba_vision_T", pretrained=False)
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

x = torch.rand(1, 3, 65, 97, device=device)
with torch.inference_mode():
    logits = model(x)

assert logits.shape == (1, 1000)
assert torch.isfinite(logits).all()
```

The architecture pads internal attention windows as needed, so height and width do not need to equal the default training resolution. Keep `in_chans=3` unless you intentionally modify the first patch embedding and accept that pretrained checkpoints may no longer match.

For a bundled command-line version, use:

```bash
python sub-skills/classification/scripts/smoke_mambavision_inference.py \
  --model mamba_vision_T \
  --device cuda \
  --height 65 \
  --width 97 \
  --batch-size 1
```

## Local checkpoint loading

Use `checkpoint_path` when you already have a `.pth` or `.pth.tar` file:

```python
from mambavision import create_model

model = create_model(
    "mamba_vision_T",
    pretrained=False,
    checkpoint_path="./checkpoints/mambavision_tiny_1k.pth.tar",
)
```

Checkpoint loading accepts common `state_dict` and `state_dict_ema` wrappers. If the checkpoint was saved from `DataParallel`, the loader strips a leading `module.` prefix.

Use `model_path` only with `pretrained=True` to control the cache/download destination:

```python
model = create_model(
    "mamba_vision_T",
    pretrained=True,
    model_path="./checkpoints/mambavision_tiny_1k.pth.tar",
)
```

If `./checkpoints/mambavision_tiny_1k.pth.tar` is absent, this command attempts a network download. If you need strictly offline behavior, keep `pretrained=False` and pass `checkpoint_path` only when a local checkpoint is present.

## Forward and feature APIs

Pip/source model object:

```python
logits = model(images)                 # [batch, 1000] by default
pooled = model.forward_features(images) # [batch, feature_dim]
```

`forward_features` returns final average-pooled flattened features from the classifier backbone, not four stage feature maps. Typical `feature_dim` values are:

| Family | Feature dim |
| --- | ---: |
| `mamba_vision_T`, `mamba_vision_T2` | 640 |
| `mamba_vision_S` | 768 |
| `mamba_vision_B`, `mamba_vision_B_21k` | 1024 |
| `mamba_vision_L`, `mamba_vision_L_21k`, `mamba_vision_L2`, `mamba_vision_L2_512_21k` | 1568 |
| `mamba_vision_L3_256_21k`, `mamba_vision_L3_512_21k` | 2048 |

Example:

```python
import torch
from mambavision import create_model

model = create_model("mamba_vision_T", pretrained=False).cuda().eval()
images = torch.rand(2, 3, 224, 224, device="cuda")
with torch.inference_mode():
    features = model.forward_features(images)
    logits = model(images)
print(features.shape)  # torch.Size([2, 640]) for mamba_vision_T
print(logits.shape)    # torch.Size([2, 1000])
```

## Hugging Face recipe

MambaVision checkpoints are also available through Hugging Face Transformers with remote code enabled. This path is useful when a user specifically wants the model cards, label metadata, or the Transformers `AutoModel*` interface.

Classification:

```python
from transformers import AutoModelForImageClassification
from timm.data.transforms_factory import create_transform
from PIL import Image
import torch

model = AutoModelForImageClassification.from_pretrained(
    "nvidia/MambaVision-T-1K",
    trust_remote_code=True,
).cuda().eval()

image = Image.open("./example.jpg").convert("RGB")
transform = create_transform(
    input_size=(3, 224, 224),
    is_training=False,
    mean=model.config.mean,
    std=model.config.std,
    crop_mode=model.config.crop_mode,
    crop_pct=model.config.crop_pct,
)
inputs = transform(image).unsqueeze(0).cuda()
with torch.inference_mode():
    outputs = model(inputs)
logits = outputs["logits"]
label = model.config.id2label[int(logits.argmax(-1))]
```

Feature extraction through Transformers:

```python
from transformers import AutoModel

model = AutoModel.from_pretrained(
    "nvidia/MambaVision-T-1K",
    trust_remote_code=True,
).cuda().eval()
with torch.inference_mode():
    pooled, stage_features = model(inputs)
print(pooled.shape)          # final pooled features
print(len(stage_features))   # 4 hierarchical stages
```

This Hugging Face path downloads model code and weights from Hugging Face unless they are already cached. It is not the right path for a no-download smoke test.

## Quick validation checks

After model construction, check:

```python
assert hasattr(model, "num_classes")
assert model.num_classes == 1000
assert model.default_cfg["input_size"][0] == 3
assert torch.isfinite(logits).all()
```

For classification workflows that require CUDA, verify `torch.cuda.is_available()` before moving tensors to CUDA. If CUDA is unavailable or `mamba_ssm` cannot import its selective scan interface, go to `troubleshooting.md`.
