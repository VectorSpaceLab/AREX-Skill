# Modeling API Reference

This reference captures stable MONAI modeling primitives and practical shape contracts. Signatures are concise and omit some inherited or advanced parameters; inspect the installed package when exact optional parameters are needed.

## Core Shape Contracts

| Item | Contract |
| --- | --- |
| Image tensor | `(B, C_in, spatial...)`; examples: `(2, 1, 128, 128)` or `(1, 1, 96, 96, 96)`. |
| Network logits | `(B, C_out, spatial...)`; `C_out=1` for single-channel binary logits, `C_out=num_classes` for multi-class logits. |
| Class-index label | `(B, 1, spatial...)`; values are integer class ids from `0` to `num_classes - 1`. |
| One-hot label/prediction | `(B, num_classes, spatial...)`; channels encode classes. |
| Sliding-window ROI | Spatial dimensions only, for example `(96, 96, 96)`, not `(B, C, 96, 96, 96)`. |
| Metric batch input | Postprocessed predictions and labels with matching batch/spatial dimensions and compatible channel representation. |

## Networks

### `monai.networks.nets.UNet`

Signature:

```python
UNet(
    spatial_dims,
    in_channels,
    out_channels,
    channels,
    strides,
    kernel_size=3,
    up_kernel_size=3,
    num_res_units=0,
    act="PRELU",
    norm="INSTANCE",
    dropout=0.0,
    bias=True,
    adn_ordering="NDA",
)
```

Usage notes:

- `len(strides)` should align with the downsampling stages implied by `channels`.
- Use small `channels` such as `(4, 8)` or `(8, 16, 32)` for CPU smoke tests.
- `spatial_dims=3` expects five-dimensional input `(B, C, H, W, D)`.

### `monai.networks.nets.SwinUNETR`

Signature:

```python
SwinUNETR(
    in_channels,
    out_channels,
    patch_size=2,
    depths=(2, 2, 2, 2),
    num_heads=(3, 6, 12, 24),
    window_size=7,
    qkv_bias=True,
    mlp_ratio=4.0,
    feature_size=24,
    norm_name="instance",
    drop_rate=0.0,
    attn_drop_rate=0.0,
    dropout_path_rate=0.0,
    normalize=True,
    patch_norm=False,
    use_checkpoint=False,
    spatial_dims=3,
    downsample="merging",
    use_v2=False,
)
```

Usage notes:

- Use for larger patch-based segmentation workloads; it has substantially higher memory requirements than a tiny UNet.
- `feature_size`, `window_size`, and input divisibility affect feasibility; validate with a representative patch before full-volume inference.
- `use_checkpoint=True` can reduce training memory at compute cost, but inference memory still depends on ROI and output channels.

## Losses

### `monai.losses.DiceLoss`

Signature:

```python
DiceLoss(
    include_background=True,
    to_onehot_y=False,
    sigmoid=False,
    softmax=False,
    other_act=None,
    squared_pred=False,
    jaccard=False,
    reduction="mean",
    smooth_nr=1e-5,
    smooth_dr=1e-5,
    batch=False,
    weight=None,
    soft_label=False,
)
```

Shape notes:

- Inputs are predictions/logits shaped `(B, C, spatial...)`.
- If `to_onehot_y=True`, labels should be class-index targets shaped `(B, 1, spatial...)` and `C` must be the number of classes.
- Use exactly one activation option: `sigmoid=True`, `softmax=True`, or `other_act=...`.

### `monai.losses.DiceCELoss`

Signature:

```python
DiceCELoss(
    include_background=True,
    to_onehot_y=False,
    sigmoid=False,
    softmax=False,
    other_act=None,
    squared_pred=False,
    jaccard=False,
    reduction="mean",
    smooth_nr=1e-5,
    smooth_dr=1e-5,
    batch=False,
    weight=None,
    lambda_dice=1.0,
    lambda_ce=1.0,
    label_smoothing=0.0,
)
```

Shape notes:

- Good default for multi-class segmentation: `DiceCELoss(to_onehot_y=True, softmax=True)` with logits `(B, C, spatial...)` and labels `(B, 1, spatial...)`.
- For binary single-channel logits, use `sigmoid=True` and leave `to_onehot_y=False`.

## Metrics

### `monai.metrics.DiceMetric`

Signature:

```python
DiceMetric(
    include_background=True,
    reduction="mean",
    get_not_nans=False,
    ignore_empty=True,
    num_classes=None,
    return_with_label=False,
    per_component=False,
)
```

