# Pretraining and Adaptation Workflows

## Purpose

Read this reference when a user asks for vit-pytorch distillation,
self-supervised pretraining, adaptation, or one-step loss checks. It summarizes
which wrapper to choose, how to construct it with tiny safe tensors, what the
forward pass returns, and which dependencies or data are needed beyond the base
package.

Use the bundled smoke helper before long training:

```bash
python sub-skills/pretraining-and-adaptation/scripts/smoke_pretraining_wrappers.py
```

## Status vocabulary

The smoke helper reports:

- `verified`: the tiny CPU construction and forward/loss check passed in the
  current runtime.
- `version_fragile`: the wrapper is known to be sensitive to current package
  token/positional-embedding shapes; the helper reproduced or detected that
  fragility.
- `dependency_gap`: an optional package such as `torchvision`, `torchaudio`,
  `accelerate`, `wandb`, `huggingface_hub`, or `safetensors` is missing or
  incompatible for the requested wrapper.
- `unexpected_failure`: a wrapper expected to pass failed; read
  [troubleshooting.md](troubleshooting.md) and avoid full training until the
  first-step smoke is fixed.

## Wrapper map

| User asks about | Import / construct | Inputs | Forward output | One-step smoke expectation | Notes |
| --- | --- | --- | --- | --- | --- |
| Distillation / DeiT-style token | `from vit_pytorch.distill import DistillableViT, DistillWrapper` | images `(b, 3, h, w)` and integer labels `(b,)`; teacher returns class logits | scalar mixed CE/KL loss from `DistillWrapper`; converted student logits from `.to_vit()` | verified finite scalar loss | README teacher example uses `torchvision.models.resnet50`; a tiny local teacher is enough for smoke. |
| MAE | `from vit_pytorch import MAE` with a `ViT` encoder | images `(b, 3, h, w)` | intended scalar MSE reconstruction loss | current base-`ViT` smoke is `version_fragile` | Check positional-embedding shape before claiming it works after upgrades. |
| SimMIM | `from vit_pytorch.simmim import SimMIM` | images `(b, 3, h, w)` | intended scalar L1 reconstruction loss | current base-`ViT` smoke is `version_fragile` | Same positional-embedding pitfall as MAE. |
| MPP | `from vit_pytorch.mpp import MPP` with a transformer exposing ViT token internals | images `(b, c, h, w)` with values matching `max_pixel_val` | intended scalar masked patch classification loss | current base-`ViT` smoke is `version_fragile` | Encoder/token-shape assumptions differ from current base `ViT`. |
| MP3 | `from vit_pytorch.mp3 import ViT, MP3` | images `(b, 3, h, w)` | scalar position-prediction CE loss | verified finite scalar loss | Use the `ViT` class from `vit_pytorch.mp3`, not the top-level base `ViT`. |
| DINO | `from vit_pytorch import Dino` around a classifier backbone | images `(b, 3, image_size, image_size)` | scalar self-supervised view loss; optional embeddings | verified finite scalar loss with identity augmentations | Requires `torchvision`; `hidden_layer` must resolve to a layer/module that emits the embedding. Call `update_moving_average()` after optimizer steps. |
| EsViT | `from vit_pytorch.es_vit import EsViTTrainer` around a multistage backbone | images `(b, 3, image_size, image_size)` | scalar view + region self-supervised loss | verified finite scalar loss with a tiny CvT pattern | Requires `torchvision`; `hidden_layer` should emit regional feature maps, not only pooled logits. |
| Learnable Memory ViT | `from vit_pytorch.learnable_memory_vit import ViT, Adapter` | images `(b, 3, h, w)` | task logits `(b, num_classes)` | verified finite logits/backward | `Adapter` expects the module-specific `ViT` class and freezes it; do not pass the top-level base `ViT`. |
| LeJEPA | `from vit_pytorch.lejepa import LeJEPA` around a backbone | images `(b, 3, image_size, image_size)` | scalar target + SigReg loss | verified finite scalar loss with reduced SigReg settings | Requires `torchvision`; default SigReg settings are heavier than the tiny smoke. |
| VAT | `from vit_pytorch.vat import ViT, VAT` | image/view tensor `(b, v, c, h, w)` or video/view tensor `(b, v, c, t, h, w)` plus optional `actions` `(b, k, dim_action)` | L1 loss when actions are supplied; predicted actions `(b, k, dim_action)` otherwise | verified finite loss and prediction shape | Use explicit view/time dimensions in smoke inputs. Route pure video-shape questions to the variable-shapes/video sub-skill. |
| SigLIP-VAT | `from vit_pytorch.vat_siglip import SigLIPVAT` | same action-wrapper convention as VAT | L1 loss or predicted action chunks | verified with a tiny randomly initialized SigLIP backbone | `load_siglip()` is optional and downloads/loads checkpoints; do not call it in a smoke unless checkpoint dependencies and storage are approved. |
| VAAT | `from vit_pytorch.vaat import VAAT` | image/video views plus raw audio or spectrograms plus optional actions | action loss or predictions | optional import check only by default | Requires `torchaudio`; audio data layout and spectrogram settings must be chosen deliberately. |
| WWT | `from vit_pytorch.wwt import WWT` | images `(b, 3, h, w)` | class logits, optional token logits, task-head outputs, and/or SigReg loss | verified finite logits and optional SigReg loss | `num_slots` must form a strictly decreasing hierarchy. |
| Decorrelation auxiliary loss | `from vit_pytorch.vit_with_decorr import ViT` | images and labels for the task loss | `(logits, decorr_aux_loss)` | verified finite logits and scalar aux loss | Full CIFAR-style training needs data/downloads and optional training packages; the bundled helper is no-download. |

