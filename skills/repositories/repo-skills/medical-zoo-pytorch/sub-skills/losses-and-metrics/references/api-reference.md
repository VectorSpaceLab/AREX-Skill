# MedicalZooPytorch loss and metric API reference

This reference covers the public operating surface of `lib.losses3D`. Make the MedicalZooPytorch package importable, then import losses with ordinary Python module imports such as:

```python
from lib.losses3D import create_loss, DiceLoss, GeneralizedDiceLoss, BCEDiceLoss
from lib.losses3D import WeightedCrossEntropyLoss, PixelWiseCrossEntropyLoss
from lib.losses3D import TagsAngularLoss, WeightedSmoothL1Loss, ContrastiveLoss, DiceLoss2D
from lib.losses3D.VAEloss import loss_vae
```

## Core shape conventions

| Data | Expected shape | Notes |
| --- | --- | --- |
| 3D segmentation logits | `[N, C, D, H, W]` float tensor | Most MedicalZoo criteria expect unnormalized model outputs and apply their own sigmoid or softmax where needed. |
| 3D segmentation targets | `[N, D, H, W]` integer tensor | Dice-family, weighted smooth L1, and tag-angular losses expand class indices to one-hot internally. Values should be in `0..C-1` unless an API explicitly supports `ignore_index`. |
| Already one-hot 3D targets | `[N, C, D, H, W]` | `expand_as_one_hot` returns 5D input unchanged, so dice-style losses can accept already-expanded targets if the channel count matches. |
| Cross-entropy targets | `[N, D, H, W]` integer tensor | Raw `CrossEntropyLoss` and `WeightedCrossEntropyLoss` consume class-index targets without one-hot expansion. |
| Pixel-wise weights | `[N, D, H, W]` float tensor | Required third argument for `PixelWiseCrossEntropyLoss.forward(input, target, weights)`. |
| Contrastive embeddings | `[N, E, D, H, W]` float tensor | `E` is embedding dimension; it is not the number of semantic classes. Target is an instance-id volume. |
| 2D Dice logits | usually `[N, C, H, W]` with `N > 1`, or `[C, H, W]` for singleton synthetic checks | `DiceLoss2D` has a singleton-batch quirk; see troubleshooting before using `N == 1` in a training loop. |
| 2D Dice targets | `[N, H, W]` integer tensor, or `[1, H, W]` when input is `[C, H, W]` | Converted to one-hot internally by `DiceLoss2D`. |

## Return-contract quick map

| API | Return from `forward`/call | Safe for unmodified 3D `Trainer`? | Notes |
| --- | --- | --- | --- |
| `DiceLoss` | `(loss_tensor, per_channel_dice_numpy)` | yes | `per_channel_dice_numpy` is a vector with one value per class/channel. |
| `GeneralizedDiceLoss` | `(loss_tensor, generalized_dice_numpy)` | structurally yes | The second item is a scalar generalized Dice value, not a per-channel vector. Writer code that assumes four channels needs adaptation. |
| `BCEDiceLoss` | `(loss_tensor, per_channel_dice_numpy)` | yes | Combines BCE-with-logits and `DiceLoss`; leave `beta=1` unless you have patched the implementation. |
| `DiceLoss2D` | `(loss_tensor, per_channel_dice_numpy)` | only in 2D segmentation route | Intended for 2D segmentation outputs; singleton batches need special care. |
| `WeightedCrossEntropyLoss` | scalar `loss_tensor` | no | Use in a custom loop or adapt trainer logging to scalar-only criteria. |
| `PixelWiseCrossEntropyLoss` | scalar `loss_tensor` | no | Requires `weights` argument in addition to `input` and `target`. |
| `TagsAngularLoss` | scalar `loss_tensor` | no | Multi-head/list contract; not a default semantic segmentation criterion. |
| `WeightedSmoothL1Loss` | scalar `loss_tensor` | no | Expands class-index target to one-hot before smooth-L1. |
| `ContrastiveLoss` | scalar `loss_tensor` | no | Instance embedding loss; instantiate directly, not via `create_loss`. |
| `loss_vae` | scalar `loss_tensor` | no | Auxiliary reconstruction + KL function, not in `create_loss`. |
| Raw `BCEWithLogitsLoss`, `MSELoss`, `SmoothL1Loss`, `L1Loss`, `CrossEntropyLoss` | scalar `loss_tensor` | no by default | PyTorch losses do not return per-channel dice. |

## Factory: `create_loss(name, weight=None, ignore_index=None, pos_weight=None)`

`create_loss` accepts case-sensitive names and raises `RuntimeError` with a supported-name list for any other value.

