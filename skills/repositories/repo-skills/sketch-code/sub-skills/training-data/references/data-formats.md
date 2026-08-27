# SketchCode training data formats

## Raw dataset layout

SketchCode training expects one flat directory containing paired PNG sketches and GUI DSL files. Pairing is by exact stem:

```text
raw_dataset/
  000001.png
  000001.gui
  000002.png
  000002.gui
```

Important behavior:

- Only stems with both `.png` and `.gui` are included by the legacy loader.
- Missing `.png` or missing `.gui` files are silently skipped by the legacy copy step; validate first so missing pairs do not reduce the dataset unexpectedly.
- Lowercase `.png` and `.gui` suffixes are safest because the historical code checks those suffix strings directly.
- The raw input directory should not be the same directory as `training_set` or `validation_set`.

## GUI DSL token stream

The current bundled vocabulary line is:

```text
, { } small-title text quadruple row btn-inactive btn-orange btn-green btn-red double <START> header btn-active <END> single
```

Tokenization facts:

- Token matching is case-sensitive.
- Whitespace is normalized.
- Commas are separated into their own `,` token before tokenization.
- The training loader wraps each `.gui` text as `<START> ... <END>` internally. Raw training `.gui` files usually should contain the layout body, not duplicate start/end markers.
- Braces are vocabulary tokens and should be separated by whitespace in `.gui` files for predictable tokenization.

A minimal token-valid body can look like this:

```text
header { btn-active , btn-inactive } row { single { small-title text } }
```

The validator checks for tokens outside the vocabulary and warns if raw GUI files already contain `<START>` or `<END>`.

## Vocabulary file contract

The historical `Dataset.load_vocab()` reads a single whitespace-separated line from `../vocabulary.vocab`, creates a Keras tokenizer with `filters=''`, `split=' '`, and `lower=False`, then computes `vocab_size = len(tokenizer.word_index) + 1` for mask/padding index zero.

If a custom vocabulary is supplied for validation or a patched training run, it must include at least:

```text
, { } <START> <END>
```

It also must include every token present in the `.gui` files after comma separation and whitespace normalization.

## Image preprocessing output

The legacy image preprocessor does the following for each PNG in a split directory:

1. Reads the image with OpenCV.
2. Converts BGR/RGB image data to grayscale.
3. Applies adaptive thresholding.
4. Stacks the thresholded image into three channels.
5. Resizes the sketch content to `200x200`.
6. Places it into the center of a white `256x256x3` canvas at rows/columns `27:227`.
7. Normalizes pixel values by dividing by `255`.
8. Saves compressed NumPy features as `sample_id.npz` containing an array named `features`.

The expected model image feature shape is:

```text
(256, 256, 3)
```

## Split directory contents

After `ModelUtils.prepare_data_for_training(...)`, the generated split folders contain copied GUI files, copied PNG files, and preprocessed `.npz` files:

```text
training_set/
  000001.png
  000001.gui
  000001.npz
validation_set/
  000002.png
  000002.gui
  000002.npz
```

Training data loading sorts filenames in each split folder, loads `.npz` feature arrays and `.gui` texts independently, and feeds them into the generator. Keep stems consistent and avoid stale `.npz` files from older runs when debugging alignment.

## Duplicate GUI contents

The split code hashes `.gui` text after removing spaces and newlines, apparently to reduce duplicate layout leakage into validation. The historical comparison uses object identity rather than value equality for hashes, so duplicate GUI text may not be filtered reliably. Treat duplicates as a warning before training:

```sh
python sub-skills/training-data/scripts/validate_training_dataset.py DATASET_DIR --strict
```

Use `--strict` when duplicate layout text should block a run instead of only warning.
