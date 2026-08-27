# Training Workflows

This reference distills the repository's YOLOv3 training path into safe,
repeatable steps. It assumes commands are run from the repository root unless a
step says otherwise.

## 1. Choose the training mode

### Train from scratch

Use this when no pretrained checkpoint is available or when the user explicitly
wants random initialization.

Key behavior: `train.py` tries to restore `cfg.TRAIN.INITIAL_WEIGHT`. If restore
fails, it prints that the path does not exist, sets `FISRT_STAGE_EPOCHS` to `0`,
and trains only the all-variable stage. For a deliberate scratch run, make that
choice explicit in the user-facing plan instead of letting a missing checkpoint
look accidental.

Recommended config shape:

```python
__C.YOLO.CLASSES = "./data/classes/<dataset>.names"
__C.YOLO.ANCHORS = "./data/anchors/basline_anchors.txt"
__C.TRAIN.ANNOT_PATH = "./data/dataset/<dataset>_train.txt"
__C.TEST.ANNOT_PATH = "./data/dataset/<dataset>_test.txt"
__C.TRAIN.FISRT_STAGE_EPOCHS = 0
__C.TRAIN.SECOND_STAGE_EPOCHS = 30
__C.TRAIN.INITIAL_WEIGHT = "./checkpoint/missing_or_unused.ckpt"
```

Then validate and train:

```bash
python sub-skills/training/scripts/check_training_config.py \
  --repo-root . \
  --config-py ./core/config.py

python train.py
```

### Train from COCO-initialized weights

Use this when the user wants the repository's recommended transfer-learning
path. The source checkpoint must be converted into the training checkpoint
prefix that `cfg.TRAIN.INITIAL_WEIGHT` expects.

1. Put the downloaded COCO checkpoint shards under `./checkpoint/` so
   `cfg.YOLO.ORIGINAL_WEIGHT` points to a valid source prefix, normally
   `./checkpoint/yolov3_coco.ckpt`.
2. Ensure `cfg.YOLO.CLASSES` already points to the target dataset class file.
   With `--train_from_coco`, the conversion script skips the output heads and
   keeps newly shaped `conv_sbbox`, `conv_mbbox`, and `conv_lbbox` heads for the
   target class count.
3. Convert the checkpoint:

```bash
python convert_weight.py --train_from_coco
```

4. Confirm that `cfg.TRAIN.INITIAL_WEIGHT` points to the converted prefix,
   normally `./checkpoint/yolov3_coco_demo.ckpt`, and validate it as required:

```bash
python sub-skills/training/scripts/check_training_config.py \
  --repo-root . \
  --config-py ./core/config.py \
  --require-checkpoint
```

5. Run training:

```bash
python train.py
```

## 2. Edit the required config fields

Training reads values from `core/config.py` through `cfg`. At minimum align these
fields:

```python
__C.YOLO.CLASSES = "./data/classes/<dataset>.names"
__C.YOLO.ANCHORS = "./data/anchors/basline_anchors.txt"
__C.TRAIN.ANNOT_PATH = "./data/dataset/<dataset>_train.txt"
__C.TEST.ANNOT_PATH = "./data/dataset/<dataset>_test.txt"
__C.TRAIN.BATCH_SIZE = 6
__C.TRAIN.INPUT_SIZE = [320, 352, 384, 416, 448, 480, 512, 544, 576, 608]
__C.TRAIN.DATA_AUG = True
__C.TRAIN.LEARN_RATE_INIT = 1e-4
__C.TRAIN.LEARN_RATE_END = 1e-6
__C.TRAIN.WARMUP_EPOCHS = 2
__C.TRAIN.FISRT_STAGE_EPOCHS = 20
__C.TRAIN.SECOND_STAGE_EPOCHS = 30
__C.TRAIN.INITIAL_WEIGHT = "./checkpoint/yolov3_coco_demo.ckpt"
```

Important details:

- The field name is misspelled as `FISRT_STAGE_EPOCHS`; adding a correctly
  spelled `FIRST_STAGE_EPOCHS` field does not affect `train.py`.
- Annotation rows must look like
  `image_path x_min,y_min,x_max,y_max,class_id ...`. Class ids are zero-based
  indexes into `cfg.YOLO.CLASSES`.
