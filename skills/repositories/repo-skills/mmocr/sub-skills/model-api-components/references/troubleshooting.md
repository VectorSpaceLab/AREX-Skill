# Troubleshooting model API components

Use this page to diagnose component-level failures before escalating to full inference/training workflows.

## Fast triage order

1. Confirm the package imports in the active Python environment.
2. Run the bundled registry probe to see whether registries and `DataSample` classes are available.
3. Import any custom project package named by `custom_imports`.
4. Initialize the intended MMEngine default scope, usually `mmocr`.
5. Check registry membership with `MODELS.get(...)`, `TRANSFORMS.get(...)`, `METRICS.get(...)`, or `VISUALIZERS.get(...)`.
6. Build the smallest component config that fails.
7. Verify the `DataSample` fields passed across the failing boundary.
8. Only then move to full dataset, checkpoint, or distributed training checks.

## Registry scope and default-scope problems

Symptoms:

- `KeyError` or build failure for a known MMOCR type such as `DBNet`, `LoadOCRAnnotations`, `Dictionary`, or `HmeanIOUMetric`.
- A class with the same name from another OpenMMLab package is selected unexpectedly.
- A config works in one script but fails in another.

Causes:

- MMOCR modules were not imported, so decorators have not populated registries.
- The current MMEngine default scope is not `mmocr`.
- A project package has not been imported before the config tries to build its class.
- A custom class was registered into the wrong registry.

Fixes:

```python
from mmengine.registry import init_default_scope
from mmocr.utils import register_all_modules
from mmocr.registry import MODELS, TRANSFORMS, METRICS, VISUALIZERS

register_all_modules(init_default_scope=False)
init_default_scope('mmocr')

assert MODELS.get('DBNet') is not None
assert TRANSFORMS.get('LoadOCRAnnotations') is not None
assert METRICS.get('HmeanIOUMetric') is not None
assert VISUALIZERS.get('TextDetLocalVisualizer') is not None
```

For project classes, import the project package first or include config `custom_imports` with `allow_failed_imports=False` so failures are explicit.

## Custom module not registered or not imported

Symptoms:

- Config says `type='TinyOCRBackbone'`, but `MODELS.build` cannot find it.
- Importing the project package succeeds, but the class still is not in `MODELS`.
- Registration works interactively but not in config-based construction.

Checks:

```python
import my_ocr_project
from mmocr.registry import MODELS
print(MODELS.get('TinyOCRBackbone'))
```

Fixes:

- Ensure the class definition has the correct decorator: `@MODELS.register_module()` for a backbone, head, postprocessor, loss, recognizer, or data preprocessor.
- Ensure the package `__init__.py` imports the module where the decorated class is defined.
- Ensure the config imports the package before the component is built:

```python
custom_imports = dict(imports=['my_ocr_project'], allow_failed_imports=False)
```

- If the class is a transform, metric, visualizer, or task utility, register it with `TRANSFORMS`, `METRICS`, `VISUALIZERS`, or `TASK_UTILS` instead of `MODELS`.
- Avoid duplicate class names when another imported package might register the same name.

## DataSample field mismatch

Symptoms:

- `AttributeError` for `gt_instances`, `pred_instances`, `gt_text`, or `pred_text`.
- Visualizer draws nothing or crashes on missing `scores`, `texts`, `bboxes`, `polygons`, or `edge_labels`.
- Metric returns zeros or fails even though model outputs look plausible.
- Setter raises because a plain tensor/dict was assigned to a `DataSample` property.

Correct field choices:

| Boundary | Required fields |
| --- | --- |
| Text detection postprocessor -> visualizer/metric | `pred_instances.polygons` or `pred_instances.bboxes`, plus `pred_instances.scores`; ground truth often needs `gt_instances.polygons` and optional `gt_instances.ignored`. |
| Text recognition postprocessor -> metric/visualizer | `pred_text.item` and usually `pred_text.score`; ground truth uses `gt_text.item`. |
| Text spotting postprocessor -> visualizer/metric | Geometry in `pred_instances.polygons` or `pred_instances.bboxes`, text strings in `pred_instances.texts`, confidence in `pred_instances.scores` and optionally `text_scores`. |
| KIE postprocessor -> metric/visualizer | `pred_instances.labels`, `pred_instances.scores`, `pred_instances.edge_labels`, `pred_instances.edge_scores`; GT layout uses `gt_instances.bboxes` and `gt_instances.texts`. |

