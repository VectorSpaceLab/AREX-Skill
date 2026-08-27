---
name: losses-and-metrics
description: "Select and apply Kornia image, segmentation, depth, stereo, pose,
  and monitoring losses and metrics with correct tensor encodings, dynamic
  ranges, reductions, and gradient checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Losses and Metrics

Use this sub-skill when choosing a differentiable training objective or evaluating
image quality, segmentation, depth, disparity, pose, or classification outputs
with `kornia.losses` and `kornia.metrics`.

## Route

1. Identify whether the operation is a **loss** (optimized, usually
   differentiable with respect to predictions) or a **metric** (reported for
   evaluation; discrete metrics such as IoU are not training objectives).
2. Normalize the representation before calling the API: image range and
   `max_val`, logits versus probabilities, class-index versus one-hot targets,
   and tensor device/dtype must be explicit.
3. Confirm the batch/channel/spatial contract and choose the reduction required
   by the training loop. Preserve `reduction="none"` when a per-pixel map or
   per-sample weighting is needed.
4. Run a tiny finite-value and backward check on the chosen differentiable loss
   before integrating it into a larger model.

## Capability routing

- Image restoration and photometric supervision: SSIM, MS-SSIM, PSNR,
  total-variation, inverse-depth smoothness, and robust residual losses.
- Semantic segmentation: Dice, Focal, binary focal-with-logits, Tversky,
  Lovasz, one-hot conversion, and Hausdorff erosion losses.
- Evaluation and monitoring: SSIM/PSNR, confusion matrices, mean IoU,
  disparity errors, pose errors/AUC, endpoint error, accuracy, and
  `AverageMeter`.
- Route camera-model, homography, pose construction, or coordinate-frame setup
  to [geometry-vision](../geometry-vision/SKILL.md). Route image decoding,
  normalization, color conversion, and range conversion to
  [image-processing](../image-processing/SKILL.md).

## Common workflows

- Use a loss for optimization and a metric for reporting; do not substitute one for the other.
- Normalize predictions and targets before computing image-quality or segmentation losses.
- For segmentation, keep track of whether the downstream step expects probabilities, logits, class indices, or one-hot labels.
- For evaluation-only metrics, convert outputs into the documented class or tensor format before reporting.
- Run a tiny backward check on the chosen loss before adopting it in a larger model.

## Pitfalls

- A wrong `max_val` or image range can make SSIM/PSNR look reasonable while measuring the wrong scale.
- A mismatched reduction can hide per-pixel or per-sample failures.
- IoU and confusion-matrix style metrics often need a different target encoding than the loss used for training.

## Quick validation habits

- For training, start with a differentiable loss and only add metrics after the tensor contract is stable.
- For reporting, use metrics that match the target encoding instead of adapting the target encoding to a convenient metric.
- Check a single mini-batch with finite outputs before scaling the loss into a full loop.
- If a reduction or range looks suspicious, verify the output shape and max/min values before tuning the weights.
- For IoU-like metrics, confirm whether the target should be one-hot or class-indexed in the chosen route.
- For photometric losses, confirm the dynamic range before changing `max_val` or the reduction.
- When a metric fails, inspect the tensor contract before changing the metric formula.
- If you need per-pixel supervision, preserve `reduction="none"` until the weighting step.
- Use one tiny backward pass to confirm the chosen loss is actually differentiable for the selected tensor shapes.
- Keep the loss and metric routes separate when the user asks for both in one request.

## References and smoke check

- Read [API reference](references/api-reference.md) for the operation families
  and selection recipes.
- Read [target shapes and reductions](references/target-shapes-and-reductions.md)
  before passing labels, masks, or per-pixel outputs.
- Read [troubleshooting](references/troubleshooting.md) for range, dtype,
  device, precision, and gradient failures.
- Run [the deterministic smoke script](scripts/loss_metric_smoke.py) with
  `--device auto`, `--device cpu`, or `--device cuda` to validate a usable
  installation without model downloads.
