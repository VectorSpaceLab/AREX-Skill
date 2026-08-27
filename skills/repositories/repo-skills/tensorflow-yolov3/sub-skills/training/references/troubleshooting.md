# Training Troubleshooting

Use this checklist before restarting a long `python train.py` run. The bundled
checker can catch many issues without importing TensorFlow:

```bash
python sub-skills/training/scripts/check_training_config.py \
  --repo-root . \
  --config-py ./core/config.py
```

Add `--require-checkpoint` when COCO-initialized training is expected.

## Missing COCO-init checkpoint

Symptoms:

- `train.py` prints a restore attempt for `cfg.TRAIN.INITIAL_WEIGHT`, then says
  the path does not exist.
- Training starts, but it is from scratch rather than COCO-initialized.
- The first frozen-head stage is silently disabled because `train.py` sets
  `FISRT_STAGE_EPOCHS = 0` after restore failure.

Fix:

1. Confirm the intended mode. If scratch training is acceptable, set
   `cfg.TRAIN.FISRT_STAGE_EPOCHS = 0` and document the choice.
2. For transfer learning, place the source COCO checkpoint artifacts under
   `./checkpoint/` for `cfg.YOLO.ORIGINAL_WEIGHT`.
3. Run `python convert_weight.py --train_from_coco` after setting
   `cfg.YOLO.CLASSES` to the target dataset.
4. Validate the converted `cfg.TRAIN.INITIAL_WEIGHT` prefix:

```bash
python sub-skills/training/scripts/check_training_config.py \
  --repo-root . \
  --config-py ./core/config.py \
  --require-checkpoint
```

A TensorFlow checkpoint prefix usually needs matching `.index` and `.data-*`
files. A `.meta` file is often needed for source checkpoint conversion, but
`train.py` restore can work from index/data files.

## Custom two-class dataset mismatch

Common failure pattern:

- The user creates a two-line class file but leaves `cfg.YOLO.CLASSES` pointing
  at an 80-class file.
- Or annotations contain class id `2` for a two-class file, where valid ids are
  only `0` and `1`.
- Or `convert_weight.py --train_from_coco` is run before changing
  `cfg.YOLO.CLASSES`, creating output heads for the wrong class count.

Fix:

1. Put exactly one class name per line in the target names file, for example:

```text
helmet
vest
```

2. Set `cfg.YOLO.CLASSES` to that file before conversion or graph construction.
3. Make every annotation class id zero-based and less than the class count.
4. Re-run COCO conversion with `--train_from_coco` after the class-file change so
   the new `conv_sbbox`, `conv_mbbox`, and `conv_lbbox` heads match `5 + C`.
5. Run the checker; it flags out-of-range class ids and malformed rows.

## NaN or exploding loss

Likely causes:

- invalid boxes where `x_max <= x_min` or `y_max <= y_min`;
- boxes outside the original image bounds;
- annotation image paths that do not exist from the training working directory;
- negative or out-of-range class ids;
- empty annotation files or files where every row has no boxes;
- too-large learning rate or batch size for the dataset/GPU;
- augmentation on boxes that are already near image edges;
- non-divisible input sizes that break stride assumptions.

Repository mitigations already present:

- invalid boxes are dropped after preprocessing;
- coordinates are clipped to the resized image extent;
- IoU/GIoU denominators add `1e-6` in several places.

What to do:

1. Run the checker with image existence checks enabled.
2. If image sizes can be inspected, add `--check-image-dimensions` to warn about
   boxes that exceed image bounds.
3. Temporarily set `cfg.TRAIN.DATA_AUG = False` to isolate augmentation effects.
4. Reduce `cfg.TRAIN.LEARN_RATE_INIT` and/or `cfg.TRAIN.BATCH_SIZE`.
5. Test a tiny subset with a few verified images before relaunching the full
   run.

## `KeyError: <image> does not exist`

`Dataset.parse_annotation` calls `os.path.exists(image_path)` exactly as written
in each annotation row. Relative paths are resolved from the process working
directory, not from the annotation file's directory.

Fix options:

- run `python train.py` from the repository root used when creating the rows;
- rewrite rows to use paths relative to that root;
- or use absolute dataset paths that are valid on the training machine.

The sample annotation files bundled with the repository were authored for a
specific machine and are not portable training data.

## `IndexError` during one-hot class assignment

`preprocess_true_boxes` creates `onehot = np.zeros(num_classes)` and then assigns
`onehot[bbox_class_ind] = 1.0`. Positive ids greater than or equal to the class
count raise an index error. Negative ids can silently index from the end of the
array in NumPy and should be treated as invalid.

Fix: validate annotation ids against `cfg.YOLO.CLASSES`; regenerate annotations
if a dataset converter used one-based ids or a stale class list.

## First-stage setting seems ignored

The config key is misspelled in the repository:

```python
__C.TRAIN.FISRT_STAGE_EPOCHS = 20
```

A correctly spelled `FIRST_STAGE_EPOCHS` field has no effect unless code is
changed. If initial checkpoint restore fails, `train.py` also overwrites the
first-stage epoch count to `0` at runtime.

## Shape mismatch when restoring or converting checkpoints

Scenarios:

- Restoring an 80-class checkpoint into a graph built for a custom class count.
- Running conversion without `--train_from_coco`, which expects a full shape
  match including output heads.
- Changing `cfg.YOLO.CLASSES` after conversion but before training.

Fix:

- For custom datasets, set `cfg.YOLO.CLASSES` first, then run
  `python convert_weight.py --train_from_coco`.
- Use the converted prefix as `cfg.TRAIN.INITIAL_WEIGHT`.
- If class count changes again, reconvert.

## `./data/log/` disappeared or old TensorBoard run vanished

`YoloTrain.__init__` deletes `./data/log/` and recreates it before constructing
its `FileWriter`. Archive any previous logs before starting a new run. Use:

```bash
tensorboard --logdir ./data
```

because summaries are written under `./data/log/`.

## Checkpoint save failure

At each epoch the script saves to:

```text
./checkpoint/yolov3_test_loss=<loss>.ckpt-<epoch>
```

If `./checkpoint/` does not exist or is not writable, epoch-end saving can fail
after a long epoch. Create and check it before launching training:

```bash
mkdir -p ./checkpoint
```

## TensorFlow/protobuf/runtime incompatibility

The repository uses TensorFlow 1.x APIs: sessions, placeholders, TF savers,
`tf.layers`, and graph collections. Old `tensorflow-gpu` wheels may not match
modern CUDA drivers or newer GPUs. Newer protobuf releases can also break TF1
imports.

Fix approach:

- prefer an isolated legacy Python environment for training;
- pin a TF1-compatible protobuf if TensorFlow import raises descriptor-related
  errors;
- prove `import tensorflow as tf`, `tf.Session`, `tf.placeholder`, and a tiny
  session run before starting training;
- only claim GPU readiness after a TensorFlow session can see and use the target
  GPU.

## Validation loss is unexpectedly multi-scale

During training, `Dataset('test')` still chooses random input sizes from
`cfg.TRAIN.INPUT_SIZE` inside the iterator. `cfg.TEST.INPUT_SIZE` is not the
source for the validation batches used by `train.py`. If you need fixed-size
validation during training, the code must be changed; changing only
`cfg.TEST.INPUT_SIZE` is insufficient.

## Empty dataset or zero-step warmup

`Dataset.load_annotations` filters out rows with no box tokens. If every row is
empty or invalid, `len(Dataset('train'))` becomes zero and training math such as
warmup/decay steps becomes meaningless.

Fix: ensure train and test annotation files contain at least one usable row with
at least one valid box. The checker reports files with no usable rows.
