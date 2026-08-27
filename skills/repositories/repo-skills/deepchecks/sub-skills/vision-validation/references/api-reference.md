# Vision Validation API Reference

This reference collects the public shapes future agents usually need first when wrapping images in Deepchecks Vision.

## Public import map

```python
from deepchecks.vision import VisionData, BatchOutputFormat, classification_dataset_from_directory
from deepchecks.vision.suites import data_integrity, train_test_validation, model_evaluation, full_suite
from deepchecks.vision.checks import ImagePropertyOutliers, LabelDrift, ClassPerformance
from deepchecks.vision.metrics import ObjectDetectionAveragePrecision, ObjectDetectionTpFpFn, MeanDice, MeanIoU
```

## `VisionData`

Signature snapshot:

`VisionData(batch_loader, task_type, label_map=None, dataset_name=None, reshuffle_data=True)`

| parameter | meaning |
| --- | --- |
| `batch_loader` | Iterable that yields batches in Deepchecks Vision format. Validation reads the first batch immediately, so prefer a re-iterable object or DataLoader rather than a one-shot generator. |
| `task_type` | One of `classification`, `object_detection`, `semantic_segmentation`, or `other`. |
| `label_map` | Optional `dict[int, str]` for readable class names and display output. |
| `dataset_name` | Optional display name shown in results and summaries. |
| `reshuffle_data` | If `True`, Deepchecks tries to reshuffle recognized loaders. Keep `False` for custom iterables and TensorFlow datasets that are already shuffled upstream. |

Useful `VisionData` attributes and helpers:

- `task_type`
- `label_map`
- `has_images`, `has_labels`, `has_predictions`, `has_embeddings`, `has_additional_data`, `has_image_identifiers`
- `num_classes`
- `number_of_images_cached`
- `get_observed_classes(use_class_names=True)`
- `get_cache(use_class_names=True)`
- `copy(reshuffle_data=False, batch_loader=None)`
- `head(num_images_to_display=5, show_in_window=False)` for a quick visual sanity check

## `BatchOutputFormat` and accepted batch keys

A batch may be a plain dictionary or `BatchOutputFormat`. Deepchecks Vision accepts these keys:

| key | expected format |
| --- | --- |
| `images` | Iterable of PIL images or HWC arrays/tensors. Images must be 3D, with 1 or 3 channels, and pixel values in the uint8 range `0..255`. |
| `labels` | Task-specific labels. |
| `predictions` | Task-specific predictions. |
| `image_identifiers` | Optional iterable of strings used for traceability in results. If omitted, Deepchecks falls back to sequential sample ids. |
| `additional_data` | Accepted by `VisionData` for downstream checks that expect extra sample-level data. |
| `embeddings` | Accepted by `VisionData` for downstream checks that expect per-sample embeddings. |

General rule: every formatter in a batch must return the same number of samples.

### Core task shapes

| task | labels | predictions | notes |
| --- | --- | --- | --- |
| `classification` | Single class id per image, either `int` or `str`. | Probability vector per image. Each vector should sum to about `1`. | If `label_map` is omitted and predictions are present, Deepchecks can infer a string label map from the probability length. |
| `object_detection` | Per image, an `Nx5` array with rows `[class_id, x_min, y_min, w, h]`. | Per image, an `Mx6` array with rows `[x_min, y_min, w, h, confidence, class_id]`. | Keep class ids aligned with `label_map` if you want readable labels. |
| `semantic_segmentation` | Per image, an `HxW` class-id mask. | Per image, a `CxHxW` probability array. Each pixel should sum to `1` across channels. | Convert logits to probabilities before wrapping. |
| `other` | Not validated. | Not validated. | Use only when you need image-only checks or custom properties/metrics. |

## `classification_dataset_from_directory`

Signature snapshot:

`classification_dataset_from_directory(root, batch_size=32, num_workers=0, shuffle=True, pin_memory=True, object_type='DataLoader', **kwargs)`

Use it for class-per-folder image datasets.

- Supported layouts:
  - `root/class_name/*.jpg`
  - `root/train/class_name/*.jpg` and `root/test/class_name/*.jpg`
