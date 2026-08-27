---
name: model-internals
description: "Explain and verify the photo2cartoon generator, discriminator,
  normalization layers, face-ID feature path, tensor utilities, and checkpoint
  structure."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Internals

Use this sub-skill for the model core only: architecture, forward signatures, normalization layers, checkpoint contents, and safe synthetic verification.

## Start here

- [Architecture reference](references/architecture-reference.md) for generator/discriminator tuples, hourglass topology, Soft-AdaLIN / LIN behavior, CAM heatmaps, and verified smoke shapes.
- [Training object reference](references/training-object-reference.md) for `UgatitSadalinHourglass`, losses, optimizer setup, checkpoint keys, and save/load behavior.
- [Face ID loss reference](references/face-id-loss.md) for `FaceFeatures`, MobileFaceNet cropping, 112×112 embeddings, and cosine-distance loss.
- [Image and tensor utilities](references/image-and-tensor-utils.md) for normalization range, CAM rendering, and helper semantics.
- [Troubleshooting](references/troubleshooting.md) for shape mismatch, checkpoint key errors, deprecated `F.upsample`, device mismatch, and missing face-ID assets.
- [Synthetic smoke](scripts/model_forward_smoke.py) for safe forward checks and optional checkpoint/face-ID validation.

## Route elsewhere

- Inference commands, asset download steps, and end-user cartoon generation workflows -> `../portrait-inference/`
- Face detection, alignment, crop, and segmentation details -> `../preprocessing/`
- Dataset layout, preprocessing batches, CLI training, and long-running optimization -> `../data-and-training/`

## What this sub-skill covers

- `ResnetGenerator`, `Discriminator`, `HourGlass`, `HourGlassBlock`, `ResnetBlock`, `ResnetSoftAdaLINBlock`, `SoftAdaLIN`, `adaLIN`, and `LIN`
- Generator and discriminator return tuples: `(out, cam_logit, heatmap)`
- CAM logits and heatmap interpretation
- Tensor normalization range used by the repo
- Face-ID embedding path through `MobileFaceNet(512)`
- Training checkpoint contents and safe load checks
- Safe synthetic verification only; no downloads, no training, no destructive writes

## Practical commands

```bash
python scripts/model_forward_smoke.py --help
python scripts/model_forward_smoke.py --repo-root /path/to/photo2cartoon
python scripts/model_forward_smoke.py --repo-root /path/to/photo2cartoon --checkpoint /path/to/checkpoint.pt --face-model /path/to/model_mobilefacenet.pth
```