| Name | Returns | Shape and option notes |
| --- | --- | --- |
| `BCEWithLogitsLoss` | `torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)` | Raw PyTorch BCE: target must already be float and same shape as input. It does not one-hot expand `[N, D, H, W]` labels. |
| `BCEDiceLoss` | `BCEDiceLoss(alpha=1, beta=1)` | Defaults to `classes=4`; instantiate directly for other class counts. Returns tuple. |
| `CrossEntropyLoss` | `torch.nn.CrossEntropyLoss(weight=weight, ignore_index=ignore_index or -100)` | Standard scalar CE with class-index targets. |
| `WeightedCrossEntropyLoss` | `WeightedCrossEntropyLoss(ignore_index=ignore_index or -100)` | Computes dynamic class weights from the softmax input and returns scalar. |
| `PixelWiseCrossEntropyLoss` | `PixelWiseCrossEntropyLoss(class_weights=weight, ignore_index=ignore_index)` | `forward` still requires a per-voxel `weights` tensor. |
| `GeneralizedDiceLoss` | `GeneralizedDiceLoss(sigmoid_normalization=False)` | Defaults to `classes=4`; factory selects softmax normalization. Returns tuple with scalar generalized Dice side output. |
| `DiceLoss` | `DiceLoss(weight=weight, sigmoid_normalization=False)` | Defaults to `classes=4`; factory selects softmax normalization. Returns tuple with vector side output. |
| `TagsAngularLoss` | `TagsAngularLoss()` | Defaults to three tag heads and `classes=4`; direct construction is safer for custom heads/classes. |
| `MSELoss` | `torch.nn.MSELoss()` | Raw PyTorch scalar; input and target shapes must match. |
| `SmoothL1Loss` | `torch.nn.SmoothL1Loss()` | Raw PyTorch scalar; input and target shapes must match. |
| `L1Loss` | `torch.nn.L1Loss()` | Raw PyTorch scalar; input and target shapes must match. |
| `WeightedSmoothL1Loss` | `WeightedSmoothL1Loss()` | Defaults to `classes=4`; expands target to one-hot and returns scalar. |

Factory limitations to remember:

- It does not expose a `classes` argument. For non-4-class segmentation, direct constructors are usually required.
- It does not construct `ContrastiveLoss`, `DiceLoss2D`, or `loss_vae`; import and instantiate/call those directly.
- It returns scalar-only PyTorch losses for several names, so do not drop them into a trainer that unpacks `(loss, per_channel_score)` unless that trainer is adapted.

## Dice-family losses

### `DiceLoss(classes=4, skip_index_after=None, weight=None, sigmoid_normalization=True)`

- Converts class-index target labels to `[N, classes, D, H, W]` via `expand_as_one_hot(target.long(), classes)` unless the target is already 5D.
- Applies `Sigmoid()` by default. Pass `sigmoid_normalization=False` for `Softmax(dim=1)` behavior.
- Calls `compute_per_channel_dice`, then returns `(1 - mean(per_channel_dice), per_channel_dice_as_numpy)`.
- `skip_index_after=index` slices the expanded target channels to `target[:, :index, ...]` before comparing shapes. Use only when the model output channel count matches `index` and the label space has extra channels you intentionally drop.

### `GeneralizedDiceLoss(classes=4, sigmoid_normalization=True, skip_index_after=None, epsilon=1e-6)`

- Shares the same base flow as `DiceLoss`: one-hot target expansion, optional target channel slicing, internal normalization, and tuple return.
- Computes inverse-volume label weighting internally.
- The side output is a scalar generalized Dice value because the implementation sums intersections and denominators across classes before returning from `dice()`.

### `BCEDiceLoss(alpha=1, beta=1, classes=4)`

- Expands targets to one-hot, checks exact input/target shape match, then combines `alpha * BCEWithLogitsLoss(input, one_hot_target)` with a `DiceLoss(classes=classes)` value.
- Returns `(combined_loss_tensor, per_channel_dice_numpy)`.
- Constructor options exist, but the implementation multiplies `beta` against the returned Dice tuple. In unpatched code, keep `beta=1` to avoid tuple-multiplication failures.

### `DiceLoss2D(classes, epsilon=1e-5, sigmoid_normalization=True)`

- Applies sigmoid by default or softmax with `sigmoid_normalization=False`.
- Expands 2D label targets to one-hot and returns `(mean(1 - per_channel_dice), per_channel_dice_numpy)`.
- It is for 2D segmentation branches, not volumetric `[N, C, D, H, W]` tensors.
- For singleton-batch smoke checks, use input `[C, H, W]` and target `[1, H, W]`. For data-loader training, verify the exact batch behavior with `smoke_losses.py` or a synthetic batch before long runs.

## Cross-entropy family

### `WeightedCrossEntropyLoss(ignore_index=-1)`

