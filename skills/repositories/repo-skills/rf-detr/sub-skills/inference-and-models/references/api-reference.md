# RF-DETR Inference API Reference

This reference distills the RF-DETR 1.10.0.dev public inference/model surface for future runtime use. It intentionally excludes training, CLI, export, and source-maintenance details.

## Install and import boundaries

Public package facts:

```bash
pip install rfdetr
```

- Distribution/import package: `rfdetr`.
- Python: `>=3.10`.
- Core inference dependencies include PyTorch, torchvision, transformers, pydantic, supervision, numpy, requests, and pyDeprecate.
- Plus detection models require an additional package boundary:

```bash
pip install "rfdetr[plus]"
```

Plus components, including detection `RFDETRXLarge` and `RFDETR2XLarge`, are outside the Apache-only core package and are licensed under the Platform Model License. Treat the Plus extension as optional: catch `ImportError` and surface the install/license requirement instead of falling back to a different model size silently.

## Public model classes and when to choose them

| Task | Preferred classes | Size / runtime identifier | Notes |
| --- | --- | --- | --- |
| Object detection | `RFDETRNano`, `RFDETRSmall`, `RFDETRMedium`, `RFDETRLarge` | `rfdetr-nano`, `rfdetr-small`, `rfdetr-medium`, `rfdetr-large` | Use `RFDETRSmall` as the default concrete example; these identifiers are also `inference` package aliases. |
| Object detection, Plus | `RFDETRXLarge`, `RFDETR2XLarge` | `rfdetr-xlarge`, `rfdetr-2xlarge` | Requires `rfdetr[plus]`; not available from core-only installs. |
| Instance segmentation | `RFDETRSegNano`, `RFDETRSegSmall`, `RFDETRSegMedium`, `RFDETRSegLarge`, `RFDETRSegXLarge`, `RFDETRSeg2XLarge` | `rfdetr-seg-nano`, `rfdetr-seg-small`, `rfdetr-seg-medium`, `rfdetr-seg-large`, `rfdetr-seg-xlarge`, `rfdetr-seg-2xlarge` | Segmentation XL/2XL are core segmentation classes, not the Plus detection classes; these identifiers are also `inference` package aliases. |
| Keypoints | `RFDETRKeypointPreview` | `rfdetr-keypoint-preview` | Preview-only keypoint model. This is the RF-DETR size identifier; inspected docs state keypoints are not yet available through the `inference` package. |
| Generic checkpoint loader | `RFDETR.from_checkpoint(path)`, `rfdetr.from_checkpoint(path)` | n/a | Infers the concrete class from checkpoint metadata, pretrain weight name, or checkpoint filename. |

Deprecated but still importable for compatibility:

| Deprecated class/identifier | Status | Runtime rule |
| --- | --- | --- |
| `RFDETRBase` / `rfdetr-base` | Deprecated | Do not use in new examples, docs, or tests. Prefer `RFDETRSmall`. |
| `RFDETRSegPreview` / `rfdetr-seg-preview` | Deprecated | Do not use for new segmentation work. Use sized segmentation classes. |
| `RFDETRLargeDeprecated` | Legacy compatibility class | Only use when loading an old checkpoint that explicitly requires it. |

## Variant geometry and shape divisibility

`predict(shape=(height, width))` and `export(shape=...)` validate both dimensions against `patch_size * num_windows`. For prediction, rectangular shapes are accepted if both dimensions are positive integers and divisible by the block size.

| Variant family | Default resolution examples | Patch size | Windows | Required divisor |
| --- | ---: | ---: | ---: | ---: |
| Detection Nano/Small/Medium/Large | 384 / 512 / 576 / 704 | 16 | 2 | 32 |
| Deprecated Base | 560 | 14 | 4 | 56 |
| Segmentation Nano | 312 | 12 | 1 | 12 |
| Segmentation Small/Medium/Large/XLarge/2XLarge | 384 / 432 / 504 / 624 / 768 | 12 | 2 | 24 |
| Deprecated Seg Preview | 432 | 12 | 2 | 24 |
| Keypoint Preview | 576 | 12 | 2 | 24 |

If a caller passes `patch_size=...` to `predict()`, it must match the instantiated model's configured patch size. Prefer omitting `patch_size` and letting RF-DETR read the model configuration.

## Core signatures

Installed-package signatures verified during production planning:

```python
RFDETR.predict(
    images,
    threshold=0.5,
    shape=None,
    patch_size=None,
    include_source_image=True,
    **kwargs,
)

RFDETR.inference(
    compile=True,
    batch_size=1,
    dtype=torch.float32,
    *,
    inplace=False,
)

RFDETR.from_checkpoint(path, trust_checkpoint=False, **kwargs)
```

Related train/evaluate/export methods exist but are owned by sibling sub-skills.

## `predict()` inputs

`predict()` accepts:

- a single local image path string;
- a single `http` or `https` URL string;
- a `PIL.Image.Image`;
- a NumPy array;
- a `torch.Tensor` in `(C, H, W)` format with values already normalized to `[0, 1]`;
- a list of any of those image forms.

Input details:

- File paths and PIL images in non-RGB modes are converted to RGB automatically.
- Tensor inputs are not auto-converted; channel count must match `model_config.num_channels`.
- Tensor values below `0` or above `1` raise `ValueError`.
- URLs are fetched with an explicit timeout and HTTP errors are surfaced.
- A bare single input returns one prediction object; any list or tuple input returns a list, even if it has one element.

## `predict()` output types