## Distillation pattern

Use this route when the user has a teacher model and a distillable vit-pytorch
student. The student must be one of the distillable classes; `DistillWrapper`
asserts this.

```python
import torch
from torch import nn
from vit_pytorch.distill import DistillableViT, DistillWrapper

student = DistillableViT(
    image_size=16,
    patch_size=8,
    num_classes=5,
    dim=32,
    depth=1,
    heads=2,
    dim_head=16,
    mlp_dim=64,
)
teacher = nn.Sequential(nn.Flatten(), nn.Linear(3 * 16 * 16, 5))

distiller = DistillWrapper(
    student=student,
    teacher=teacher,
    temperature=2.0,
    alpha=0.5,
    hard=False,
)

images = torch.randn(2, 3, 16, 16)
labels = torch.randint(0, 5, (2,))
loss = distiller(images, labels)
loss.backward()
plain_vit = student.to_vit()
logits = plain_vit(images)
```

Expected: `loss` is a scalar finite tensor and `logits.shape == (2, 5)`.
For a real teacher, ensure the teacher output class dimension equals the student
`num_classes` and that preprocessing matches the teacher’s training recipe.

## Masked pretraining patterns

### MAE and SimMIM

Both wrappers extract patching and transformer internals from an encoder and
are intended to return reconstruction losses:

- `MAE(encoder=vit, masking_ratio=0.75, decoder_dim=..., decoder_depth=...)`
  reconstructs masked patch pixels with a decoder and MSE loss.
- `SimMIM(encoder=vit, masking_ratio=0.5)` replaces masked tokens and predicts
  masked patch pixels with an L1 loss.

Current base-`ViT` compatibility is fragile because the wrapper code expects a
batched positional-embedding layout while the current base `ViT` exposes a
2-D positional embedding. Use the helper to detect whether the installed
version has been fixed before suggesting these wrappers for full training.

### MPP

`MPP(transformer=..., patch_size=..., dim=..., mask_prob=..., replace_prob=...)`
implements masked patch classification. It expects a transformer object with
specific patch embedding, class-token, positional-embedding, dropout, and
transformer internals. With the current base `ViT`, tiny smoke reproduces a
class-token/token-shape failure. Prefer MP3 for a currently verified masked
position pretraining path unless the user provides a compatible encoder or a
package version where MPP passes the smoke.

### MP3

Use the module-local `vit_pytorch.mp3.ViT` with `MP3`, because it exposes the
context-attention behavior expected by the MP3 wrapper:

