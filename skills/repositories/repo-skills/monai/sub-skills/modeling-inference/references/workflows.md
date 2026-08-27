# Modeling and Inference Workflows

This reference distills MONAI modeling, loss, metric, inferer, postprocessing, visualization, and export-oriented patterns into self-contained recipes. It assumes the `monai` package and its core dependencies are installed; optional IO, visualization, export, tracking, and acceleration packages may not be installed.

## Shape And Channel Ground Rules

- Use channel-first tensors throughout MONAI modeling: `(B, C, spatial...)` for network input and logits.
- Use `spatial_dims=2` for `(B, C, H, W)` and `spatial_dims=3` for `(B, C, H, W, D)`.
- Use label tensors consistently: class-index labels are commonly `(B, 1, spatial...)`; one-hot labels are `(B, classes, spatial...)`.
- Set network `out_channels` equal to the number of output channels/classes expected by the loss and postprocessing path.
- Keep preprocessing and metadata handling in the data sub-skill; by the time tensors reach this sub-skill, they should already be channel-first and appropriately batched.

## Network Selection

| Goal | Common MONAI choice | Practical setup |
| --- | --- | --- |
| Small deterministic segmentation baseline | `monai.networks.nets.UNet` | Set `spatial_dims`, `in_channels`, `out_channels`, short `channels`, and matching `strides`; verify a tiny CPU forward first. |
| Larger 3D segmentation with transformer blocks | `SwinUNETR` | Use `spatial_dims=3` for volumes, choose `feature_size` conservatively, and expect higher memory pressure than a small UNet. |
| Residual or encoder-decoder segmentation | `SegResNet`, `BasicUNet`, `AttentionUnet`, `DynUNet` | Match architecture to patch size and anisotropy; prefer existing MONAI net classes over custom blocks when possible. |
| Classification/regression | DenseNet/EfficientNet/Regressor-style nets where available | Confirm output tensor shape before selecting losses/metrics; not all segmentation postprocessing applies. |
| Generative or diffusion inference | Diffusion/autoencoder nets and dedicated inferers | Treat as an advanced path; confirm optional dependencies and memory requirements before routing there. |

Network recipe:

1. Determine spatial rank from input tensor rank minus batch/channel axes.
2. Set `in_channels` from the input image channels after preprocessing.
3. Set `out_channels` to `1` for single-channel binary logits, or to `num_classes` for mutually exclusive multi-class logits.
4. Pick a minimal architecture that can forward a tiny representative tensor on CPU.
5. Only then scale channel widths, patch size, ROI size, and device placement.

## Loss Selection

| Prediction task | Logits shape | Label shape | Good starting loss | Key flags |
| --- | --- | --- | --- | --- |
| Binary segmentation | `(B, 1, spatial...)` | `(B, 1, spatial...)` binary mask | `DiceLoss` or `DiceCELoss` | `sigmoid=True`, `to_onehot_y=False` |
| Multi-class exclusive segmentation | `(B, C, spatial...)` | `(B, 1, spatial...)` class indices | `DiceCELoss` | `softmax=True`, `to_onehot_y=True` |
| Multi-label segmentation | `(B, C, spatial...)` | `(B, C, spatial...)` multi-hot mask | `DiceLoss`, `DiceFocalLoss`, or task-specific loss | `sigmoid=True`, `to_onehot_y=False` |
| Class imbalance | Binary or multi-class | Matching target layout | Dice + CE/Focal/Tversky variants | Tune `include_background`, `weight`, `lambda_dice`, `lambda_ce` |
| Boundary/surface emphasis | Segmentation logits | Matching masks or distances | Hausdorff/surface/clDice variants | Validate target representation and optional dependencies |

Loss wiring rules:

- Do not apply `torch.softmax` or `torch.sigmoid` before a MONAI loss if the loss is configured with `softmax=True` or `sigmoid=True`; double activation silently degrades gradients.
- Use `to_onehot_y=True` only when targets are class-index labels with a singleton channel dimension and predictions have multiple channels.
- Use `include_background=False` for foreground-centric metrics/losses when background dominance hides poor foreground performance.
- Use `soft_label=True` in `DiceLoss` only when targets intentionally contain probabilities rather than hard labels.

## Metric Selection And Lifecycle

