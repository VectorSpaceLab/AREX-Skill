# vit-pytorch API Reference

## Purpose

Read this for top-level package facts that several sub-skills share: install expectations, imported names, and the smallest verified constructor patterns. Deeper workflow details live in the nearest sub-skill references.

## Verified package facts

- Distribution name: `vit-pytorch`.
- Import root: `vit_pytorch`.
- Public runtime dependency floor from package metadata: `einops>=0.8.2`, `torch>=2.4`, `torchvision`.
- Optional package behavior in this snapshot: `vit_pytorch.vaat` imports `torchaudio` at module import time; treat VAAT as optional unless `torchaudio` is installed.
- No console entry points were declared in `pyproject.toml`.

## Top-level exports verified from the installed package

```python
from vit_pytorch import ViT, SimpleViT, MAE, Dino
```

These names are available from `vit_pytorch.__init__` in the installed package snapshot and are the most common starting point for 2D image and pretraining workflows.

## Small verified constructor patterns

### Base ViT

```python
from vit_pytorch import ViT

model = ViT(
    image_size = 32,
    patch_size = 8,
    num_classes = 7,
    dim = 32,
    depth = 1,
    heads = 2,
    dim_head = 16,
    mlp_dim = 64,
)
```

Installed signature:

```text
ViT(*, image_size, patch_size, num_classes, dim, depth, heads, mlp_dim, pool='cls', channels=3, dim_head=64, dropout=0.0, emb_dropout=0.0)
```

Behavior notes:

- `pool` accepts `cls` or `mean`.
- A positive `num_classes` returns logits; `num_classes <= 0` returns token features in this source snapshot.
- `image_size` and `patch_size` must divide exactly for patch-based inputs.

### SimpleViT

```python
from vit_pytorch import SimpleViT

model = SimpleViT(
    image_size = 32,
    patch_size = 8,
    num_classes = 7,
    dim = 32,
    depth = 1,
    heads = 2,
    dim_head = 16,
    mlp_dim = 64,
)
```

Installed signature:

```text
SimpleViT(*, image_size, patch_size, num_classes, dim, depth, heads, mlp_dim, channels=3, dim_head=64)
```

Behavior notes:

- No `pool`, `dropout`, or `emb_dropout` constructor arguments.
- 2D sin/cos positional embeddings require `dim % 4 == 0`.

### MAE and Dino

```python
from vit_pytorch import MAE, Dino
```

Installed signatures:

```text
MAE(*, encoder, decoder_dim, masking_ratio=0.75, decoder_depth=1, decoder_heads=8, decoder_dim_head=64)
Dino(net, image_size, hidden_layer=-2, projection_hidden_size=256, num_classes_K=65336, projection_layers=4, student_temp=0.9, teacher_temp=0.04, local_upper_crop_scale=0.4, global_lower_crop_scale=0.5, moving_average_decay=0.9, center_moving_average_decay=0.9, augment_fn=None, augment_fn2=None)
```

Behavior notes:

- MAE and SimMIM are currently version-fragile against the installed base ViT positional-embedding layout; see the pretraining sub-skill troubleshooting guide.
- DINO and related wrappers need `torchvision` for their default augmentation pipeline, though identity augmentations work for smoke checks.

## Module import notes

Common module paths that were verified to import in this snapshot include:

- `vit_pytorch.vit`
- `vit_pytorch.simple_vit`
- `vit_pytorch.na_vit`
- `vit_pytorch.vit_3d`
- `vit_pytorch.cct`
- `vit_pytorch.cross_vit`
- `vit_pytorch.recorder`
- `vit_pytorch.extractor`
- `vit_pytorch.vivit`

If you need a specific family signature, read the nearest sub-skill reference instead of guessing from the README snippet alone.