- Input: logits `[N, C, D, H, W]`.
- Target: class-index labels `[N, D, H, W]`.
- Computes class weights dynamically as `(1 - p).sum / p.sum` from softmax probabilities and calls `torch.nn.functional.cross_entropy`.
- Direct construction defaults to `ignore_index=-1`; factory construction defaults to `-100` when not supplied.

### `PixelWiseCrossEntropyLoss(class_weights=None, ignore_index=None)`

- Input: logits `[N, C, D, H, W]`.
- Target: labels `[N, D, H, W]`.
- `weights`: required per-voxel weights `[N, D, H, W]` in the forward call.
- Converts targets to one-hot, broadcasts `weights` to input shape, multiplies optional class weights, then returns the mean negative log likelihood.
- Not a drop-in replacement for `criterion(output, target)` because `weights` is mandatory.

## Smooth L1, angular, and contrastive losses

### `WeightedSmoothL1Loss(threshold=0, initial_weight=0.1, apply_below_threshold=True, classes=4)`

- Expands integer targets to one-hot with `classes` channels.
- Computes elementwise smooth-L1 with `reduction="none"`, down/up-weights elements selected by the threshold mask, and returns `mean()`.
- Use `threshold=0.5` if you intend to distinguish one-hot zeros from ones; the default threshold of `0` selects no one-hot zeros with the default `apply_below_threshold=True`.

### `TagsAngularLoss(tags_coefficients=[1.0, 0.8, 0.5], classes=4)`

- `inputs` must be a list of tag-head tensors. With one input head, a single target tensor is wrapped as a list; with multiple heads, pass a target list of the same length.
- Each input head must match the one-hot-expanded target shape `[N, classes, D, H, W]`.
- Returns a scalar weighted sum of squared angular losses.

### `ContrastiveLoss(delta_var=0.5, delta_dist=1.5, norm='fro', alpha=1.0, beta=1.0, gamma=0.001)`

- Input: embeddings `[N, E, D, H, W]`.
- Target: instance labels `[N, D, H, W]`.
- The implementation sets the one-hot class count to `torch.unique(target).size(0)`, so labels must be contiguous integers from `0` through `num_instances-1`. Remap sparse instance ids before calling it.
- Returns a scalar mean discriminative embedding loss.

## Helpers and wrappers

| API | Purpose | Contract |
| --- | --- | --- |
| `expand_as_one_hot(input, C, ignore_index=None)` | Convert `[N, D, H, W]` label tensor to `[N, C, D, H, W]`; return 5D input unchanged. | `input` must contain valid scatter indices except positions equal to `ignore_index`. |
| `compute_per_channel_dice(input, target, epsilon=1e-6, weight=None)` | Compute per-channel Dice from already-normalized probabilities and one-hot target. | `input` and `target` shapes must match; returns a tensor with channel dimension length. |
| `flatten(tensor)` | Move channels first and flatten spatial/batch dimensions. | `[N, C, ...] -> [C, N * ...]`. |
| `SkipLastTargetChannelWrapper(loss, squeeze_channel=False)` | Drop the last target channel before forwarding to another loss. | Target must have more than one channel; returns whatever the wrapped loss returns. |
| `_MaskingLossWrapper(loss, ignore_index)` | Zero-out positions where `target == ignore_index` before forwarding to another loss. | Private-style helper; returns whatever the wrapped loss returns. |
| `loss_vae(recon_x, x, mu, logvar, type='BCE', h1=0.1, h2=0.1)` | Auxiliary reconstruction + KL loss. | Requires `recon_x.size() == x.size()` and returns scalar. Validate the selected reconstruction `type` on tiny tensors before use. |

## Criterion-selection patterns

- **Default 3D segmentation trainer:** prefer `DiceLoss(classes=C)`, `GeneralizedDiceLoss(classes=C)`, or `BCEDiceLoss(classes=C)` because the trainer unpacks `(loss, per_channel_score)` and logs channel scores.
- **Class imbalance without per-channel logging:** `WeightedCrossEntropyLoss` is scalar-only and suitable for custom loops or a trainer route adapted by `segmentation-workflows`.
- **Voxel-weighted supervision:** use `PixelWiseCrossEntropyLoss` only when your batch provides a per-voxel weight map and your loop can call `criterion(output, target, weights)`.
- **Embedding/instance losses:** use `ContrastiveLoss` for embedding heads and contiguous instance labels; do not treat it as a semantic segmentation Dice substitute.
- **Tag-direction heads:** use `TagsAngularLoss` only for list-based tag-head outputs whose target heads and coefficients align.
- **2D segmentation:** use `DiceLoss2D` and verify singleton-batch behavior before running a long job.