| Need | Metric | Inputs expected |
| --- | --- | --- |
| Mean overlap for segmentation | `DiceMetric` | Postprocessed predictions and labels in compatible channel/one-hot layout. |
| Boundary or distance quality | `HausdorffDistanceMetric`, surface-distance metrics | Binary/one-hot masks, often foreground-only with `include_background=False`. |
| Confusion-style classification/segmentation summaries | Confusion matrix and ROC/AUC metrics | Discrete predictions or probabilities depending on metric. |
| Loss tracked as validation metric | `LossMetric` | Callable loss and correctly shaped prediction/label pairs. |

Metric lifecycle recipe:

1. Put the network in `eval()` and use `torch.no_grad()` for validation/inference.
2. Convert logits to discrete predictions before metrics: sigmoid/softmax, threshold or argmax, then one-hot if the metric expects channels.
3. If using batched dictionaries, decollate or otherwise ensure the metric receives consistently shaped tensors.
4. Call the metric object for each batch.
5. Call `aggregate()` once for the validation epoch.
6. Call `reset()` before the next epoch or independent evaluation.

## Postprocessing Recipes

For multi-class segmentation logits in dictionary form:

```python
from monai.transforms import Compose, Activationsd, AsDiscreted

post = Compose([
    Activationsd(keys="pred", softmax=True),
    AsDiscreted(keys="pred", argmax=True, to_onehot=num_classes),
    AsDiscreted(keys="label", to_onehot=num_classes),
])
```

For binary segmentation logits:

```python
from monai.transforms import Compose, Activationsd, AsDiscreted

post = Compose([
    Activationsd(keys="pred", sigmoid=True),
    AsDiscreted(keys="pred", threshold=0.5),
])
```

For tensor-only flows, use `monai.networks.one_hot` or tensor transforms directly, but preserve the same activation/discretization order.

## Sliding-Window Inference

Use sliding-window inference when a full image/volume is too large for one forward pass.

Function form:

```python
from monai.inferers import sliding_window_inference

logits = sliding_window_inference(
    inputs=image,
    roi_size=(96, 96, 96),
    sw_batch_size=2,
    predictor=model,
    overlap=0.25,
    mode="gaussian",
)
```

Object form:

```python
from monai.inferers import SlidingWindowInferer

inferer = SlidingWindowInferer(roi_size=(96, 96, 96), sw_batch_size=2, overlap=0.25, mode="gaussian")
logits = inferer(image, model)
```

Practical tuning:

- `roi_size` contains spatial dimensions only; it must match the network's expected spatial rank.
- Start with `mode="gaussian"` for smoother stitching when overlap regions show seams; use `mode="constant"` for simpler averaging.
- Lower `sw_batch_size` first when memory fails; lower ROI size second; lower model size last.
- Set `sw_device` for window computation and `device` for stitched output only when you need explicit device placement.
- Use `buffer_steps`/`buffer_dim` for large-volume buffering after confirming the basic inference path works.
- If the predictor returns a tuple or dict, confirm downstream code handles the same structure returned by `sliding_window_inference`.

## Visualization Notes

MONAI visualization helpers include class activation maps, occlusion sensitivity, gradient-based utilities, and TensorBoard-oriented image helpers. Treat them as optional workflow additions:

- Confirm the model exposes target layers/features compatible with CAM-style methods.
- Expect visualization tensors to follow the same channel-first convention.
- TensorBoard logging and some image display/export paths may require optional packages not present in a minimal MONAI installation.
- Keep visualization outside the core validation metric path unless it is explicitly part of the deliverable.

## Export-Oriented Caveats

This sub-skill covers model utility caveats, not Bundle CLI export orchestration. For packaged `onnx_export`, `ckpt_export`, `trt_export`, and bundle verification commands, route to `bundle-config`.

When preparing a model for export:

- First prove deterministic CPU or target-device inference with a representative example tensor.
- Prefer a wrapper module if the original network returns dicts, tuples, metadata, or auxiliary outputs that the export tool cannot represent directly.
- Avoid Python-side control flow in `forward` that depends on non-tensor metadata.
- ONNX export requires the optional `onnx` ecosystem; TensorRT export requires NVIDIA/TensorRT tooling and compatible GPU/driver support.
- Tests in MONAI commonly use CPU for ONNX comparison because CUDA and exported outputs can differ numerically.

## Cross-Skill Handoffs

- If an input is not channel-first or metadata-aware inverse transforms are needed, hand off to `data-transforms` before selecting modeling primitives.
- If an agent asks for `SupervisedTrainer`, validation handlers, checkpointing, or logging, hand off to `training-evaluation` after selecting the model/loss/metric primitive.
- If the model must be run from a Bundle config or exported with Bundle CLI commands, hand off to `bundle-config` after verifying the primitive forward path.
