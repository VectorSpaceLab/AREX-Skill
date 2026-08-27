# Extension patterns

Use these patterns when extending MMOCR without editing the core package. They are based on MMOCR's OpenMMLab `projects/` convention, core registry code, and contributed ABCNet/SPTS project patterns.

## Project-style extension contract

A project extension is just an importable Python package whose modules register classes into MMOCR/MMEngine registries.

Minimum contract:

1. Create an importable package, for example `my_ocr_project`.
2. In the package's `__init__.py`, import the modules that define registered classes. Registration happens at import time.
3. Decorate each class with the registry that will build it:
   - `@MODELS.register_module()` for neural modules, losses, decoders, postprocessors, preprocessors, and model wrappers.
   - `@TRANSFORMS.register_module()` for pipeline transforms.
   - `@METRICS.register_module()` for evaluation metrics.
   - `@VISUALIZERS.register_module()` for visualizers.
   - `@TASK_UTILS.register_module()` for utilities such as dictionaries/parsers that are not `nn.Module` components.
4. Add `custom_imports = dict(imports=['my_ocr_project'], allow_failed_imports=False)` to configs that use those class names.
5. Keep `default_scope = 'mmocr'` unless you intentionally build from another scope.
6. Use standard MMOCR `DataSample` fields so existing postprocessors, metrics, and visualizers continue to work.

Do not modify MMOCR core files for ordinary research extensions. A core edit should be reserved for changes that truly belong in the package API and are tested as part of the package.

## Minimal custom backbone pattern

The important parts are importability, `MODELS` registration, and output compatibility with the downstream neck/head. This simplified example shows the shape of the pattern; adapt channel counts and feature levels to the detector you are plugging into.

```python
# my_ocr_project/backbones/tiny_ocr_backbone.py
import torch
from torch import nn
from mmengine.model import BaseModule
from mmocr.registry import MODELS

@MODELS.register_module()
class TinyOCRBackbone(BaseModule):
    def __init__(self, out_channels=64, init_cfg=None):
        super().__init__(init_cfg=init_cfg)
        self.stem = nn.Sequential(
            nn.Conv2d(3, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        feat = self.stem(x)
        # Many MMOCR/MMDetection necks expect a tuple/list of feature maps.
        return (feat,)
```

```python
# my_ocr_project/__init__.py
from .backbones.tiny_ocr_backbone import TinyOCRBackbone

__all__ = ['TinyOCRBackbone']
```

Config-side pattern:

```python
default_scope = 'mmocr'
custom_imports = dict(imports=['my_ocr_project'], allow_failed_imports=False)

model = dict(
    type='DBNet',
    backbone=dict(type='TinyOCRBackbone', out_channels=64),
    # Keep the rest of the detector compatible with the backbone output.
)
```

Compatibility checks before training:

- `MODELS.get('TinyOCRBackbone')` is not `None` after importing the project.
- The backbone output type and number of feature maps match the neck/head.
- Feature map channels match any `in_channels` fields in the downstream config.
- The detector's data preprocessor still matches the task (`TextDetDataPreprocessor` for detection, `TextRecogDataPreprocessor` for recognition).

## Custom text-detection postprocessor pattern

A text-detection postprocessor should fill `TextDetDataSample.pred_instances`. Existing visualizers and `HmeanIOUMetric` expect `polygons` or `bboxes` plus `scores`.

```python
import numpy as np
import torch
from mmengine.structures import InstanceData
from mmocr.models.textdet.postprocessors import BaseTextDetPostProcessor
from mmocr.registry import MODELS

@MODELS.register_module()
class TinyTextDetPostprocessor(BaseTextDetPostProcessor):
    def get_text_instances(self, pred_result, data_sample, score_thr=0.3):
        # Replace this placeholder logic with model-specific decoding.
        polygons = [np.array([0, 0, 10, 0, 10, 10, 0, 10], dtype=np.float32)]
        scores = torch.tensor([0.99], dtype=torch.float32)

        data_sample.pred_instances = InstanceData(
            polygons=polygons,
            scores=scores,
        )
        return data_sample
```

Key rules:

- Store detection confidences in `pred_instances.scores`.
- Store polygon geometry as a list of NumPy arrays or boxes as a float tensor/array in `pred_instances.bboxes`.
- If a visualizer must show text strings, use a spotting-style sample/visualizer and set `pred_instances.texts`.
- If using `rescale_fields`, include only fields that the base postprocessor can rescale as polygons.

## Custom recognition postprocessor pattern

For recognition, use `Dictionary` consistently and fill `pred_text`.

```python
import torch
from mmengine.structures import LabelData
from mmocr.models.textrecog.postprocessors import BaseTextRecogPostprocessor
from mmocr.registry import MODELS

@MODELS.register_module()
class GreedyRecogPostprocessor(BaseTextRecogPostprocessor):
    def get_single_prediction(self, probs: torch.Tensor, data_sample=None):
        max_scores, indexes = probs.max(dim=-1)
        kept_indexes = []
        kept_scores = []
        for idx, score in zip(indexes.tolist(), max_scores.tolist()):
            if idx in self.ignore_indexes:
                continue
            kept_indexes.append(idx)
            kept_scores.append(score)
        return kept_indexes, kept_scores
```

The base class converts indexes to text with `self.dictionary.idx2str`, creates `LabelData`, and writes `data_sample.pred_text.item` plus `data_sample.pred_text.score`.

## Custom KIE postprocessor pattern

KIE postprocessors should preserve KIE layout semantics. `KIELocalVisualizer` reads GT boxes/texts for layout and predicted labels/edges for output.