Usage notes:

- Metrics are stateful. Call the metric on each batch, call `aggregate()` once, then call `reset()`.
- Feed postprocessed predictions, not raw logits, unless using a helper specifically configured to apply activation/discretization.
- `ignore_empty=True` skips empty ground-truth classes during reduction; this can produce `NaN` or fewer valid class contributions depending on settings.
- `include_background=False` drops channel 0 from the result and is common for foreground-focused segmentation reporting.

### `monai.metrics.HausdorffDistanceMetric`

Signature:

```python
HausdorffDistanceMetric(
    include_background=False,
    distance_metric="euclidean",
    percentile=None,
    directed=False,
    reduction="mean",
    get_not_nans=False,
)
```

Usage notes:

- Use on postprocessed masks rather than logits.
- `percentile=95` is a common robust HD95-style setting when full Hausdorff is too sensitive to outliers.
- Surface/distance metrics may rely on optional numerical/image-processing dependencies for some backends.

## Inferers

### `monai.inferers.sliding_window_inference`

Signature:

```python
sliding_window_inference(
    inputs,
    roi_size,
    sw_batch_size,
    predictor,
    overlap=0.25,
    mode="constant",
    sigma_scale=0.125,
    padding_mode="constant",
    cval=0.0,
    sw_device=None,
    device=None,
    progress=False,
    roi_weight_map=None,
    process_fn=None,
    buffer_steps=None,
    buffer_dim=-1,
    with_coord=False,
    *args,
    **kwargs,
)
```

Usage notes:

- `inputs` can be a `torch.Tensor` or MONAI `MetaTensor` with batch and channel axes.
- `predictor` receives window batches and returns a tensor, tuple, or dict of tensors.
- Output device defaults to the input device unless `device` is specified.
- `sw_device` controls where windows are forwarded; `device` controls where stitched output is accumulated.

### `monai.inferers.SlidingWindowInferer`

Signature:

```python
SlidingWindowInferer(
    roi_size,
    sw_batch_size=1,
    overlap=0.25,
    mode="constant",
    sigma_scale=0.125,
    padding_mode="constant",
    cval=0.0,
    sw_device=None,
    device=None,
    progress=False,
    cache_roi_weight_map=False,
    cpu_thresh=None,
    buffer_steps=None,
    buffer_dim=-1,
    with_coord=False,
)
```

Usage notes:

- Object form is convenient for evaluators or repeated inference calls.
- Use `cache_roi_weight_map=True` only when ROI shape and blending parameters are stable.
- `cpu_thresh` can move stitching to CPU for large images, but this trades GPU memory for CPU memory and transfer time.

## Postprocessing Transforms

### `monai.transforms.Activationsd`

Signature:

```python
Activationsd(keys, sigmoid=False, softmax=False, other=None, allow_missing_keys=False, **kwargs)
```

Usage notes:

- Dictionary transform for applying activations to prediction keys.
- Use `softmax=True` for mutually exclusive multi-class channel logits.
- Use `sigmoid=True` for binary or multi-label logits.

### `monai.transforms.AsDiscreted`

Signature:

```python
AsDiscreted(keys, argmax=False, to_onehot=None, threshold=None, rounding=None, allow_missing_keys=False, **kwargs)
```

Usage notes:

- Use `argmax=True, to_onehot=num_classes` after softmax for multi-class segmentation predictions.
- Use `threshold=0.5` after sigmoid for binary or multi-label masks.
- Use `to_onehot=num_classes` on label keys when metrics require one-hot labels.

## One-Hot Utility

`monai.networks.one_hot(labels, num_classes, dim=1, dtype=torch.float)` converts class-index labels to one-hot tensors. Typical input labels include `(B, 1, spatial...)` and output becomes `(B, num_classes, spatial...)` along `dim=1`.

## Minimal Multi-Class Pattern

```python
from monai.losses import DiceCELoss
from monai.metrics import DiceMetric
from monai.networks.nets import UNet
from monai.transforms import Compose, Activationsd, AsDiscreted

num_classes = 3
net = UNet(spatial_dims=3, in_channels=1, out_channels=num_classes, channels=(8, 16), strides=(2,))
loss = DiceCELoss(to_onehot_y=True, softmax=True)
metric = DiceMetric(include_background=False, reduction="mean")
post = Compose([
    Activationsd(keys="pred", softmax=True),
    AsDiscreted(keys="pred", argmax=True, to_onehot=num_classes),
    AsDiscreted(keys="label", to_onehot=num_classes),
])
```