Fix pattern:

```python
from mmengine.structures import InstanceData, LabelData
from mmocr.structures import TextDetDataSample, TextRecogDataSample

sample = TextDetDataSample()
sample.pred_instances = InstanceData(polygons=[], scores=[])

rec_sample = TextRecogDataSample()
rec_sample.pred_text = LabelData(item='MMOCR', score=[0.99])
```

Do not assign a plain tensor directly to `sample.pred_instances` or `sample.pred_text`; wrap values in `InstanceData` or `LabelData`.

## Dictionary and token unknowns

Symptoms:

- `Chararcter: X not in dict` during label encoding.
- Decoder output dimension does not match `dictionary.num_classes`.
- Recognition metric is poor because text casing/symbols do not match expected dictionary behavior.
- Postprocessor warns that an ignored character such as `padding`, `end`, or `unknown` does not exist.

Checks:

```python
from mmocr.registry import TASK_UTILS

dictionary = TASK_UTILS.build(dict(
    type='Dictionary',
    dict_file='path/to/your/dict.txt',
    with_padding=True,
    with_unknown=True,
))
print(dictionary.num_classes, dictionary.padding_idx, dictionary.unknown_idx)
print(dictionary.str2idx('abc'))
```

Fixes:

- Use a one-character-per-line dictionary; no duplicates.
- Align model decoder output classes to `dictionary.num_classes` after special tokens are appended.
- For CTC-like models, include the expected padding/blank token and ignore it in postprocessing.
- For attention-like models, include start/end tokens when the decoder expects them.
- If labels may contain characters outside the dictionary, either expand the dictionary or intentionally set `with_unknown=True` and evaluate whether unknown substitution is acceptable.
- Normalize text consistently in transforms if metrics should ignore case/symbol differences.

## Transform pipeline type not found or wrong keys

Symptoms:

- `KeyError` for transform type names such as `LoadOCRAnnotations`, `PackTextDetInputs`, or a custom transform.
- Transform crashes with a missing key such as `img`, `gt_polygons`, `gt_texts`, or `gt_edge_labels`.
- Packed model inputs lack the expected `DataSample` fields.

Causes and fixes:

- Registry not populated: import MMOCR modules and set the default scope before building the pipeline.
- Custom transform not imported: include the project in `custom_imports` or import it before build.
- Transform order wrong: put image loading before image transforms, annotation loading before annotation transforms, and packing transforms last.
- Task packer mismatch: use `PackTextDetInputs` for detection/spotting geometry, `PackTextRecogInputs` for recognition labels, and `PackKIEInputs` for KIE graph data.
- Cross-project adapter missing: insert `MMDet2MMOCR` or `MMOCR2MMDet` only at boundaries where a detector from another OpenMMLab package expects different field names.

Small pipeline sanity check:

```python
from mmengine.registry import init_default_scope
from mmocr.utils import register_all_modules
from mmocr.registry import TRANSFORMS

register_all_modules(init_default_scope=False)
init_default_scope('mmocr')
assert TRANSFORMS.get('PackTextDetInputs') is not None
```

## Visualization font and headless issues

Symptoms:

- Window/display errors in a server or notebook-free environment.
- Saved text visualization has boxes but missing Chinese/Korean/Unicode glyphs.
- KIE visualizer crashes on dataset metadata or edge label shape.
- Detection visualizer filters all predictions.

Fixes:

- Use non-interactive mode: pass `show=False` and save through an output file or visualizer backend.
- Provide a valid font through `font_properties` for non-Latin characters.
- For text detection, ensure `pred_instances.scores` exists and adjust `pred_score_thr` if all predictions are filtered.
- For text recognition, ensure `gt_text.item` / `pred_text.item` exist.
- For spotting, ensure `pred_instances.texts` length matches geometry length.
- For KIE, set `visualizer.dataset_meta['category']` to a mapping whose label ids have `name` fields; ensure `edge_labels` is `(N, N)` and `texts` length is `N`.
- Use RGB image arrays as inputs.

