# Training Data Troubleshooting

## Annotation validator reports malformed boxes

**Symptoms**

- A token does not contain exactly five comma-separated fields.
- Coordinates are not integers.
- `xmax <= xmin` or `ymax <= ymin`.
- Class ID is outside the class-file range.

**Recovery**

- Regenerate the annotation file from COCO/VOC source data.
- Confirm the class file used by the converter matches the class file used by
  training/evaluation.
- For custom data, convert to pixel corner coordinates before using
  `dataset_type="converted_coco"`.

## Image path does not exist during training

**Symptom**

```text
KeyError: <image path> does not exist ...
```

**Cause**: The annotation file contains paths that are not valid on the training
machine. The repository's example annotation files contain source-author
absolute paths and are not portable.

**Recovery**

- Regenerate annotations with paths valid on the current machine, or rewrite the
  image path prefix deliberately.
- Run the bundled validator with `--check-images` on a subset before training.
- Prefer absolute paths for large external datasets, or checkout-relative paths
  for small local fixtures.

## Training crashes with NumPy alias errors

**Symptom**

```text
AttributeError: module 'numpy' has no attribute 'float'
```

**Cause**: The source uses `np.float`, which was removed in recent NumPy.
TensorFlow 2.3 normally installs NumPy 1.18.x where the alias still exists.

**Recovery**

- Use the compatibility reference's TensorFlow 2.3/Python 3.8 environment.
- If a newer stack is required, patch the target checkout to replace `np.float`
  with `float` or `np.float64` after testing dataset preprocessing.

## Class count or labels are wrong

**Symptoms**

- Model output class count does not match custom labels.
- Drawn labels are shifted or nonsensical.
- `IndexError` when mapping class IDs to names.

**Recovery**

1. Count lines in the active class file.
2. Validate all annotation class IDs are in `[0, num_classes - 1]`.
3. Confirm conversion/training/inference use the same class-file order.
4. Re-export the model after changing class count; do not reuse old converted
   artifacts with new label files.

## Scratch training still tries to load weights

**Cause**: `train.py` defaults `--weights` to `./scripts/yolov4.weights` and only
skips loading when `FLAGS.weights == None`.

**Recovery**

- For transfer learning, supply an existing `--weights` path.
- For true scratch training, patch the target checkout so the default is `None`
  or so a sentinel value like `--weights ''` skips loading. Also set
  `cfg.TRAIN.FISRT_STAGE_EPOCHS=0` as the README suggests.

## Evaluation/training reads the wrong split

**Cause**: Paths live in `core.config.cfg`, not only CLI flags.

**Recovery**

- For training, edit `cfg.TRAIN.ANNOT_PATH` and `cfg.TEST.ANNOT_PATH` before the
  run.
- For evaluation, remember that `evaluate.py` iterates `cfg.TEST.ANNOT_PATH` even
  when `--annotation_path` is passed.
- Record config edits in the user's experiment notes so conversion/inference
  artifacts can be traced back to data.

## Full training quality is lower than expected

**Evidence**: The README states training performance is not fully reproduced and
recommends AlexeyAB Darknet for training custom data, then converting `.weights`
back into this TensorFlow/TFLite repository.

**Recovery**

- Use this repo for conversion and deployment when training quality is critical.
- If using this repo's `train.py`, start with a tiny validated dataset and short
  run to catch data/config errors before full training.
- Compare against Darknet-trained weights if mAP is the acceptance criterion.
