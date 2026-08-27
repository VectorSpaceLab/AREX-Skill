# Evaluation and export troubleshooting

Use the smallest local fixture first. The bundled
[`medmnist_smoke.py`](../scripts/medmnist_smoke.py) is deterministic, uses a
temporary root, and never downloads or cleans a default root.

## Evaluator setup failures

### `RuntimeError: Failed to setup the default root directory`

The supplied root is missing or is not a directory visible to the process.
Create an explicit local directory and pass it:

```python
from pathlib import Path
from medmnist import Evaluator

root = Path("./fixture-root")
root.mkdir(parents=True, exist_ok=True)
evaluator = Evaluator("pneumoniamnist", "test", root=str(root))
```

The constructor does not create a custom root. Do not solve this by enabling a
network download unless data acquisition was explicitly requested.

### `Dataset not found` or a NumPy file error

Check the exact filename: default/28 is `flag.npz`; a larger size is
`flag_64.npz`, `flag_128.npz`, or `flag_224.npz` as supported by that dataset.
For evaluation, the selected split must have a `*_labels` array. For export,
the NPZ must also have matching `*_images` arrays for `train`, `val`, and
`test`. Confirm `images.shape[0] == labels.shape[0]` for every split.

### `ValueError` for the split

Only `train`, `val`, and `test` are accepted. Use the registry's exact flag and
lowercase split name. This skill does not cover creating a new registry entry.

## Score shape and metric failures

### Assertion or sample-count mismatch

`Evaluator.evaluate` asserts `y_score.shape[0] == evaluator.labels.shape[0]`.
Print both shapes before evaluating:

```python
print("labels:", evaluator.labels.shape, "scores:", y_score.shape)
assert y_score.ndim in (1, 2)
assert y_score.shape[0] == evaluator.labels.shape[0]
```

Do not include sample IDs as an extra score row. A standard evaluator CSV has
an index column on disk, but `parse_and_evaluate` removes it with
`index_col=0`; a hand-written CSV should follow the same layout.

### `IndexError: tuple index out of range` in multilabel code

The multilabel branch requires `(N, L)` labels and scores. Do not squeeze a
single selected label before calling the API. Confirm that `y_true.ndim == 2`
and `y_score.ndim == 2`, and that both have the same `N` and `L`.

### ROC AUC error about one class or a continuous format

Every binary target passed to `roc_auc_score` must contain both 0 and 1. This
applies to the binary fixture, every multilabel column, and every one-vs-rest
class in multiclass/ordinal evaluation. Use a larger or deliberately balanced
synthetic fixture; do not fabricate an AUC from a single-class split.

### ACC is unexpectedly low

Check what task the registry reports. Binary and multilabel scores use a
strict `> 0.5` threshold; multiclass and ordinal use `argmax`, regardless of
whether scores sum to one. For binary two-column scores, the last column is
used as the positive score. Passing class IDs instead of score values can make
both AUC and ACC invalid or misleading.

### `get_dummy_prediction()` has an unexpected multiclass width

It is random and its current multiclass implementation derives the number of
columns from `labels.max()`. For a reliable test, determine `C` from the
registry/task or model output and construct an explicit `(N, C)` array. Make
sure labels include every class needed for one-vs-rest AUC.

## Filename and parser failures

### `parse_and_evaluate` cannot infer flag, size, or split

Use an underscore-separated basename such as:

```text
pneumoniamnist_64_test_anything@smoke.csv
```

The parser recognizes the first token as the flag, an optional numeric size,
and a split token beginning with `train`, `val`, or `test`. Keep the standard
name emitted by `Evaluator.evaluate` rather than inventing punctuation.

### `run` assertion or an overwritten file

When `run=None`, the basename must contain `@run`. Pass an explicit `run` to
make tests stable. Parsing writes another standardized file in the same folder
and can target the same path when the input is already standardized. Use a
fresh copy or disposable results folder if preserving the input matters.

### Custom root works directly but CLI `evaluate` fails

This is expected from the public wrapper: `evaluate(path)` delegates to a
class method that constructs `Evaluator` without a custom root. Use:

```python
Evaluator("pneumoniamnist", "test", size=64, root="./fixture-root")\
    .evaluate(scores, save_folder="./results", run="smoke")
```

Do not delete or repopulate a default root merely to make a local smoke test
pass. If a CLI-only integration is mandatory, document and obtain approval
for the exact default-root data placement first.

## Export and montage failures

### Images are present but the CSV is duplicated or malformed

The utility opens the CSV in append mode and emits records without a header.
Use a new output folder or remove only a user-approved fixture output before
rerunning. Do not use the package-wide `clean` command.

### 2-D image save fails on a postfix

The 2-D path delegates extension handling to Pillow. Use `png` for the
portable default. Ensure image arrays are valid 2-D grayscale or 3-D RGB
`uint8` arrays. The `as_rgb` dataset option affects item retrieval; `save`
operates on the stored image array.

### Montage asks for too many samples

The default `length=20` selects 400 samples without replacement. For tiny
fixtures use `length=2, replace=True`, and seed NumPy if reproducibility is
needed. A montage is randomly selected and should not be treated as a fixed
sample audit unless the seed and fixture are recorded.

### 3-D save or montage fails

`MedMNIST3D.save` accepts only `postfix="gif"`. The montage path requires
single-channel data and returns frames, not one PIL image. Verify the volume
shape is `(N, D, H, W)`, the array is nonempty, and Pillow can save each frame.
A GIF montage is written only when `save_folder` is supplied.

## CLI boundaries

`save --download=True` can access the network and write large exports;
`download` can fetch many datasets; `clean` deletes downloaded NPZ files; and
the development `test()` command exercises broad operations. Keep all four out
of unattended smoke checks. Prefer `available`, `info`, direct evaluation,
and the bundled synthetic helper for safe diagnosis.