```python
import torch
from mmengine.structures import InstanceData
from mmocr.registry import MODELS

@MODELS.register_module()
class TinyKIEPostprocessor:
    def __call__(self, preds, data_samples):
        node_logits, edge_logits = preds
        for sample, node_logit, edge_logit in zip(data_samples, node_logits, edge_logits):
            labels = node_logit.argmax(dim=-1).cpu()
            scores = node_logit.softmax(dim=-1).max(dim=-1).values.cpu()
            edge_labels = edge_logit.argmax(dim=-1).cpu()
            edge_scores = edge_logit.softmax(dim=-1).max(dim=-1).values.cpu()
            sample.pred_instances = InstanceData(
                labels=labels,
                scores=scores,
                edge_labels=edge_labels,
                edge_scores=edge_scores,
            )
        return data_samples
```

Verify `edge_labels` and `edge_scores` are `(N, N)` per sample and labels are `(N,)`.

## Custom transform pattern

A transform should document required, modified, and added keys, then register with `TRANSFORMS`.

```python
from mmcv.transforms import BaseTransform
from mmocr.registry import TRANSFORMS

@TRANSFORMS.register_module()
class NormalizeOCRText(BaseTransform):
    """Normalize OCR text labels.

    Required Keys:
    - gt_texts

    Modified Keys:
    - gt_texts
    """

    def __init__(self, lower=True):
        self.lower = lower

    def transform(self, results):
        texts = results.get('gt_texts', [])
        if self.lower:
            texts = [text.lower() for text in texts]
        results['gt_texts'] = texts
        return results
```

Pipeline placement rules:

- Put image loading before transforms that use `img`, `img_shape`, or `ori_shape`.
- Put annotation loading before transforms that use `gt_bboxes`, `gt_polygons`, `gt_ignored`, `gt_texts`, or `gt_edge_labels`.
- Put `PackTextDetInputs`, `PackTextRecogInputs`, or `PackKIEInputs` last among data-formatting steps because they produce model-ready inputs and `DataSample` objects.
- Use `MMDet2MMOCR` / `MMOCR2MMDet` only at boundaries where another OpenMMLab detector expects different field names or mask types.

## Custom metric pattern

Metrics are MMEngine `BaseMetric` subclasses. The `process` method extracts minimal serializable results from predictions; `compute_metrics` aggregates and returns scalar values.

```python
from mmengine.evaluator import BaseMetric
from mmocr.registry import METRICS

@METRICS.register_module()
class ExactLengthMetric(BaseMetric):
    def process(self, data_batch, predictions):
        for sample in predictions:
            pred = sample.pred_text.item
            target = sample.gt_text.item
            self.results.append((len(pred), len(target)))

    def compute_metrics(self, results):
        correct = sum(pred_len == target_len for pred_len, target_len in results)
        total = max(len(results), 1)
        return {'exact_length_acc': correct / total}
```

Rules:

- Return plain Python scalars or tensors that MMEngine can log.
- Use stable output keys; changing keys breaks downstream log parsing.
- If combining multiple metrics, avoid duplicate output keys or set evaluator prefixes.

## Custom visualizer pattern

A custom visualizer should read task-standard `DataSample` fields and support non-interactive saving.

```python
import numpy as np
from mmocr.registry import VISUALIZERS
from mmocr.visualization import TextDetLocalVisualizer

@VISUALIZERS.register_module()
class ScoreOnlyTextDetVisualizer(TextDetLocalVisualizer):
    def add_datasample(self, name, image: np.ndarray, data_sample=None, **kwargs):
        # Reuse standard drawing and filtering behavior.
        return super().add_datasample(name, image, data_sample=data_sample, **kwargs)
```

Rules:

- Accept `show=False` and `out_file`/backend saving for headless environments.
- For text rendering beyond ASCII, expose `font_properties` and pass it to drawing helpers.
- Do not silently invent fields; fail clearly if required fields such as `pred_instances.scores` or `pred_text.item` are missing.

## ABCNet and SPTS as advanced contributed-project references

ABCNet and SPTS demonstrate larger extension surfaces beyond a single backbone:

- ABCNet registers text-spotting detectors, Bezier ROI extraction, BiFPN, detection/recognition heads, detection and recognition postprocessors, module losses, and E2E hmean metrics. Its configs import the project package through `custom_imports` and use a project dictionary for recognition tokens.
- SPTS registers a sequence-prediction text spotter, encoder/decoder, module loss, postprocessor, E2E point metric, and SPTS-specific transforms such as Bezier/polygon conversion and text-to-token conversion. Its configs import the project package and align transforms, dictionary, decoder, postprocessor, and metric around a tokenized text-spotting formulation.

Design lesson from both projects: the config can remain declarative only if every project class is registered and imported before build time, and every cross-component boundary uses stable MMOCR conventions for dictionaries, transforms, and `DataSample` fields.

## Source-script decisions for component work

- `get_flops.py`: reference-only. It builds a model from config through `MODELS` and uses a FLOP analysis package, but FLOP correctness depends on operator support and full model inputs. Keep it as conceptual evidence for how to build models from registries; do not bundle it as a component runtime helper here.
- `publish_model.py`: excluded. It mutates checkpoints by removing keys, saving files, hashing, and moving outputs; that is a maintainer checkpoint publication operation, not a safe component-inspection helper.
- Project-specific adapters/converters: reference-only unless the downstream task is explicitly about that project. They encode project-specific data/model assumptions and should not be presented as generic MMOCR component utilities.

For this sub-skill, the bundled script is intentionally limited to read-only registry/dictionary probing.
