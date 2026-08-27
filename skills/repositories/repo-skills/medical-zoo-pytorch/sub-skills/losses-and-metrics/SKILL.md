---
name: losses-and-metrics
description: "Operate MedicalZooPytorch loss and metric APIs for segmentation
  criteria, shape contracts, tuple returns, and safe smoke checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# losses-and-metrics

Use this sub-skill when the task is to select, instantiate, debug, or smoke-test MedicalZooPytorch loss objects exposed through `lib.losses3D`.

## Route first

- For exact constructor names, accepted shapes, return types, one-hot expansion, and criterion-selection rules, open [references/api-reference.md](references/api-reference.md).
- For assertion failures, unsupported loss names, singleton-batch 2D Dice quirks, device mismatches, or pixel-weight issues, open [references/troubleshooting.md](references/troubleshooting.md).
- For model creation, trainer wiring, writer updates, checkpoints, full training loops, and inference, hand off to the sibling route [segmentation-workflows](../segmentation-workflows/). Bring only the selected criterion and its return contract from this sub-skill.
- For how dataset loaders produce target tensors and labels, hand off to [data-loading-preprocessing](../data-loading-preprocessing/).

## Fast operating rules

1. Standard 3D semantic segmentation criteria expect logits shaped `[N, C, D, H, W]` and integer label targets shaped `[N, D, H, W]` unless the API reference says a raw PyTorch loss requires same-shaped targets.
2. Dice-family MedicalZoo losses expand class-index targets to one-hot internally and normalize logits internally. Match the loss `classes` argument to the model output channel count.
3. The built-in 3D trainer route expects `criterion(output, target)` to return `(loss_tensor, per_channel_dice_like)`. `DiceLoss`, `GeneralizedDiceLoss`, `BCEDiceLoss`, and `DiceLoss2D` satisfy that shape of contract; scalar-only losses require a trainer adaptation owned by `segmentation-workflows`.
4. `create_loss(name, ...)` is case-sensitive and does not expose every constructor option. Instantiate classes directly when class count, `skip_index_after`, tag coefficients, contrastive embeddings, or 2D Dice behavior matters.
5. Keep targets integer-valued and on the same device as logits. Move criterion modules that carry weight buffers to the target device before CUDA checks.

## Bundled smoke check

Run the bundled deterministic smoke check after making the MedicalZooPytorch package importable:

```bash
python sub-skills/losses-and-metrics/scripts/smoke_losses.py
python sub-skills/losses-and-metrics/scripts/smoke_losses.py --cuda
```

The script uses tiny synthetic tensors, validates tuple versus scalar return contracts, exercises representative factory/manual loss paths, and confirms unsupported factory names fail with guidance.
