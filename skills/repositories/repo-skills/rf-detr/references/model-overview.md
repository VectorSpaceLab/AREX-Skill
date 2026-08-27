# RF-DETR Model Overview

## When to read

Read this when selecting a model class or alias, explaining RF-DETR task families, deciding whether Plus models are in scope, or updating examples/tests/docs that need a concrete model.

## Task families

| Task | Public package class family | Alias pattern | Default for new examples | Notes |
| --- | --- | --- | --- | --- |
| Object detection | `RFDETRNano`, `RFDETRSmall`, `RFDETRMedium`, `RFDETRLarge` | `rfdetr-nano`, `rfdetr-small`, `rfdetr-medium`, `rfdetr-large` | `RFDETRSmall` / `"rfdetr-small"` | Use released sized variants; `RFDETRBase` is deprecated for new examples. |
| Object detection Plus | `RFDETRXLarge`, `RFDETR2XLarge` | `rfdetr-xlarge`, `rfdetr-2xlarge` | Only when user needs Plus | Requires `rfdetr_plus` through `pip install "rfdetr[plus]"` and separate license/account constraints. |
| Instance segmentation | `RFDETRSegNano`, `RFDETRSegSmall`, `RFDETRSegMedium`, `RFDETRSegLarge`, `RFDETRSegXLarge`, `RFDETRSeg2XLarge` | `rfdetr-seg-{nano,small,medium,large,xlarge,2xlarge}` | `RFDETRSegSmall` or `RFDETRSegMedium` depending accuracy/latency need | Do not use `RFDETRSegPreview` for new examples. |
| Keypoint detection | `RFDETRKeypointPreview` | `rfdetr-keypoint-preview` | `RFDETRKeypointPreview` | Keypoints are preview-only in the current package. Fine-tuned keypoint models can use custom keypoint counts. |

## Public import surface

```python
from rfdetr import (
    RFDETRSmall,
    RFDETRSegSmall,
    RFDETRKeypointPreview,
    RFDETR,
    from_checkpoint,
)
```

The package also exposes `ModelContext` and released model variants at top level. Training objects such as `RFDETRModelModule`, `RFDETRDataModule`, and `build_trainer` are lazily exposed and require training dependencies.

## Model-size selection

- Use `small` for examples, docs, tests, quick starts, and most agent-generated snippets.
- Use `nano` when the user asks for lowest latency or constrained hardware.
- Use `medium`/`large` when the user emphasizes accuracy and can afford more latency/memory.
- Use Plus `xlarge`/`2xlarge` only when the user already opted into Plus dependencies/license or asks for those sizes specifically.
- For segmentation, pick the sized `RFDETRSeg*` class matching the same latency/accuracy trade-off.
- For keypoints, there is no released sized family yet; use only `RFDETRKeypointPreview`.

## Geometry facts that affect inference/export

RF-DETR validates prediction and export shapes against each model's `patch_size * num_windows` block size. Typical detection variants use a block size of `32`; many segmentation and keypoint variants use `24`, while segmentation nano uses `12`. When a user supplies `shape=(height, width)`, both dimensions must be positive integers divisible by the model's block size.

Use `sub-skills/inference-and-models/scripts/inspect_rfdetr_models.py` to inspect installed model class facts without downloading weights. Use `sub-skills/export-and-deployment/scripts/inspect_export_options.py` to preflight export shapes and output names.

## License and package boundaries

The open-source `rfdetr` package and Apache-designated model families are Apache 2.0. Plus components are supplied through a separate `rfdetr_plus` package and are not part of the baseline install. If a Plus import fails, do not treat that as a broken base RF-DETR install; route to optional dependency guidance.

## Avoid these mistakes

- Do not use `RFDETRBase` / `"rfdetr-base"` in new examples, docs, or tests.
- Do not use `RFDETRSegPreview` / `"rfdetr-seg-preview"` for new segmentation work.
- Do not use detection or segmentation preview variants as placeholders.
- Do not index fine-tuned detections with `COCO_CLASSES` unless the checkpoint is COCO-pretrained; prefer `detections.data["class_name"]`.
- Do not claim TensorRT/CoreML/TFLite/ExecuTorch support merely because a model class imports; those are export/backend-specific claims.
