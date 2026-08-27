# pix2code Data Formats

## Purpose

Read this when validating or preparing pix2code training data.

## Directory shapes

### Raw paired screenshot dataset

```text
dataset_root/
  sample_001.gui
  sample_001.png
  sample_002.gui
  sample_002.png
```

### Preprocessed feature dataset

```text
dataset_root/
  sample_001.gui
  sample_001.npz   # contains a `features` array
```

The preprocessing script stores each image as a compressed NumPy archive named after the sample basename.

## Pairing rules

- A `.gui` file should have a sibling `.png` or `.npz` file with the same basename.
- The dataset loader walks one directory and skips unpaired entries.
- The loader uses `.png` when both image forms exist; otherwise it uses `.npz`.
- The validation helper should fail fast if the directory has unmatched basenames or no usable pairs.

## Tokenization rules

During dataset loading, each line of the `.gui` file is transformed by:

- replacing commas with explicit comma tokens,
- replacing newline characters with explicit newline tokens,
- prepending `<START>`,
- appending `<END>`.

The model then builds context windows of length `CONTEXT_LENGTH = 48` from the token sequence.

## Array shapes

- Images are resized to `IMAGE_SIZE = 256` before being stored or consumed.
- The model consumes either raw image arrays or preprocessed feature arrays depending on the training mode.
- `meta_dataset.npy` stores `[input_shape, output_size, dataset_size]`.

## Validation commands

Use the bundled helper instead of the original checkout scripts when checking a directory:

```bash
python sub-skills/data-and-training/scripts/prepare_pix2code_dataset.py validate --input /path/to/dataset
```

For a small synthetic fixture, split and convert the same directory to prove the layout is consistent.
