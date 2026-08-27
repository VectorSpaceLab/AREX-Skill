# ImageAI Custom Training Workflows

Use this reference after the dataset layout has been validated. The snippets are
for ImageAI 3.x PyTorch APIs and intentionally avoid stale TensorFlow-era
parameters.

## Pre-flight checks

1. Confirm ImageAI imports in the target environment.
2. Validate the dataset layout with `scripts/validate_imageai_dataset.py`.
3. Decide whether training is a smoke run or a real accuracy run.
4. Decide whether to train from scratch or initialize from compatible `.pt` or
   `.pth` weights.
5. Prefer CUDA for real training. CPU can verify wiring but may be very slow.

For any target runtime, verify ImageAI, PyTorch, and TorchVision imports before training. Treat GPU as optional acceleration, not a requirement for API semantics; use CUDA for realistic training speed when it is available and compatible.

## Custom classification training

### Current trainer API

```python
from imageai.Classification.Custom import ClassificationModelTrainer

trainer = ClassificationModelTrainer()
trainer.setModelTypeAsResNet50()      # or MobileNetV2, InceptionV3, DenseNet121
trainer.setDataDirectory("path/to/classification-dataset")
trainer.trainModel(
    num_experiments=100,
    batch_size=8,
    model_directory=None,
    transfer_from_model=None,
    verbose=True,
)
```

Available model-type setters:

| Setter | Internal model type | Notes |
| --- | --- | --- |
| `setModelTypeAsMobileNetV2()` | `mobilenet_v2` | Smaller/faster architecture. |
| `setModelTypeAsResNet50()` | `resnet50` | Common default in examples. |
| `setModelTypeAsInceptionV3()` | `inception_v3` | Uses 299-pixel transforms in current source. |
| `setModelTypeAsDenseNet121()` | `densenet121` | DenseNet classifier head is replaced for class count. |

`trainModel(...)` signature verified from source:

```text
trainModel(num_experiments=100, batch_size=8, model_directory=None, transfer_from_model=None, verbose=True)
```

Do not pass `num_objects`, `enhance_data`, `show_network_summary`,
`continue_from_model`, `initial_num_objects`, or `save_full_model` to the
current PyTorch path.

### Classification outputs

If `model_directory` is omitted, the trainer writes under:

```text
<dataset>/models/
```

Expected artifacts:

- `<dataset_name>_model_classes.json` mapping string indexes to class labels.
- A best checkpoint named like
  `<model_type>-<dataset_name>-test_acc_<score>_epoch-<epoch>.pt` when test
  accuracy improves.

The current trainer removes the previous best checkpoint when a better test
accuracy is found, so the directory usually contains the current best `.pt` plus
the classes JSON rather than every epoch.

### Classification transfer learning

Pass `transfer_from_model="path/to/weights.pt"` or `.pth` to initialize from a
compatible PyTorch state dict for the same architecture. You may call:

```python
trainer.freezeAllLayers()      # freeze existing layers except the replaced head
# or
trainer.fineTuneAllLayers()    # default: train all layers
```

before `trainModel(...)`. The file extension check rejects `.h5` and any suffix
other than `.pt` or `.pth`. The checkpoint must be compatible with the selected
architecture; a ResNet weight file is not a DenseNet transfer source.

### Classification artifact handoff

For inference after training, route to the `classification-workflows` sub-skill
with:

- the chosen model type setter;
- the best `.pt` model path; and
- `<dataset_name>_model_classes.json`.

The current custom classification `loadModel()` takes no `num_objects` argument.

## Custom YOLO detection training

### Current trainer API

```python
from imageai.Detection.Custom import DetectionModelTrainer

trainer = DetectionModelTrainer()
trainer.setModelTypeAsYOLOv3()          # or setModelTypeAsTinyYOLOv3()
trainer.setDataDirectory(data_directory="path/to/yolo-dataset")
trainer.setTrainConfig(
    object_names_array=["class_for_id_0", "class_for_id_1"],
    batch_size=4,
    num_experiments=100,
    train_from_pretrained_model=None,
)
trainer.trainModel()
```

`setTrainConfig(...)` signature verified from source:

```text
setTrainConfig(object_names_array, batch_size=4, num_experiments=100, train_from_pretrained_model=None)
```

Supported model-type setters:

| Setter | Internal model type | Typical use |
| --- | --- | --- |
| `setModelTypeAsYOLOv3()` | `yolov3` | Larger model; source uses 9 generated anchors. |
| `setModelTypeAsTinyYOLOv3()` | `tiny-yolov3` | Smaller/faster model; source uses 6 generated anchors. |

### Detection outputs

The trainer writes inside the dataset directory:

```text
<dataset>/
  json/
    <dataset_name>_yolov3_detection_config.json
    <dataset_name>_tiny-yolov3_detection_config.json
  models/
    yolov3_<dataset_name>_mAP-<score>_epoch-<epoch>.pt
    yolov3_<dataset_name>_last.pt
    tiny-yolov3_<dataset_name>_mAP-<score>_epoch-<epoch>.pt
    tiny-yolov3_<dataset_name>_last.pt
  cache/                 # temporary/regenerable if present in the runtime path
```

The JSON contains:

```json
{
  "labels": ["class_for_id_0", "class_for_id_1"],
  "anchors": [/* generated integer anchors */]
}
```

Treat `cache/` as temporary training state when present. The current PyTorch
training path covered here uses YOLO txt annotations and does not require
`pycocotools` or a Pascal VOC pickle cache.

### Detection transfer learning

Pass a compatible `.pt` or `.pth` file with `train_from_pretrained_model=...`.
For standard YOLOv3 transfer learning, use YOLOv3 weights with
`setModelTypeAsYOLOv3()`. For TinyYOLOv3, use TinyYOLO-compatible weights with
`setModelTypeAsTinyYOLOv3()`. If the class count differs, the current loader
keeps only state-dict entries whose names and shapes match and initializes the
rest randomly.

The extension check rejects `.h5`, and invalid extensions produce a direct error
before training begins.

### Detection artifact handoff

For custom image detection, route to `object-detection-workflows` with:

- `setModelTypeAsYOLOv3()` or `setModelTypeAsTinyYOLOv3()` matching training;
- the chosen `.pt` model checkpoint, usually the best mAP checkpoint or the
  `_last.pt` checkpoint if no best file was saved; and
- the matching JSON from `<dataset>/json/`.

For custom video detection, route the same `.pt` + JSON pair to
`video-detection-workflows`. The JSON must come from the same training run as
the checkpoint because it stores labels and generated anchors.

## Dataset validation and Pascal VOC conversion workflow

For a Pascal VOC dataset, do not train directly. Convert first, then validate:

```bash
python scripts/pascal_voc_to_yolo.py --dataset-dir voc-data --output-dir voc-data-yolo
python scripts/validate_imageai_dataset.py --task detection --dataset-dir voc-data-yolo --strict
```

The converter writes class names sorted alphabetically to `classes.txt`. Use that
exact order for `object_names_array`. If a project requires a custom class order,
adjust the generated YOLO class ids and `classes.txt` together before training.

## CPU/GPU performance guidance

- ImageAI chooses CUDA automatically when `torch.cuda.is_available()` is true;
  otherwise it trains on CPU.
- CPU training can be appropriate for smoke checks with tiny fixtures but is too
  slow for realistic classification or detection accuracy work.
- A GPU run still needs enough memory for the selected model, image transforms,
  and batch size. Lower `batch_size` if CUDA runs out of memory.
- For detection, larger batches can improve optimization stability, but the
  source scales accumulation around a nominal batch size. Start with the default
  `batch_size=4` unless the GPU budget supports more.
- The active 3.x path does not require TensorFlow GPU packages.

## Minimal smoke-vs-real-training expectations

A bounded smoke run may check that folders, labels, imports, and artifact writes
work, but it does not establish model quality. A real training claim should
report at least:

- dataset sizes per class or split;
- model type;
- epoch count and batch size;
- whether transfer weights were used;
- backend used (CPU or CUDA);
- produced JSON/config and checkpoint paths;
- best test accuracy for classification or best mAP metrics for detection;
- any signs of overfitting or class imbalance.