- `object_type='VisionData'` returns ready-to-run `VisionData` objects with inferred class maps.
- `object_type='DataLoader'` returns PyTorch loaders that can be adapted further.
- The helper expects a working `torchvision` install and matching image I/O support.

## Vision suite factories

| factory | signature snapshot | default coverage |
| --- | --- | --- |
| `data_integrity` | `(image_properties=None, label_properties=None, **kwargs)` | `ImagePropertyOutliers`, `LabelPropertyOutliers`, `PropertyLabelCorrelation` |
| `train_test_validation` | `(label_properties=None, image_properties=None, **kwargs)` | `NewLabels`, `HeatmapComparison`, `LabelDrift`, `ImagePropertyDrift`, `ImageDatasetDrift`, `PropertyLabelCorrelationChange` |
| `model_evaluation` | `(scorers=None, area_range=(32 ** 2, 96 ** 2), image_properties=None, prediction_properties=None, **kwargs)` | `ClassPerformance`, `MeanAveragePrecisionReport`, `MeanAverageRecallReport`, `PredictionDrift`, `SimpleModelComparison`, `ConfusionMatrixReport`, `WeakSegmentsPerformance` |
| `full_suite` | `(n_samples=5000, image_properties=None, label_properties=None, prediction_properties=None, scorers=None, area_range=(32 ** 2, 96 ** 2), **kwargs)` | Wraps the other three suite groups into a single overview suite. |

These factories are task-sensitive: some checks only run for the matching task type and will be skipped or marked unsupported when the data format does not match.

For custom composition, import `Suite` and the individual checks from `deepchecks.vision.checks`.

## Scorers, metrics, and properties

### Scorers and metrics

- Classification accepts string scorers, sklearn-style scorers/callables, and prebuilt metric objects.
- Object detection and semantic segmentation use Deepchecks metric objects or supported metric strings.
- Custom callable scorers are classification-only in the current runtime.
- Built-in Deepchecks metric classes are available from `deepchecks.vision.metrics`.
- Custom object-detection or segmentation metrics should subclass `deepchecks.vision.metrics_utils.CustomMetric` and implement `reset`, `update`, and `compute`.

Minimal custom metric skeleton:

```python
from deepchecks.vision.metrics_utils import CustomMetric

class MyMetric(CustomMetric):
    def reset(self):
        self._state = []

    def update(self, output):
        y_pred, y_true = output
        self._state.append((y_pred, y_true))

    def compute(self):
        return len(self._state)
```

### Property schema

Current runtime validation accepts property dictionaries with these keys:

- `name`
- `method`
- `output_type`

Accepted `output_type` values are `numerical`, `categorical`, and `class_id`.
Older docs may say `continuous` or `discrete`; normalize those to the current runtime values before using them.

Property input/output rule of thumb:

- Image properties receive a list of images and must return one value per image.
- Label and prediction properties receive the task-specific labels/predictions and must return one value per input sample; each item may itself be a scalar or a list of primitive values.

### Built-in property families

| family | built-in property names |
| --- | --- |
| Image | Aspect Ratio, Area, Brightness, RMS Contrast, Mean Red Relative Intensity, Mean Green Relative Intensity, Mean Blue Relative Intensity |
| Classification labels / predictions | Samples Per Class |
| Object detection labels / predictions | Samples Per Class, Bounding Box Area (in pixels), Number of Bounding Boxes Per Image |
| Semantic segmentation labels / predictions | Samples Per Class, Segment Area (in pixels), Number of Classes Per Image |

## Data-format notes

- `VisionData` validates the first batch as soon as it is constructed.
- A one-shot generator can lose its first batch during validation. Prefer a re-iterable wrapper or a DataLoader / TensorFlow dataset object.
- `reshuffle_data=True` only helps for loaders Deepchecks can recognize and reshuffle. For custom iterables and TensorFlow datasets, shuffle upstream and keep `reshuffle_data=False`.
- For classification with predictions, keep the prediction length aligned with `label_map` length.
- `task_type='other'` is the image-only path for custom data formats or image-only checks.
- Use `head()` after construction when you want a quick visual inspection of the first batch.

See [Workflows](workflows.md) for adapter patterns and [Troubleshooting](troubleshooting.md) for common failure messages.
