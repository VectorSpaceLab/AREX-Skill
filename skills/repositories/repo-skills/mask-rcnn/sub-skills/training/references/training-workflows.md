# Training Workflows

## API sequence

```python
from mrcnn.config import Config
from mrcnn import model as modellib

class TrainConfig(Config):
    NAME = "my_dataset"
    NUM_CLASSES = 1 + 1
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    IMAGE_MIN_DIM = 512
    IMAGE_MAX_DIM = 512
    STEPS_PER_EPOCH = 100
    VALIDATION_STEPS = 5

config = TrainConfig()
model = modellib.MaskRCNN(mode="training", config=config, model_dir="logs")
model.load_weights("initial_weights.h5", by_name=True)
model.train(dataset_train, dataset_val,
            learning_rate=config.LEARNING_RATE,
            epochs=30,
            layers="heads")
```

Both `dataset_train` and `dataset_val` must be prepared `mrcnn.utils.Dataset` subclasses. See [dataset-contract.md](../../data-preparation/references/dataset-contract.md).

## Layer selection

The package maps friendly layer names to regular expressions:

| Layers argument | Meaning |
| --- | --- |
| `heads` | Train RPN, FPN, classifier, bbox, and mask heads while leaving backbone frozen. Good first stage for transfer learning. |
| `3+` | Fine-tune ResNet stage 3 and above plus heads. |
| `4+` | Fine-tune ResNet stage 4 and above plus heads. Common second COCO stage. |
| `5+` | Fine-tune ResNet stage 5 and heads. |
| `all` | Train all layers. Use after heads have stabilized and memory/runtime are acceptable. |
| Custom regex | Any regular expression matched against layer names. Use only after inspecting model summary/layers. |

## Sample schedules distilled from repository evidence

These schedules are starting points, not universal prescriptions.

### Balloon / one-class VIA polygons

- Config: `NUM_CLASSES = 1 + 1`, `STEPS_PER_EPOCH = 100`, `DETECTION_MIN_CONFIDENCE = 0.9`.
- Common transfer path: load COCO weights by name, exclude final class/mask heads, train `heads` for about 30 epochs.
- Dataset: `train/` and `val/` with VIA polygon JSON.

### COCO

- Config: `NUM_CLASSES = 1 + 80`, `IMAGES_PER_GPU = 2` for a 12GB GPU in the original notes.
- Training stages:
  1. heads to epoch 40;
  2. `4+` to epoch 120;
  3. `all` to epoch 160 with lower learning rate.
- Evaluation uses pycocotools and COCO validation/minival splits.

### Nucleus

- Config: `BACKBONE = "resnet50"`, crop training resize at 512, `NUM_CLASSES = 1 + 1`, `DETECTION_MIN_CONFIDENCE = 0`.
- Schedule: train heads, then all layers. The sample uses augmentation including flips, rotations, multiply, and blur.
- Validation split is hard-coded in the original sample; adjust for partial datasets.

### Shapes

- Config: `IMAGE_MIN_DIM = IMAGE_MAX_DIM = 128`, `NUM_CLASSES = 1 + 3`, small anchors.
- Useful for pipeline smoke tests and educational notebooks. It still uses a deep backbone, so CPU training remains slow.

## Augmentation

`MaskRCNN.train()` accepts `augmentation` and passes it to the data generator. Use mask-safe imgaug augmenters and test that masks maintain shape. For sources that should not be augmented, use `no_augmentation_sources`.

## Callbacks and logs

Training creates TensorBoard and checkpoint callbacks automatically. `model_dir` controls the log/checkpoint root; `set_log_dir()` creates timestamped experiment directories and `checkpoint_path` naming.

Custom callbacks can be appended through `custom_callbacks`, but they must be compatible with Keras `fit_generator`.

## Practical validation

Before a long training run:

1. Validate dataset layout.
2. Load a few images/masks and visualize them.
3. Build a tiny inference/training graph with a small config.
4. Run one very small epoch only when hardware/time allow.
5. Confirm checkpoints are written and `find_last()` can locate them.
