# Evaluation and export API reference

This reference is a compact contract for the installed MedMNIST 3.0.2 API.
Use the [export recipes](export-recipes.md) for end-to-end commands and
[troubleshooting](troubleshooting.md) when a contract check fails.

## Evaluator and metrics

```python
from medmnist import Evaluator
from medmnist.evaluator import Metrics, getAUC, getACC

Evaluator(flag, split, size=None, root="~/.medmnist")
Evaluator.evaluate(y_score, save_folder=None, run=None)
Evaluator.get_dummy_prediction()
Evaluator.parse_and_evaluate(path, run=None)
getAUC(y_true, y_score, task)
getACC(y_true, y_score, task, threshold=0.5)
Metrics(AUC, ACC)
```

`Evaluator.__init__` accepts a registry flag, one of `train`, `val`, or `test`,
an optional image size, and a root directory. The root must already exist. A
missing root raises `RuntimeError`; an invalid split raises `ValueError`. The
constructor loads only `{flag}.npz` for default/28 or `{flag}_{size}.npz` for a
larger size. `evaluate` asserts that the first score dimension equals the
loaded label count, computes a `Metrics` namedtuple, and optionally serializes
the score matrix. The output directory is not created by `evaluate`.

The evaluator uses `INFO[flag]["task"]`:

- `binary-class`: `y_true` is effectively `(N,)`; scores may be `(N,)` or
  `(N, 2)`. A 2-D binary score uses the last column as the positive score.
- `multi-label, binary-class`: both labels and scores must remain `(N, L)`.
  AUC and ACC are computed independently for each label and averaged.
- `multi-class` and `ordinal-regression`: scores are `(N, C)`, with one column
  per class. AUC is the mean of one-vs-rest ROC AUC values and ACC is the
  accuracy of `argmax(score, axis=-1)`.

All paths eventually call `squeeze()`. Validate the exact dimensions before
calling the low-level functions. Binary/multilabel ACC thresholds scores at
`0.5`; it does not compare scores directly to integer labels. ROC AUC needs
both classes in every binary target. `Metrics` fields are named exactly `AUC`
and `ACC`.

`get_dummy_prediction()` generates random values. Its binary and multilabel
branches follow the label-array shape. Its multiclass branch uses the maximum
observed label as the number of columns in this version, so it should not be
used as a definitive class-count oracle. Use explicit deterministic arrays for
checks and reports.

## Standard evaluation file contract

`Evaluator.evaluate` writes `pd.DataFrame(y_score).to_csv(path, header=None)`
with the normal pandas index. The filename is:

```text
{flag}{size_flag}_{split}_[AUC]{auc:.3f}_[ACC]{acc:.3f}@{run}.csv
```

`size_flag` is empty for `None`/28 and `_size` otherwise. A supplied `run`
value is preserved; when it is omitted, a time value is generated. A standard
file therefore contains an index column followed by one or more score columns,
with no header row.

`parse_and_evaluate` splits the basename on underscores, recognizes an
unsuffixed or sized flag, reads with `index_col=0, header=None`, sorts the index,
and evaluates the matrix. If `run` is absent it requires `@run` in the basename.
It constructs the evaluator using its default root, then writes the evaluated
standard file in the source file's folder and prints the metrics. The CLI
wrapper does not provide a root argument; direct evaluation is the reliable
custom-root route.

## Dataset export methods

The dataset class methods are:

```python
MedMNIST2D.save(folder, postfix="png", write_csv=True)
MedMNIST2D.montage(length=20, replace=False, save_folder=None)
MedMNIST3D.save(folder, postfix="gif", write_csv=True)
MedMNIST3D.montage(length=20, replace=False, save_folder=None)
```

2-D `save` delegates to `utils.save2d`; 3-D `save` delegates to `utils.save3d`
and asserts that the postfix is exactly `gif`. Both create an image folder
named `{flag}{size_flag}` and can write `{flag}{size_flag}.csv`. The utility
uses the split names `TRAIN`, `VALIDATION`, and `TEST` in CSV records and
names files with the split, numeric index, labels, and extension.

`montage` selects `length * length` random indices. Without replacement, the
selection count cannot exceed the dataset length. 2-D returns a PIL image and
saves JPG; 3-D returns a list of PIL frames and saves GIF. The 3-D path asserts
a single channel. See [export-recipes.md](export-recipes.md) for tiny-fixture
and CLI examples.
