---
name: model-architecture
description: "Understand and safely smoke-test U-2-Net model variants, side
  outputs, builders, and checkpoint-loading decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Architecture

Use this sub-skill when the task is to choose, instantiate, smoke-test, or diagnose U-2-Net model architectures. It covers the original `U2NET` and `U2NETP` classes, the refactored `U2NET_full()` and `U2NET_lite()` builders, seven-output forward semantics, and safe checkpoint/device loading decisions.

## Route elsewhere

- Full image-to-mask saliency or human-segmentation inference belongs to `salient-object-inference`.
- Portrait preprocessing, face crops, portrait prediction, and compositing belong to `portrait-workflows`.
- Dataset transforms, training layout, loss wiring, or long training runs belong to `data-and-training`.

## Quick operating facts

- U-2-Net is a script-style PyTorch repository, not an installable package with distribution metadata. Architecture checks against a local checkout should pass that checkout explicitly with `--repo-root`.
- Original models: `model.U2NET(in_ch=3, out_ch=1)` and `model.U2NETP(in_ch=3, out_ch=1)`.
- Refactored builders: `model.u2net_refactor.U2NET_full()` and `model.u2net_refactor.U2NET_lite()`.
- A 3-channel input tensor shaped `(N, 3, H, W)` produces seven sigmoid probability maps. For `out_ch=1`, each output is shaped `(N, 1, H, W)`. The first output is the fused prediction; the remaining six are side outputs.
- Prefer `U2NETP(3, 1)` for quick CPU smoke tests. Use `U2NET(3, 1)` for official full-size, human-segmentation, and portrait checkpoints unless a checkpoint explicitly targets `U2NETP`.

## References and scripts

- [API reference](references/api-reference.md): exact constructors, forward-output semantics, and safe checkpoint-loading snippets.
- [Model overview](references/model-overview.md): RSU/REBNCONV building-block summary and architecture selection guidance.
- [Troubleshooting](references/troubleshooting.md): wrong checkpoint, missing dependencies, CUDA confusion, deprecated upsample warnings, and output-shape surprises.
- [`scripts/smoke_architecture.py`](scripts/smoke_architecture.py): run this to verify imports and a tiny forward pass without pretrained weights.

## Safe architecture smoke test

```bash
python scripts/smoke_architecture.py \
  --model u2netp \
  --height 64 \
  --width 64 \
  --device cpu
```

The command prints JSON with the selected device, input shape, output count, and output tensor shapes. Request `--device cuda` only when the local PyTorch build reports CUDA as available; otherwise the helper fails clearly instead of silently falling back.

## Decision checklist

1. Need only a fast structural check? Use `--model u2netp --device cpu`.
2. Need compatibility with `u2net.pth`, human segmentation, or portrait weights? Instantiate `U2NET(3, 1)` unless evidence says the checkpoint targets `U2NETP`.
3. Seeing checkpoint mismatches? Check architecture variant, `out_ch`, original-vs-refactor implementation, and CPU/CUDA `map_location` before changing `strict` loading.
4. Seeing unexpected output handling? Remember: output 0 is fused; outputs 1-6 are side predictions, all already passed through sigmoid in the bundled model implementations.
