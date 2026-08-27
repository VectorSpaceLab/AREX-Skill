# Vision Workflows

This guide distills the most common ways to prepare Deepchecks Vision inputs without depending on large external downloads.

## 1) Start with a re-iterable batch loader

Because `VisionData` validates the first batch immediately, prefer a loader object whose `__iter__` returns a fresh iterator every time.

```python
class TinyVisionBatches:
    def __init__(self, batches):
        self._batches = list(batches)

    def __iter__(self):
        return iter(self._batches)
```

Use this pattern for tiny in-memory fixtures, precomputed predictions, or smoke tests. Avoid a one-shot generator object unless you explicitly accept losing the first batch during validation.

## 2) PyTorch DataLoader adapter

For PyTorch, adapt the collate function so the batch becomes Deepchecks-compatible. The main job is to convert tensors into HWC uint8 images and keep labels/predictions in the task-specific shapes.

```python
def deepchecks_collate(batch):
    images, labels = zip(*batch)
    images = torch.stack(images).permute(0, 2, 3, 1).cpu().numpy()
    # Unnormalize first if your dataset is normalized.
    images = np.clip(images, 0, 255).astype(np.uint8)
    return {
        'images': list(images),
        'labels': list(labels),
    }
```

If you already have model outputs, add `predictions` to the same batch dict. Keep the loader shuffled or use a recognized `DataLoader` with `reshuffle_data=True`.

## 3) TensorFlow dataset adapter

For TensorFlow, the simplest route is to `map` an existing dataset into Deepchecks format and shuffle upstream before wrapping it.

```python
def to_deepchecks(batch):
    images, labels = batch
    # Convert CHW tensors to HWC before handing them to Deepchecks.
    # If your tensors are normalized, unnormalize them before this step.
    images = tf.transpose(images, [0, 2, 3, 1])
    return {
        'images': images,
        'labels': labels,
    }

vision_ds = tf_ds.shuffle(1024).map(to_deepchecks)
vision_data = VisionData(vision_ds, task_type='classification', reshuffle_data=False)
```

Keep `reshuffle_data=False` for TensorFlow datasets because Deepchecks does not reshuffle them for you.

## 4) Class-per-folder datasets

When you already have a directory tree organized by class names, use `classification_dataset_from_directory`.

```python
from deepchecks.vision import classification_dataset_from_directory

train_ds, test_ds = classification_dataset_from_directory(
    root='path/to/data',
    object_type='VisionData',
    image_extension='jpg',
)
```

If the root has no `train/` and `test/` subdirectories, the helper returns a single dataset rather than a tuple.

Use one of these layouts:

- `root/class_name/*.jpg`
- `root/train/class_name/*.jpg` and `root/test/class_name/*.jpg`

The helper is best for simple classification data. It is not a general loader for detection or segmentation datasets.

## 5) Object detection workflow

For detection, normalize every image batch into the following shapes before wrapping it:

- labels: `Nx5` arrays with `[class_id, x_min, y_min, w, h]`
- predictions: `Mx6` arrays with `[x_min, y_min, w, h, confidence, class_id]`

Practical adapter steps:

1. Load images and labels in a local collate function or generator.
2. Convert model outputs to the Deepchecks box order.
3. Keep confidence scores and class ids in the final two columns.
4. Pass a `label_map` if you want readable names in the reports.

If you are adapting a Hugging Face detector, YOLO-like output, or DETR-like output, keep the conversion logic thin and local. Treat model weights and dataset downloads as external prerequisites, not as part of the bundled smoke helper.

## 6) Semantic segmentation workflow

For segmentation, the shapes are different:

- labels: per-image `HxW` class-id masks
- predictions: per-image `CxHxW` probability arrays

If your model returns logits, apply softmax across the class/channel axis before wrapping the outputs in `VisionData`.

## 7) Precomputed predictions

If predictions are expensive or come from a remote server, read them from a local file or another local cache and include them in the batch dict.

This pattern works well when:

- the model is unavailable in the current environment
- you want to validate model outputs before training a new model
- you already have offline inference logs

The only requirement is that each batch keeps the task-specific label and prediction shapes consistent.

## 8) Choose the right suite

- `data_integrity(...)` for a single dataset
- `train_test_validation(...)` for train/test split validation
- `model_evaluation(...)` when predictions are available
- `full_suite(...)` for a combined overview

A minimal run usually looks like this:

```python
train_ds = VisionData(train_loader, task_type='classification', label_map={0: 'cat', 1: 'dog'})
test_ds = VisionData(test_loader, task_type='classification', label_map={0: 'cat', 1: 'dog'})
suite = train_test_validation()
result = suite.run(train_ds, test_ds)
```

Use the dedicated `train_dataset` / `test_dataset` pair for split validation and a single dataset for integrity checks. For a smoke-only proof, the two loaders can be tiny fixtures; for real validation they should represent different splits.

## 9) Customize properties

Properties are the easiest way to extend drift and correlation checks.

```python
def brightness(images):
    return [img.mean() for img in images]

properties = [
    {'name': 'Brightness', 'method': brightness, 'output_type': 'numerical'},
]
```

Guidelines:

- return one item per input sample
- keep output types within `numerical`, `categorical`, or `class_id`
- use `class_id` when the property output should be matched against `label_map`

## 10) Customize metrics and scorers

- Classification tasks can use sklearn-style scorers or supported string scorers.
- Object detection and segmentation tasks usually need Deepchecks metric objects or a custom metric class.
- For a custom metric class, implement `reset`, `update`, and `compute`.

```python
from deepchecks.vision.metrics_utils import CustomMetric

class ExampleMetric(CustomMetric):
    def reset(self):
        self._count = 0

    def update(self, output):
        self._count += 1

    def compute(self):
        return self._count
```

## 11) Image-only custom tasks

If your labels and predictions do not fit the built-in task formats, set `task_type='other'` and run image-only checks first. That is often enough to debug image quality, drift, or outlier issues before you invest in custom metrics.

## 12) Safe smoke workflow

For a lightweight local proof, use the bundled smoke script at [scripts/deepchecks_vision_smoke.py](../scripts/deepchecks_vision_smoke.py). It creates tiny in-memory batches, avoids downloads, and exercises the same batch-format rules used by the real loaders.
