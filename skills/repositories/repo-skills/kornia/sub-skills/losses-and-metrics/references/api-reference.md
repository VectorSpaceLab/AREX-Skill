# Loss and metric API reference

This guide describes the public `kornia.losses` and `kornia.metrics` surfaces
covered by this sub-skill. The package is PyTorch-first and the listed losses
and metrics use the base installation; this workflow does not require ONNX,
Transformers, Diffusers, Ivy, or pretrained model downloads.

## Fast selection

| Need | Prefer | Prediction/target contract | Output direction |
|---|---|---|---|
| Photometric reconstruction | `ssim_loss`, `MS_SSIMLoss`, `psnr_loss` | Same-shaped floating images | Losses are lower-is-better |
| Smooth image/depth regularization | `total_variation`, `inverse_depth_smoothness_loss` | Image-like floating tensors; depth and image share `B,H,W` | Lower-is-smoother |
| Multiclass region overlap | `dice_loss`, `tversky_loss` | Logits `(B,C,H,W)`, labels `(B,H,W)` | Lower-is-better |
| Class imbalance | `focal_loss` or `FocalLoss` | Logits `(B,C,*)`, labels `(B,*)` | Lower-is-better |
| Binary logits | `binary_focal_loss_with_logits` | Logits and floating 0/1 targets with the same shape | Lower-is-better |
| IoU-aligned segmentation objective | `lovasz_hinge_loss` or `lovasz_softmax_loss` | Binary `(B,1,H,W)` or multiclass `(B,C,H,W)` logits plus `(B,H,W)` labels | Lower-is-better |
| Boundary mismatch | `HausdorffERLoss` / `HausdorffERLoss3D` | Prediction channels plus a single-channel integer label map | Lower-is-better |
| Segmentation report | `confusion_matrix`, `mean_iou` | Discrete integer predictions and labels with identical shape | Higher-is-better |
| Stereo report | disparity error functions | Same-shaped continuous disparity maps and optional valid mask | Lower-is-better |
| Pose report | `angle_error_*`, `pose_errors`, `auc_from_errors` | Rotation/translation/pose tensors in the documented forms | Lower error / higher AUC |

## Image and reconstruction losses

Import through `kornia.losses` or `import kornia as K`.

### SSIM and MS-SSIM

```python
K.losses.ssim_loss(
    img1, img2, window_size, max_val=1.0, eps=1e-12,
    reduction="mean", padding="same"
)
K.metrics.ssim(img1, img2, window_size, max_val=1.0, eps=1e-12, padding="same")
```

- Inputs are floating tensors with identical `(B,C,H,W)` shape.
- `ssim_loss` returns the structural dissimilarity `(1 - SSIM) / 2`; use it
  for optimization. With `reduction="none"`, its output is an SSIM-derived
  map with the same shape for `padding="same"`.
- `metrics.ssim` returns the local SSIM map with `(B,C,H,W)` shape for
  `padding="same"`. `padding="valid"` crops the border and therefore returns
  smaller spatial dimensions.
- `max_val` is the image dynamic range, not a normalization switch. Use a
  floating value such as `1.0` for `[0,1]` images or `255.0` for `[0,255]`
  values; convert the images consistently before choosing it.
- `SSIMLoss(window_size, max_val=1.0, eps=1e-12, reduction="mean", padding="same")`
  and `SSIM(window_size, max_val=1.0, eps=1e-12, padding="same")` wrap the
  corresponding functions.
- `MS_SSIMLoss` combines multiscale SSIM and a Gaussian-weighted L1 term. Its
  constructor includes `sigmas`, `data_range`, `K`, `alpha`, `compensation`,
  and `reduction`. Inputs are same-shaped `(B,C,H,W)` images. Move the module
  to the input device and dtype when using a non-default backend or precision.

For 3D image volumes use `ssim3d_loss`, `SSIM3DLoss`, `metrics.ssim3d`, or
`metrics.SSIM3D` with same-shaped `(B,C,D,H,W)` tensors. The same
`max_val`, `eps`, `padding`, and reduction principles apply.

