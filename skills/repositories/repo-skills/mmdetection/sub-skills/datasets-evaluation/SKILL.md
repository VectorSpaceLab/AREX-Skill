---
name: datasets-evaluation
description: "Prepare and validate MMDetection datasets, annotation formats,
  dataloaders, transforms, samplers, evaluators, and analysis workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datasets Evaluation

Use this sub-skill when a task is about dataset layout, annotation conversion, custom dataset config, transform pipelines, sampler choices, evaluator metrics, dataset browsing, or post-test analysis.

## Route First

- Dataset files or annotations: use `references/data-formats.md` for COCO, panoptic, MMEngine middle format, `data_root`, `ann_file`, `data_prefix`, `metainfo`, class order, transforms, samplers, and tiny validation checks.
- Metrics or analysis: use `references/evaluation-analysis.md` for `CocoMetric`, `VOCMetric`, `CityScapesMetric`, evaluator config, `format_only`, classwise AP, browsing, error analysis, and robustness commands.
- Failures: use `references/troubleshooting.md` for schema, path, category, palette, transform-key, dependency, and metric-output diagnosis.
- Image folder manifest: use `scripts/images_to_coco.py` to create a COCO-like JSON with image and category entries but no bounding-box annotations.

## Boundaries

- For launching training, testing, distributed jobs, resume, or checkpoint result dumping, route to `training-testing`.
- For custom dataset class implementation or registration code, route to `customization-extension` after this sub-skill defines the target format and config contract.
- For inference visualization and prediction rendering, route to `inference-visualization`.
- For selecting or editing base model configs outside dataset/evaluator fields, route to `configuration-model-zoo`.

## Minimal Custom COCO Config Pattern

```python
dataset_type = 'CocoDataset'
data_root = 'data/my_dataset/'
metainfo = dict(classes=('cat', 'dog'), palette=[(220, 20, 60), (0, 0, 142)])

train_dataloader = dict(dataset=dict(
    type=dataset_type,
    data_root=data_root,
    metainfo=metainfo,
    ann_file='annotations/train.json',
    data_prefix=dict(img='train/'),
    filter_cfg=dict(filter_empty_gt=True, min_size=32)))
val_dataloader = dict(dataset=dict(
    type=dataset_type,
    data_root=data_root,
    metainfo=metainfo,
    ann_file='annotations/val.json',
    data_prefix=dict(img='val/'),
    test_mode=True))
test_dataloader = val_dataloader
val_evaluator = dict(type='CocoMetric', ann_file=data_root + 'annotations/val.json', metric='bbox')
test_evaluator = val_evaluator
```

If the class count changes, update dataset `metainfo.classes`, every model head `num_classes`, evaluator `ann_file`, and visualization `palette` together.
