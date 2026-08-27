# SketchCode training workflow

This reference distills SketchCode's legacy training path without requiring runtime access to the source files used during skill creation. Use it to plan safe dataset staging, validation, training, and fine-tuning.

## Before training

1. Put raw training samples in one flat directory. Each sample must have the same stem for both files:
   - `sample_id.png`
   - `sample_id.gui`
2. Validate the directory with the bundled script:

   ```sh
   python sub-skills/training-data/scripts/validate_training_dataset.py DATASET_DIR
   ```

3. Choose a scratch parent directory that can safely receive new sibling split folders. The legacy training path deletes and recreates `training_set` and `validation_set` siblings under the parent of `DATASET_DIR`.
4. Decide whether to train from scratch or fine-tune from an existing model JSON plus weights file.
5. Budget for a long legacy TensorFlow/Keras run. GPU acceleration can help but is not required by the original public workflow.

## Legacy CLI flags

The public training entry point accepts these flags:

| Flag | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--data_input_path` | yes | none | Directory containing paired `.png` and `.gui` files. |
| `--validation_split` | no | `0.2` | Fraction of paired samples copied into validation. The count is `int(split * paired_count)`. |
| `--epochs` | yes | none | Number of training epochs. |
| `--model_output_path` | yes | none | Directory where final model files and training logs are written. Created if missing. |
| `--model_json_file` | no | none | Existing model architecture JSON for fine-tuning. Must be paired with weights. |
| `--model_weights_file` | no | none | Existing Keras weights file for fine-tuning. Must be paired with JSON. |
| `--augment_training_data` | no | `1` | When `1`, applies Keras `ImageDataGenerator` augmentation to training images only. Validation images are not augmented. |

## Training from scratch

Use a scratch data directory and separate model output directory. Start with the bundled wrapper's dry-run plan; it validates pairs, reports the split directories that may be deleted/recreated, and avoids importing TensorFlow/Keras until a real run is requested.

```sh
python sub-skills/training-data/scripts/run_training.py \
  --sketchcode-root "$SKETCHCODE_ROOT" \
  --data-input-path /path/to/scratch/raw_dataset \
  --validation-split 0.2 \
  --epochs 10 \
  --model-output-path /path/to/model_output \
  --augment-training-data 1
```

To actually start training after reviewing the dry-run output, repeat the command with `--run --allow-destructive-split`. The wrapper changes into the SketchCode runtime `src` directory for the real run so the legacy `../vocabulary.vocab` path resolves consistently.

## Fine-tuning from existing JSON and weights

Fine-tuning requires both files. Providing only weights or only JSON is not enough because the legacy code only loads a pretrained model when both optional flags are present.

```sh
python sub-skills/training-data/scripts/run_training.py \
  --sketchcode-root "$SKETCHCODE_ROOT" \
  --data-input-path /path/to/scratch/raw_dataset \
  --validation-split 0.2 \
  --epochs 5 \
  --model-output-path /path/to/fine_tuned_output \
  --model-json-file /path/to/model_json.json \
  --model-weights-file /path/to/weights.h5 \
  --augment-training-data 1
```

Add `--run --allow-destructive-split` only after confirming the dry-run plan.

For in-place fine-tuning requests, do not reuse a parent directory that contains valuable `training_set` or `validation_set` folders. Stage a copy of the raw paired files in a scratch location and write fine-tuned outputs to a new model output directory.

## What training mutates or creates

Given `--data_input_path /workspace/data/raw`, the legacy split code creates sibling directories below `/workspace/data`:

```text
/workspace/data/raw/              # input files are read from here
/workspace/data/training_set/     # deleted if it already exists, then recreated
/workspace/data/validation_set/   # deleted if it already exists, then recreated
```

The split directories receive copied `.png` and `.gui` files. Preprocessing then writes compressed `.npz` feature files into those split directories using the same sample stems.

The model output directory receives:

```text
model_json.json
weights.h5
training_val_losses.csv
weights-epoch-####--val_loss-####--loss-####.h5  # best checkpoints, every 2 epochs in the legacy callback
```

## Validation split behavior

- The legacy dataset loader includes only stems that have both `.gui` and `.png` files.
- It shuffles sample IDs with NumPy before splitting.
- `val_count = int(validation_split * number_of_paired_samples)`.
- The duplicate-layout check hashes whitespace-stripped `.gui` content and appears intended to avoid putting duplicate GUI text into validation. The historical implementation compares hash strings by object identity instead of equality, so duplicate contents may still be treated as unique. Use the bundled validator to identify duplicates before training.

## Augmentation and preprocessing

Training preprocessing converts split PNGs into normalized image arrays and saves them as `.npz` files. When `--augment_training_data 1`, training images pass through Keras `ImageDataGenerator` with small rotation, shift, and zoom ranges before `.npz` writing. Validation images are always resized/thresholded without augmentation.

## Source script decision

The historical training entry point is not copied verbatim because full training can be long-running, requires legacy TensorFlow/Keras/OpenCV imports, and deletes/recreates split directories. This generated skill instead bundles two safer replacements: `scripts/validate_training_dataset.py` for preflight dataset/vocabulary checks and `scripts/run_training.py` as a guarded dry-run-first wrapper that can call the same training classes only after explicit `--run --allow-destructive-split` acknowledgement.
