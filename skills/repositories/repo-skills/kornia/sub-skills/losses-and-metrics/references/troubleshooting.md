# Loss and metric troubleshooting

Use the smallest failing tensor pair first. Check shape, dtype, device, range,
and finiteness before changing the loss formula.

## Logits versus probabilities

**Symptom:** Dice/Focal/Tversky/Lovasz produces a poor or flat training signal,
or binary focal values disagree with a BCE reference.

**Fix:** Pass raw logits to `dice_loss`, `tversky_loss`, `focal_loss`,
`binary_focal_loss_with_logits`, and Lovasz losses. Multiclass Dice/Focal/
Tversky/Lovasz-Softmax apply softmax internally; binary focal applies sigmoid
logic internally. Applying softmax or sigmoid first changes the intended
numerics and can double-normalize the prediction.

Use probabilities only where the API asks for them, such as distribution
losses (`js_div_loss_2d` and `kl_div_loss_2d`) or a custom post-processing
step. Metrics that need discrete segmentation labels require `argmax` first.

## Class-index versus one-hot targets

**Symptom:** A segmentation loss reports a rank/channel mismatch, or
`mean_iou` returns an unexpected shape or fails in `bincount`.

**Fix:** For multiclass softmax losses use `logits: (B,C,H,W)` with
`target: (B,H,W)` `torch.int64` indices in `[0,C)`. For metric evaluation use
`pred_index` and `target_index` with identical shape and `torch.int64` dtype.
Convert a one-hot `(B,C,H,W)` tensor with `argmax(dim=1)` before calling
`mean_iou` or `confusion_matrix`.

Binary focal is the exception: its target has the same shape as its logits and
contains floating 0/1 values. Hausdorff losses use a single-channel long class
map `(B,1,H,W)` or `(B,1,D,H,W)`, not one-hot labels.

## Channel, batch, and spatial shape errors

- Image SSIM requires both inputs to be exactly `(B,C,H,W)` and same-shaped;
  use `ssim3d` for `(B,C,D,H,W)` volumes.
- Dice/Focal/Tversky need the prediction class axis at dimension 1. A target
  shaped `(B,1,H,W)` is not the normal class-index target for these APIs;
  squeeze the label channel only when it is a singleton encoding of `(B,H,W)`.
- Lovasz hinge requires exactly one prediction channel. Lovasz Softmax requires
  more than one.
- Inverse-depth smoothness requires depth and image to share `B,H,W`, device,
  and dtype. It does not require the same channel count.
- Disparity `valid_mask` can have fewer dimensions, but it must broadcast to the
  complete input shape. If it selects zero pixels, handle the documented NaN
  mean result.
- Pose functions reject accidental broadcasting. Make both pose batches have
  the same shape before calling them.

Print `tensor.shape`, `tensor.dtype`, `tensor.device`, and
`tensor.requires_grad` for every argument before debugging deeper.

## Reduction and backward errors

**Symptom:** `RuntimeError: grad can be implicitly created only for scalar
outputs`, or a logging value has an unexpected number of elements.

**Fix:** Use `reduction="mean"` for the usual scalar training objective, or
reduce a `reduction="none"` result explicitly:

```python
per_pixel = K.losses.charbonnier_loss(pred, target, reduction="none")
loss = per_pixel.mean()
loss.backward()
```

Remember that `total_variation` retains leading dimensions, Dice/Tversky
return a scalar after their own averaging, and `mean_iou` returns `(B,K)` even
though its name says “mean”. Choose a class/batch reduction deliberately for
logging and checkpoint selection.

## `max_val`, range, and infinity

**Symptom:** SSIM/PSNR values are implausible, PSNR loss has the wrong sign, or
PSNR is infinite.

**Fix:** `max_val` must match the numerical peak of both images. Use `1.0` for
`[0,1]`, `255.0` for byte-scale floating images, and the corresponding actual
peak for another range. `max_val` does not rescale or clamp inputs. The
current SSIM metric/loss API expects a Python float, so use `1.0`, not `1`.

SSIM metric is higher-is-better, while `ssim_loss=(1-SSIM)/2` is lower-is-
better. PSNR metric is higher-is-better, while `psnr_loss=-PSNR` is
lower-is-better. Identical inputs have zero MSE and therefore infinite PSNR;
use a non-identical deterministic pair in finite-value smoke tests.

## Dtype and device mismatch

- Predictions and floating references must use compatible floating dtype and
  the same device. Inverse-depth smoothness explicitly requires matching
  dtype.
- Class labels for Dice/Focal/Tversky/Lovasz/mean IoU/confusion matrix should
  be `torch.int64`; do not cast them to the prediction's floating dtype.
- Class weights, `pos_weight`, and one-hot outputs must be on the prediction
  device. Create them with `device=pred.device` or move them before the call.
- CPU, CUDA, and MPS support is backend-specific. Let the model and every
  tensor move together; do not create a CPU target for a CUDA prediction.
- The package imports filters and geometry before other modules to avoid
  circular imports. Use the public `kornia` package imports rather than
  rearranging package internals.

## Half precision, linalg, and angular singularities

The package precision guide classifies `kornia.losses` and `kornia.metrics` as
partial (`⚠️`) for float16 and bfloat16: photometric/pixel operations are often
usable, while linalg-sensitive paths may fail or lose accuracy. For gradient
checks, pose metrics, difficult boundary cases, or unexpected NaN/Inf, rerun in
float32 or float64 before attributing the issue to the loss itself. CUDA half
precision is not proof that CPU half precision will behave the same way.

Pose-specific edge cases are mathematical, not just dtype problems:

- `angle_error_mat` and `angle_error_vec` use `acos`; gradients are singular
  at exactly 0 and 180 degrees.
- A zero-length vector has undefined angle and returns NaN.
- `pose_errors` propagates NaN translation errors for zero translations into
  `max_err` and `auc_from_errors`.
- `auc_from_errors` requires strictly positive thresholds and nonnegative
  errors; NaNs are intentionally propagated.

Use safe non-degenerate rotations/vectors for gradient checks and mask invalid
samples before computing aggregate reports.

## Metric versus loss confusion

**Symptom:** A metric is used in the optimizer and gradients are absent or
training is unstable.

**Fix:** Keep differentiable objectives in `kornia.losses`. Use SSIM/PSNR,
confusion matrix, mean IoU, disparity, pose, and accuracy metrics for detached
validation/reporting unless a specific differentiable use has been verified.
Discrete `argmax`, `bincount`, and IoU computations are evaluation operations,
not substitutes for a segmentation loss.

## Import and optional-dependency issues

The losses and metrics covered here use the base PyTorch-oriented installation.
A missing ONNX, Transformers, Diffusers, or Ivy extra should not block these
APIs. If importing the package fails, first verify that PyTorch and the base
Kornia dependencies are installed and that the import is not being shadowed by
an unrelated module named `kornia`. Do not trigger pretrained model downloads
while checking losses or metrics.