| Model kind | Return type | Key fields |
| --- | --- | --- |
| Detection | `supervision.Detections` | `xyxy`, `confidence`, `class_id`, `data["class_name"]`, `data["source_shape"]`, optional `metadata["source_image"]` |
| Segmentation | `supervision.Detections` | All detection fields plus `mask`; masks are present even when no objects pass the threshold. |
| Keypoint | `supervision.KeyPoints` | `xy`, `keypoint_confidence`, `detection_confidence`, `class_id`, `visible`, `data["xyxy"]`, `data["class_name"]`, `data["source_shape"]`, optional `data["source_image"]` |

Detection/segmentation source image placement:

- `detections.metadata["source_image"]` is populated when `include_source_image=True`.
- `detections.data["source_shape"]` is a per-detection NumPy array of `[height, width]` rows.
- Use `include_source_image=False` to avoid carrying image arrays through filtering/indexing paths.

Keypoint source image placement:

- `KeyPoints` does not have the same collection-level metadata shape as `Detections`, so RF-DETR stores `source_image` in `key_points.data["source_image"]` as one image entry per detection when requested.
- `key_points.data["xyxy"]` stores the bounding box for each instance.
- `key_points.data["covariance"]` is present when RF-DETR emitted keypoint precision parameters and source shape is available.

## Keypoint output semantics

`RFDETRKeypointPreview.predict()` returns `supervision.KeyPoints`:

| Field | Shape | Meaning |
| --- | --- | --- |
| `key_points.xy` | `(N, K, 2)` | Pixel coordinates for each keypoint per detected instance. |
| `key_points.keypoint_confidence` | `(N, K)` | Per-keypoint findability/confidence, not a copy of object score. |
| `key_points.detection_confidence` | `(N,)` | Per-instance score used by `threshold`; keypoint models may include normalized uncertainty fusion. |
| `key_points.class_id` | `(N,)` | Predicted class slot. Use `data["class_name"]` for names. |
| `key_points.visible` | `(N, K)` | Default visibility is `keypoint_confidence > 0`; set entries to `False` to hide joints from supervision annotators. |
| `key_points.data["xyxy"]` | `(N, 4)` | Detection box in `[x1, y1, x2, y2]` order. |
| `key_points.data["covariance"]` | `(N, K, 2, 2)` | Pixel-space covariance, when precision information is available. |

`K=17` for the pretrained COCO person-keypoint preview checkpoint. Fine-tuned keypoint checkpoints use their dataset schema, so custom checkpoints can return a different keypoint count.

## Class-name mapping rules

Prefer this for all detection, segmentation, and keypoint outputs:

```python
labels = list(predictions.data["class_name"])
```

Why:

- Fine-tuned detection and segmentation checkpoints use contiguous `0`-based class IDs; `data["class_name"]` follows checkpoint/dataset class names.
- COCO-pretrained checkpoints can emit sparse COCO category IDs (`1` to `90` with gaps). `COCO_CLASSES` is a sparse dict for those IDs, while `COCO_CLASS_NAMES` is a flat 80-name list.
- Active-first keypoint checkpoints use normal `0`-based foreground class slots.
- Legacy background-first keypoint checkpoints use slot `0` as `"__background__"` and foreground slots after that.
- Fine-tuned one-class keypoint preview checkpoints can report `class_id=0` as foreground and `class_id=1` as `"__background__"`.

Manual `COCO_CLASSES[class_id]` lookup is only appropriate when you are certain the checkpoint is COCO-pretrained and the ID is a valid COCO category. It is a common bug for fine-tuned checkpoints.

## Checkpoint loading and trust

Use:

```python
from rfdetr import RFDETR

model = RFDETR.from_checkpoint("checkpoint_best_total.pth")
```

or:

```python
import rfdetr

model = rfdetr.from_checkpoint("checkpoint_best_total.pth")
```

Class inference order:

1. `model_name` saved in the checkpoint.
2. `pretrain_weights` stored in checkpoint args.
3. Checkpoint filename, when `pretrain_weights` is unset-like (`""`, `"none"`, `"null"`).

Security rules:

- Default `trust_checkpoint=False` uses safe deserialization first.
- Tensor-only checkpoints and legacy `argparse.Namespace` / `types.SimpleNamespace` args are supported without trust.
- Arbitrary Python objects in a checkpoint are rejected unless `trust_checkpoint=True`.
- Set `trust_checkpoint=True` only for checkpoint files from a fully trusted source, because it permits full pickle deserialization.
- Plus detection checkpoints raise an actionable `ImportError` when the Plus package is missing; do not pretend they are core Large models.

Checkpoint-derived schema facts:

- `from_checkpoint()` can infer `num_classes` from `class_embed` weight shape when saved config is stale.
- Keypoint checkpoint schema can be inferred from `_kp_active_mask`.
- Checkpoint-derived `num_classes` is not treated as a user override; later training can still adapt to a new dataset unless the caller explicitly passed `num_classes=...`.

## Model context and device behavior

- `RFDETR.__init__()` builds a `ModelContext` and keeps the underlying module CPU-resident until first use; prediction/export/inference lazily moves it to `model_config.device`.
- `model.model` is the `ModelContext`; `model.model.model` is the underlying PyTorch module until destructive in-place inference optimization clears it.
- Use `model.class_names` to inspect resolved class names, but prefer prediction `data["class_name"]` for per-object labels.
- `model.inference()` creates an optimized inference snapshot. With `compile=True`, the compiled snapshot is tied to a fixed batch size and square resolution. With `inplace=True`, `compile` must be `False`.
