---
name: pretraining-and-adaptation
description: "Routes vit-pytorch loss wrappers, self-supervised pretraining
  helpers, distillation, and adaptation or fine-tuning flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pretraining-and-adaptation

Use this sub-skill when the user asks how to build or smoke-test vit-pytorch
loss-based wrappers, self-supervised learners, distillation flows, or adaptation
heads. The goal is to route to the right wrapper, identify expected inputs and
outputs, and surface version/dependency pitfalls before a user starts a long
training run.

## Read first

- Read [references/workflows.md](references/workflows.md) for wrapper roles,
  tiny construction patterns, expected input/output shapes, and which helpers
  return logits versus scalar losses.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a
  wrapper fails during construction, hook registration, augmentation, optional
  dependency import, checkpoint loading, or the first loss backward pass.
- Run [scripts/smoke_pretraining_wrappers.py](scripts/smoke_pretraining_wrappers.py)
  to check the installed package with tiny CPU random tensors. The helper
  reports `verified`, `version_fragile`, `dependency_gap`, and
  `unexpected_failure` statuses.

## Route here for

- `DistillableViT`, `DistillableT2TViT`, `DistillableEfficientViT`, and
  `DistillWrapper` one-step teacher/student distillation.
- Masked-image or masked-position pretraining: `MAE`, `SimMIM`, `MPP`, and
  `MP3`.
- Self-supervised crop/view learners: `Dino`, `EsViTTrainer`, and `LeJEPA`.
- Adaptation/fine-tuning helpers: Learnable Memory ViT `Adapter`, VAT,
  SigLIP-VAT, optional VAAT, WWT, and `vit_with_decorr.ViT`.
- Questions like “does this wrapper still work after upgrading?”, “can I run a
  one-step loss check on random tensors?”, and “what dependencies do I need for
  this adaptation flow?”

## Do not route here for

- Plain image backbone selection with no pretraining/adaptation wrapper; use
  [../image-architectures/SKILL.md](../image-architectures/SKILL.md).
- Attention-map or embedding inspection without a loss/training objective; use
  [../introspection-and-customization/SKILL.md](../introspection-and-customization/SKILL.md).
- General variable-resolution, N-D, or video routing unless the wrapper itself
  depends on the shape family, such as VAT/VAAT action conditioning; use
  [../variable-shapes-video/SKILL.md](../variable-shapes-video/SKILL.md) for
  pure shape/model-family questions.

## Current compatibility gates

Treat these as live caveats for this generated snapshot until the bundled smoke
helper proves otherwise for the installed version:

- `MAE` and `SimMIM` are intended to return scalar reconstruction losses, but
  tiny current-package smokes with base `ViT` reproduce a positional-embedding
  shape mismatch. Do not promise they work after an upgrade without rerunning
  the helper.
- `MPP` is intended to return a scalar masked patch prediction loss, but the
  current base-`ViT` usage is token-shape fragile around class-token and patch
  embedding expectations.
- `MP3`, `DistillWrapper`, `Dino`, `EsViTTrainer`, Learnable Memory `Adapter`,
  `LeJEPA`, VAT, SigLIP-VAT, WWT, and `vit_with_decorr.ViT` have tiny CPU smoke
  patterns in the bundled helper. Still rerun the helper in the user’s runtime,
  because optional dependencies and installed versions can differ.

## Fast workflow

1. Identify the user’s requested wrapper and whether they need a scalar loss,
   logits, action predictions, or an adapter head.
2. Read [references/workflows.md](references/workflows.md) for the wrapper’s
   construction pattern and expected tensors.
3. Run a bounded check before full training:

   ```bash
   python sub-skills/pretraining-and-adaptation/scripts/smoke_pretraining_wrappers.py
   ```

   Add `--json` for machine-readable output, or `--case dino --case distill`
   for a narrow check.
4. If any result is `version_fragile`, explain the exact pitfall and avoid
   presenting that wrapper as verified. If any result is `dependency_gap`, name
   the missing optional package instead of starting a full training script.
5. For long training, downloads, pretrained checkpoint loading, W&B/Accelerate,
   or real datasets, keep the one-step smoke separate from the heavyweight
   recipe and list the extra prerequisites explicitly.

## Output expectations by wrapper family

- Distillation: `DistillWrapper(img, labels)` returns a finite scalar loss;
  the distillable student can be converted back with `.to_vit()`.
- MAE/SimMIM/MPP/MP3: intended API returns a finite scalar loss and supports
  `loss.backward()`, but MAE/SimMIM/MPP require current-version compatibility
  checks before use.
- DINO/EsViT/LeJEPA: constructors attach/hook a hidden layer, run augment/crop
  logic, and `forward(images)` returns a finite scalar self-supervised loss.
  DINO and EsViT also require `update_moving_average()` after optimizer steps.
- Learnable Memory ViT: `Adapter(vit=..., num_classes=...)` freezes the supplied
  module-specific ViT and returns task logits.
- VAT/SigLIP-VAT/VAAT: with `actions=...`, return an L1 action-prediction loss;
  without actions, return predicted action chunks. Prefer explicit view/time
  dimensions for smoke inputs.
- WWT: returns class logits, and may also return token logits, task-head outputs,
  or a SigReg loss depending on constructor flags.
- `vit_with_decorr.ViT`: returns `(logits, decorr_aux_loss)`; train with ordinary
  task loss plus a weighted decorrelation auxiliary term.
