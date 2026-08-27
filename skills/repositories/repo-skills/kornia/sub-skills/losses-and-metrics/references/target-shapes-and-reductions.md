# Target shapes, encodings, and reductions

Make the tensor contract explicit before selecting an operation. Kornia checks
rank, shape, device, and sometimes dtype at runtime; PyTorch broadcasting is not
a substitute for the documented shape.

## Shape matrix

| Family | Prediction/input | Target/reference | Typical output |
|---|---|---|---|
| 2D SSIM loss/metric | `(B,C,H,W)` float | Same shape float | SSIM map `(B,C,H,W)` or loss scalar/map |
| 3D SSIM loss/metric | `(B,C,D,H,W)` float | Same shape float | SSIM map or loss scalar/map |
| PSNR loss/metric | Any shape float | Same shape float | Scalar |
| Total variation | `(*,H,W)` float/int | None | `*` values; reduction does not remove leading axes |
| Inverse-depth smoothness | `(B,Cd,H,W)` float | Image `(B,Ci,H,W)` float | Scalar |
| Robust residual loss | Any shape float | Same shape and device | Same shape, scalar for mean/sum |
| Multiclass Dice/Focal/Tversky | Logits `(B,C,...)` float | Labels `(B,...)` `int64` | Usually scalar; Focal `none` preserves class axis |
| Binary focal with logits | Logits `(B,C,...)` float | Same shape, float 0/1 | Same shape or scalar |
| Lovasz hinge | Logits `(B,1,H,W)` float | Labels `(B,H,W)` binary | Scalar |
| Lovasz softmax | Logits `(B,C,H,W)` float, `C>1` | Labels `(B,H,W)` | Scalar |
| Hausdorff 2D | `(B,C,H,W)` float | `(B,1,H,W)` long class map | Scalar/map per reduction |
| Hausdorff 3D | `(B,C,D,H,W)` float | `(B,1,D,H,W)` long class map | Scalar/map per reduction |
| Confusion matrix | `(B,*)` long indices | Same shape long indices | `(B,K,K)` float32 |
| Mean IoU | `(B,*)` long indices | Same shape long indices | `(B,K)` float |
| Disparity metrics | Any same-shaped float maps | Same shape float + broadcastable mask | Scalar or same-shaped map |
| Rotation angle | `(*,3,3)` float | Same shape | `(*)` degrees |
| Vector angle | `(*,3)` float | Same shape | `(*)` degrees |
| Translation ATE | `(*,3)` float | Same shape | `(*)`; unbatched input returns `(1,)` |
| Pose errors | `(3,4)`, `(4,4)`, or batched | Same shape | Dict of `(B,)` tensors |

Here `B` is batch size, `C` is class/channel count, and `*` denotes arbitrary
leading or spatial dimensions permitted by that API. Do not add a channel axis
to a class-index label unless the specific operation asks for one.

## Segmentation target encoding

### Multiclass softmax losses

For `dice_loss`, `tversky_loss`, `focal_loss`, and `lovasz_softmax_loss`:

```python
logits.shape == (B, C, H, W)
target.shape == (B, H, W)
target.dtype == torch.int64
target.min() >= 0
target.max() < C
```

Pass raw logits. These implementations normalize class scores internally. A
one-hot `(B,C,H,W)` target is not the standard target contract for these
functions. If labels are one-hot, convert them once with
`target = one_hot_target.argmax(dim=1).to(torch.int64)`.

`DiceLoss` and `TverskyLoss` return a scalar. `FocalLoss(reduction="none")`
returns `(B,C,H,W)` because its implementation retains the class contribution;
`mean` and `sum` return scalars. `ignore_index` removes selected label
locations for Dice, Tversky, and Focal; keep ignored labels out of any metric
unless you mask them yourself.

### Binary logits

For `binary_focal_loss_with_logits`, `pred` and `target` must have the exact
same shape, for example `(B,1,H,W)` or `(B,C,H,W)`. The target is floating
0/1 data (with an optional ignored value), and the prediction is a raw logit.
For `lovasz_hinge_loss`, use one logit channel `(B,1,H,W)` and a class-index
binary target `(B,H,W)`.

### Hausdorff labels

Hausdorff erosion losses use a **single** target channel, not one-hot labels:
`(B,1,H,W)` for 2D or `(B,1,D,H,W)` for 3D. The target is `torch.long` and
contains class indices. The prediction has one floating channel per class.
The loss performs the per-class target comparison internally.

## Metric encoding

`confusion_matrix` and `mean_iou` operate on discrete class indices, not logits,
probabilities, or one-hot channel tensors:

```python
pred_index = logits.detach().argmax(dim=1).to(torch.int64)  # (B,H,W)
target_index = target_one_hot.argmax(dim=1).to(torch.int64)  # (B,H,W), if needed
assert pred_index.shape == target_index.shape
```

The public docstring for `mean_iou` uses wording about one-hot targets, but the
runtime/tests require same-shaped integer tensors and the confusion matrix
implementation uses those values as class indices. Treat this as an API
compatibility detail and convert one-hot inputs explicitly.

`mean_iou` returns `(B,K)` per-class IoUs. If a scalar score is needed, reduce
it deliberately, for example `iou.mean()` or a masked class mean; do not assume
that the function itself returns a global mean.

## Image ranges and dynamic range

SSIM and PSNR constants depend on `max_val`:

- For tensors normalized to `[0,1]`, pass `max_val=1.0`.
- For tensors in `[0,255]`, pass `max_val=255.0`.
- For another range, pass the actual peak value and ensure both tensors use
  that same scale.

`ssim` checks that `max_val` is a Python float in the current API, so prefer
`1.0` rather than integer `1`. `max_val` does not clamp or normalize the
inputs. Use the image-processing workflow to perform conversions, then use the
matching dynamic range here.

## Reduction semantics

| Reduction | Meaning | Shape consequence |
|---|---|---|
| `"none"` | Preserve local/class/sample contributions | Usually input-like or class-aware map |
| `"mean"` | Arithmetic mean of the implementation's unreduced values | Usually scalar |
| `"sum"` | Sum of the implementation's unreduced values | Usually scalar |

Check the individual function when composing objectives:

- `ssim_loss` and the SSIM family preserve an image-like map with `none` and
  reduce it over all output elements for `mean`/`sum`.
- `focal_loss` with `none` keeps `(B,C,...)`, while Dice and Tversky perform
  their own batch/class averaging and return a scalar.
- Robust residual functions preserve the residual shape for `none`.
- `total_variation` always reduces only the final two spatial axes, so the
  leading dimensions remain. Its default is `sum`, unlike many training
  losses.
- Disparity metrics with a `valid_mask` reduce only selected values for
  `mean`/`sum`; `none` returns a map with invalid positions set to zero. A
  mask selecting no pixels yields `NaN` for mean and zero for sum.

When adding losses, make each term scalar first unless per-pixel weighting is
intentional:

```python
loss = dice_loss(logits, labels) + 0.1 * charbonnier_loss(pred, target, reduction="mean")
loss.backward()
```

Do not call `.backward()` on a non-scalar `reduction="none"` result without
providing an explicit gradient or reducing it yourself.