### PSNR

```python
K.metrics.psnr(image, target, max_val)
K.losses.psnr_loss(image, target, max_val)
K.losses.PSNRLoss(max_val)(image, target)
```

`image` and `target` can have any identical shape. `metrics.psnr` returns a
scalar where larger is better. `psnr_loss` is exactly negative PSNR, so it is
an optimization objective whose values become more negative as reconstruction
quality improves. A zero MSE produces positive infinity; avoid using that value
as a finite smoke-test assertion.

### Regularization and robust residual losses

- `total_variation(img, reduction="sum")` accepts `(*,H,W)` and returns one
  value per leading element, not necessarily a scalar. Only `"sum"` and
  `"mean"` are valid reductions; `mean` is more resolution-invariant.
- `inverse_depth_smoothness_loss(idepth, image)` expects `(B,Cd,H,W)` and
  `(B,Ci,H,W)` tensors with the same spatial shape, device, and dtype. The
  image gradients attenuate inverse-depth gradients near image edges.
- `charbonnier_loss`, `welsch_loss`, `cauchy_loss`, and
  `geman_mcclure_loss` accept same-shaped floating tensors and support
  elementwise (`"none"`), mean, and sum variants. These are robust residual
  penalties; they do not perform image range conversion.
- `js_div_loss_2d` and `kl_div_loss_2d` expect `(B,N,H,W)` heatmaps and a
  reduction. Supply valid nonnegative distributions appropriate for the
  divergence rather than raw unconstrained logits.

## Segmentation losses

### Multiclass logits and class-index labels

The standard contract is `pred/logits: (B,C,H,W)` and `target: (B,H,W)` with
integer labels in `[0,C)`. The losses below apply softmax internally; pass
logits, not already-softmaxed probabilities.

- `dice_loss(pred, target, average="micro", eps=1e-8, weight=None,
  ignore_index=-100)` computes `1 - Dice`. `"micro"` aggregates classes
  before the score; `"macro"` computes class-wise scores and averages them.
  It returns a scalar after its internal mean over the batch.
- `tversky_loss(pred, target, alpha, beta, eps=1e-8,
  ignore_index=-100)` returns a scalar. `alpha` increases the false-positive
  penalty and `beta` increases the false-negative penalty. `alpha=beta=0.5`
  is the Dice-like setting.
- `focal_loss(pred, target, alpha, gamma=2.0, reduction="none",
  weight=None, ignore_index=-100)` supports `(B,C,*)` logits and `(B,*)`
  labels. `reduction="none"` preserves the class dimension and spatial axes;
  `mean` and `sum` return scalars.
- `lovasz_softmax_loss(pred, target, weight=None)` expects `C > 1` and returns
  a scalar. It is an IoU surrogate and applies softmax internally.
- `DiceLoss`, `TverskyLoss`, `FocalLoss`, and `LovaszSoftmaxLoss` are module
  wrappers for the same contracts.

Use `kornia.losses.one_hot(labels, num_classes, device, dtype)` only when a
one-hot tensor is explicitly needed. It accepts `int64` labels of shape
`(B,*)` and returns `(B,C,*)` in the requested floating dtype. It adds a small
`eps` floor to every output entry, so it is not a strict zero/one encoding.

### Binary losses

- `binary_focal_loss_with_logits(pred, target, alpha=0.25, gamma=2.0,
  reduction="none", pos_weight=None, weight=None, ignore_index=-100)` expects
  logits and target tensors with exactly the same shape `(B,C,*)`. Targets are
  floating 0/1 values (or ignored values when configured). It applies sigmoid
  logic internally; do not sigmoid first.
- `lovasz_hinge_loss(pred, target)` expects binary logits `(B,1,H,W)` and
  binary class-index labels `(B,H,W)`. For multiclass labels use Lovasz
  Softmax instead.