- Relative image paths inside annotation rows are resolved by Python from the
  current training working directory. Run training from the same root used by
  the checker.
- `TRAIN.INPUT_SIZE` is multi-scale. Each batch randomly chooses one listed
  input size; every value should be positive and divisible by `32`.

## 3. Understand the two training stages

`YoloTrain.__init__` builds a TensorFlow 1.x graph, creates one `Dataset('train')`
and one `Dataset('test')`, then defines two optimizers:

1. **First stage:** only variables whose top-level scope is `conv_sbbox`,
   `conv_mbbox`, or `conv_lbbox` are trainable. This adapts the detection heads
   while the backbone and intermediate layers remain frozen.
2. **Second stage:** all `tf.trainable_variables()` are optimized.

`train.py` selects the stage per epoch:

```text
epoch <= cfg.TRAIN.FISRT_STAGE_EPOCHS  -> train_op_with_frozen_variables
epoch >  cfg.TRAIN.FISRT_STAGE_EPOCHS  -> train_op_with_all_variables
```

If initial-weight restore fails, `train.py` sets the first-stage epoch count to
zero and immediately trains all variables from scratch.

## 4. Dataset batch contract during training

Each dataset iteration returns seven arrays in the exact order fed to the graph:

```text
0 batch_image       -> input_data
1 batch_label_sbbox -> label_sbbox
2 batch_label_mbbox -> label_mbbox
3 batch_label_lbbox -> label_lbbox
4 batch_sbboxes     -> true_sbboxes
5 batch_mbboxes     -> true_mbboxes
6 batch_lbboxes     -> true_lbboxes
```

For a selected input size `S`, batch size `B`, and class count `C`:

```text
batch_image:       [B, S, S, 3]
batch_label_sbbox: [B, S/8,  S/8,  3, 5 + C]
batch_label_mbbox: [B, S/16, S/16, 3, 5 + C]
batch_label_lbbox: [B, S/32, S/32, 3, 5 + C]
batch_sbboxes:     [B, 150, 4]
batch_mbboxes:     [B, 150, 4]
batch_lbboxes:     [B, 150, 4]
```

The final incomplete batch wraps around to earlier samples so that every yielded
batch has exactly `B` examples.

## 5. Augmentation and label preprocessing

When `TRAIN.DATA_AUG` is `True`, each training image may receive three
independent 50% augmentations:

- horizontal flip;
- crop around the union of boxes;
- translation within margins allowed by the union of boxes.

After augmentation, the loader letterboxes images to the chosen square input
size, rescales boxes, drops boxes with `x_max <= x_min` or `y_max <= y_min`, and
clips coordinates into image bounds to reduce NaN risk. It does **not** guard
against out-of-range class ids before one-hot encoding, so validate class ids
before a long run.

## 6. Logs, checkpoints, and monitoring

Training side effects are relative to the repository root:

- `./data/log/` is deleted and recreated when `YoloTrain` is constructed.
- TensorBoard summaries are written to `./data/log/` with scalar names
  `learn_rate`, `giou_loss`, `conf_loss`, `prob_loss`, and `total_loss`.
- A `tqdm` progress bar reports per-step training loss.
- At each epoch, test-set loss is averaged and the model is saved under
  `./checkpoint/yolov3_test_loss=<loss>.ckpt-<epoch>` with TensorFlow checkpoint
  artifacts. The saver keeps at most ten checkpoints.

Monitoring command:

```bash
tensorboard --logdir ./data
```

Create `./checkpoint/` before training if it does not exist; `train.py` does not
create that directory before saving.

## 7. Long-run prerequisites

Before approving a real run, confirm:

- a TensorFlow 1.x-compatible runtime is active; the repository uses TF1 session,
  placeholder, saver, and summary APIs;
- the protobuf version is compatible with the chosen TF1 wheel;
- a GPU stack is compatible with that TF1 build, or the user accepts very slow
  CPU training;
- all train/test image paths in annotation files exist from the chosen working
  directory;
- the class file count matches every annotation class id;
- the initial checkpoint prefix exists when transfer learning is expected;
- disk space is sufficient for TensorBoard logs and up to ten checkpoints;
- batch size and multi-scale input sizes fit device memory.