## Metric output mismatch

Symptoms:

- Expected keys are absent from the evaluator output.
- Multiple metrics overwrite keys.
- Scores are zero because predictions are in the wrong fields.
- Text recognition accuracy differs from paper-style reporting.

Fixes:

- For `HmeanIOUMetric`, provide polygons and scores; check ignored GT flags and threshold search settings.
- For `WordMetric`, choose modes explicitly: `exact`, `ignore_case`, and/or `ignore_case_symbol`.
- For `CharMetric`, remember output is character recall/precision and is case-insensitive.
- For `OneMinusNEDMetric`, expect output key `1-N.E.D` and use it for edit-distance-sensitive text-line evaluation.
- For `F1Metric`, ensure predicted and GT labels are aligned and use `micro`/`macro` modes intentionally.
- When combining metrics, use distinct keys or evaluator prefixes if two metrics could emit the same name.
- Custom metrics should return stable scalar dictionaries from `compute_metrics`.

## Project config import paths

Symptoms:

- A contributed project config fails to import its package.
- Registered project classes are missing during build.
- Project-specific dictionaries or transforms cannot be found after moving the config.

Fixes:

- Make the project package importable through a normal Python packaging or application setup method.
- Keep `custom_imports` in every config that references project classes.
- Do not depend on implicit working-directory imports in reusable code; package the project module and dictionary resources explicitly.
- If dictionary paths use config-relative template variables, resolve them into stable application paths before runtime use.
- For advanced contributed projects, keep model, transforms, metrics, dictionaries, and postprocessors together; splitting one without updating the others usually breaks token or `DataSample` contracts.

## Advanced difficult cases

### Add a custom backbone through a project package

Failure-prone points:

- Class registered in `MODELS` but package `__init__.py` does not import it.
- Config has `custom_imports`, but the package is not importable in the runtime environment.
- Backbone returns one feature map while the neck expects multiple feature levels.
- Channel counts do not match downstream `in_channels`.

Minimal acceptance checks:

```python
import my_ocr_project
from mmengine.registry import init_default_scope
from mmocr.utils import register_all_modules
from mmocr.registry import MODELS

register_all_modules(init_default_scope=False)
init_default_scope('mmocr')
assert MODELS.get('TinyOCRBackbone') is not None
backbone = MODELS.build(dict(type='TinyOCRBackbone', out_channels=64))
```

Then test a tiny tensor through the backbone and inspect output feature shapes before plugging it into a full detector.

### Choose `DataSample` fields for a custom postprocessor and visualizer

Failure-prone points:

- Detection postprocessor writes `bboxes` but visualizer is configured to draw only polygons.
- Spotting postprocessor writes decoded strings to `pred_text` instead of `pred_instances.texts`.
- Recognition postprocessor writes a plain string instead of `LabelData(item=...)`.
- KIE postprocessor predicts edges but produces a flat vector rather than an `(N, N)` matrix.

Minimal acceptance checks:

```python
from mmengine.structures import InstanceData, LabelData
from mmocr.structures import TextDetDataSample, TextRecogDataSample, KIEDataSample

# Detection / spotting geometry
sample = TextDetDataSample()
sample.pred_instances = InstanceData(polygons=[], scores=[])
assert 'pred_instances' in sample and 'scores' in sample.pred_instances

# Recognition text
rec_sample = TextRecogDataSample()
rec_sample.pred_text = LabelData(item='abc', score=[1.0, 1.0, 1.0])
assert rec_sample.pred_text.item == 'abc'

# KIE graph shape should be checked against N boxes/texts.
kie_sample = KIEDataSample()
```

## When to route elsewhere

- If the failure is about downloading models, inferencer task modes, visualization output from a pretrained pipeline, or prediction JSON format, route to the inference sub-skill.
- If the failure is about CLI options, config inheritance, training loops, distributed launch, work directories, checkpoint loading, or evaluator placement in a full run, route to the training/evaluation/config sub-skill.
- If the failure is about converting public datasets, obtaining raw data, or preparing dataset-zoo tasks, route to the data-preparation sub-skill.