- `HausdorffERLoss` expects prediction `(B,C,H,W)` and a single-channel long
  target `(B,1,H,W)` whose values select a class. `HausdorffERLoss3D` uses
  `(B,C,D,H,W)` and `(B,1,D,H,W)`. These are erosion-based differentiable
  approximations, configured with `alpha`, `k`, and `reduction`.

## Metrics and monitoring

### Classification and segmentation

- `accuracy(pred, target, topk=(1,))` consumes classifier outputs and returns a
  list of accuracy tensors, one per requested `k`.
- `confusion_matrix(pred, target, num_classes, normalized=False)` accepts
  same-shaped integer class-index tensors `(B,*)` and returns float32
  `(B,K,K)`. The implementation uses a batched bincount; predictions and
  labels must be on the same device.
- `mean_iou(pred, target, num_classes, eps=1e-6)` returns per-image,
  per-class IoU with shape `(B,K)`, not a single scalar mean. Despite a
  docstring phrase describing one-hot targets, the tested/runtime contract is
  same-shaped integer class-index tensors. Convert one-hot labels and model
  logits to class indices before calling it, for example:

```python
pred_index = logits.detach().argmax(dim=1).to(torch.int64)
target_index = one_hot_target.argmax(dim=1).to(torch.int64)
iou_by_class = K.metrics.mean_iou(pred_index, target_index, num_classes=C)
```

- `mean_iou_bbox(boxes_1, boxes_2, box_format="xyxy")` evaluates the
  Cartesian product of two box sets and returns `(B1,B2)`; supported formats
  are `xyxy`, `xywh`, and `cxcywh`.
- `mean_average_precision(...)` evaluates detection lists and is separate from
  the segmentation `mean_iou` contract.

### Image quality

`metrics.ssim`/`SSIM` return a local map; `metrics.psnr` returns a scalar. These
are evaluation metrics, so detach model outputs when no metric gradient is
needed. Use the same `max_val` and image range as the matching loss.

### Disparity and flow

- `mean_absolute_disparity_error`, `root_mean_squared_disparity_error`, and
  `mean_bad_pixel_error` accept same-shaped continuous disparity tensors and an
  optional boolean or numeric `valid_mask` broadcastable to that shape.
- All three support `reduction="mean"`, `"sum"`, or `"none"`. For `none`,
  invalid locations are zeroed. An empty valid mask yields `NaN` for mean
  reduction; detect this explicitly rather than silently logging it.
- `aepe(input, target, reduction="mean")` evaluates endpoint error for the
  final vector dimension of size two and returns a scalar or an error map.

### Pose and error AUC

- `angle_error_mat(R1,R2)` accepts `(*,3,3)` rotations and returns degrees
  with shape `(*)`.
- `angle_error_vec(v1,v2)` accepts `(*,3)` vectors and returns degrees with
  shape `(*)`.
- `translation_ate(t,t_gt)` measures metric Euclidean translation error for
  `(*,3)` inputs. An unbatched `(3,)` input returns `(1,)`.
- `pose_errors(P,P_gt,fold_translation=True)` accepts `(3,4)`, `(4,4)`, or
  batched pose matrices and returns `R_err`, `t_err`, and `max_err` tensors.
  Folding maps translation direction error to `[0,90]` degrees to absorb the
  sign ambiguity common to essential-matrix translations.
- `auc_from_errors(errors, thresholds=(1,3,5,10))` accepts nonnegative error
  tensors and returns a Python dictionary of percentage AUCs. Thresholds use
  the same units as the errors. NaN errors propagate to NaN AUC values.

These angular metrics are undefined for zero vectors and have infinite/NaN
mathematical gradients exactly at 0 or 180 degrees. Use them for evaluation and
avoid backpropagating through singular configurations.

### Running averages

`AverageMeter` stores `val`, weighted `sum`, `count`, and a running `avg`.
Call `update(value, n=batch_size)` so batch-level values are weighted by the
number of represented examples; call `reset()` at an epoch boundary. The
`avg` property converts scalar tensors to a Python float.
