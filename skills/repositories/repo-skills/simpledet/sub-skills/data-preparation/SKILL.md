---
name: data-preparation
description: "Guides SimpleDet annotation conversion and roidb validation for
  COCO-like, VOC, CrowdHuman, and custom JSON detection or instance-segmentation
  data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data preparation

Use this route for annotation conversion, `data/cache/*.roidb`, image layouts,
class IDs, polygon masks, split names, or validation. Read
[data-formats.md](references/data-formats.md) before conversion and
[troubleshooting.md](references/troubleshooting.md) after a failure.

## Workflow

1. Choose COCO-like JSON, VOC XML, CrowdHuman ODGT, or custom JSON.
2. Confirm the image/annotation layout and exact split names.
3. Use the bundled [convert_roidb.py](scripts/convert_roidb.py) with an explicit
   `--output`; it never downloads data.
4. Run [validate_roidb.py](scripts/validate_roidb.py) on a tiny result before
   using the cache for a model workflow.
5. Match the output basename to `DatasetParam.image_set`.
6. For masks, validate `gt_poly`, polygon lengths, and static config limits.

## Data contract

- `gt_class` uses positive foreground IDs; `0` is background and CrowdHuman
  ignore regions use `-2`.
- `gt_bbox` is `(N,4)` xyxy, not COCO xywh.
- `flipped` should be false in cached records; loader-time augmentation flips.
- `image_url`, positive `h`/`w`, and float32-safe `im_id` are required.
- Mask records need one raw polygon-list entry per instance.

## Bundled helpers

```bash
python <skill-root>/sub-skills/data-preparation/scripts/convert_roidb.py --help
python <skill-root>/sub-skills/data-preparation/scripts/validate_roidb.py --help
python <skill-root>/sub-skills/data-preparation/scripts/validate_roidb.py --input data/cache/custom.roidb --check-images --max-records 3
```

The converter supports `--format json|voc|coco|crowdhuman`; it requires only
its format-specific public dependencies and writes only the explicit output.
The validator is read-only and can check JSON/JSONL without NumPy; pickle
roidbs require NumPy.

## Route onward

- Runtime/compiler/backend issues: [setup-and-operations](../setup-and-operations/SKILL.md).
- Detector/config/checkpoint execution: [detection-workflows](../detection-workflows/SKILL.md).
- Architecture or tensor-contract changes: [model-customization](../model-customization/SKILL.md).

Read [workflows.md](references/workflows.md) for format-specific commands and
cache handoff details.