```python
import torch
from vit_pytorch.mp3 import ViT, MP3

vit = ViT(
    image_size=16,
    patch_size=8,
    num_classes=5,
    dim=32,
    depth=1,
    heads=2,
    dim_head=16,
    mlp_dim=64,
)
learner = MP3(vit=vit, masking_ratio=0.5)
loss = learner(torch.randn(2, 3, 16, 16))
loss.backward()
```

Expected: a scalar finite cross-entropy loss over patch positions.

## DINO, EsViT, and LeJEPA

These wrappers use crop/augmentation modules and hidden-layer extraction.
Before training:

1. Verify `torchvision` imports successfully.
2. Choose `hidden_layer` carefully.
   - For a top-level `ViT` in DINO/LeJEPA smoke, `hidden_layer='to_latent'`
     hooks the pooled embedding before the classifier.
   - For EsViT, the hook must emit regional feature maps shaped like
     `(batch, channels, height, width)` so the regional loss can be computed.
3. Use identity augmentations in tiny smoke checks when you only need to prove
   wrapper wiring. Use real stochastic augmentations only for actual training.
4. For DINO and EsViT, call `update_moving_average()` after each optimizer step
   once the first forward has created the teacher encoder.

The constructors run an internal mock forward to instantiate singleton
projectors/teacher state. If construction fails, it usually means the
`hidden_layer`, image size, augmentation dependency, or feature shape is wrong.

## Adaptation and fine-tuning patterns

### Learnable Memory ViT

Use `vit_pytorch.learnable_memory_vit.ViT` and `Adapter`. The adapter freezes
the supplied ViT and adds learnable memory tokens and a task-specific head:

```python
from vit_pytorch.learnable_memory_vit import ViT, Adapter

vit = ViT(image_size=16, patch_size=8, num_classes=5, dim=32, depth=1,
          heads=2, dim_head=16, mlp_dim=64)
adapter = Adapter(vit=vit, num_classes=3, num_memories_per_layer=2)
logits = adapter(images)  # (batch, 3)
```

Use this for fine-tuning new task heads while keeping the original backbone
mostly fixed.

### VAT, SigLIP-VAT, and VAAT

VAT-style modules adapt visual (and optionally audio) representations to action
chunks. Supply `actions` to get a supervised L1 loss; omit `actions` to get
predicted action chunks.

- Prefer image/view inputs shaped `(batch, views, channels, height, width)` for
  current smoke checks, even when there is only one view.
- For time-aware variants, use `(batch, views, channels, time, height, width)`
  and set `time_seq_len` consistently.
- `tasks`, `advantages`, and `extra` are optional conditioning signals, but the
  constructor must enable them with `num_tasks`, `num_advantage_bins`, or
  `dim_extra_token` before they are passed to `forward`.
- `SigLIPVAT.load_siglip()` is a heavyweight checkpoint path; keep it separate
  from one-step random-tensor smoke checks.
- VAAT imports `torchaudio` at module import time and needs audio/spectrogram
  decisions in addition to image/video shapes.

### WWT

WWT builds a whole-within-token hierarchy. The important construction rule is
that `num_slots` must be strictly decreasing, for example `(4, 2)` in a tiny
smoke. Depending on flags, `forward` may return plain logits or a tuple with
extra losses/task-head outputs. Always inspect the actual return structure in a
one-step check before writing a training loop.

### vit_with_decorr

`vit_with_decorr.ViT` adapts a standard classifier with an auxiliary
decorrelation loss. The full training recipe uses CIFAR-style data,
`torchvision`, `accelerate`, and W&B; do not run it as a default smoke. The
safe pattern is:

```python
import torch
import torch.nn.functional as F
from vit_pytorch.vit_with_decorr import ViT

model = ViT(image_size=16, patch_size=8, num_classes=5, dim=32, depth=1,
            heads=2, dim_head=16, mlp_dim=64, decorr_sample_frac=1.0)
model.train()
logits, aux = model(torch.randn(2, 3, 16, 16))
loss = F.cross_entropy(logits, torch.randint(0, 5, (2,))) + 0.1 * aux
loss.backward()
```

Expected: `logits.shape == (2, 5)` and `aux` is a scalar finite tensor.
