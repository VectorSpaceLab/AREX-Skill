---
name: evaluation-and-export
description: "Evaluate MedMNIST predictions and export 2D or 3D datasets safely,
  including metric calculation, standard result filenames, montages, CSV/image
  output, and the Fire CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MedMNIST evaluation and export

Use this skill when the task concerns `Evaluator`, `getAUC`, `getACC`, score
shapes, metric interpretation, standard result CSV names, `parse_and_evaluate`,
`MedMNIST2D/3D.save`, `montage`, PNG/GIF/CSV export, or the public `save` and
`evaluate` CLI commands. This skill is for evaluation and output handling, not
for loading arbitrary datasets or training models.

## Route and safety boundary

1. **First identify the flag, split, task, score shape, and root.** The split
   must be `train`, `val`, or `test`; `y_score.shape[0]` must equal the label
   count. Use `INFO[flag]["task"]` to choose binary, multilabel,
   multiclass, or ordinal handling. For registry and NPZ-loading questions,
   route to the sibling `dataset-loading` skill instead.
2. Use an explicit, already-created `root` for programmatic evaluation. The
   constructor never creates a missing custom root and never downloads unless
   the dataset class is constructed with `download=True`.
3. Keep result files and exports in a new, isolated output directory. The
   evaluator does not create `save_folder`; create it first. Do not use bulk
   download, default-root cleanup, broad development `test()`, or network
   downloads as part of a smoke check.
4. Scores are probabilities/scores, not class labels. Binary and multilabel
   scores are thresholded only for ACC; multiclass and ordinal predictions use
   `argmax`. Preserve row order and do not add a CSV header to an evaluator
   input file.

For a compact API contract, see [references/api-reference.md](references/api-reference.md).
For CLI syntax and network/destructive boundaries, see
[references/cli-reference.md](references/cli-reference.md).
For reproducible evaluation and export procedures, see
[references/export-recipes.md](references/export-recipes.md).
For failures and recovery, see [references/troubleshooting.md](references/troubleshooting.md).
Run the safe local check with
[scripts/medmnist_smoke.py](scripts/medmnist_smoke.py).

## Evaluation procedure

### Direct `Evaluator` use

Use the installed API, with the dataset NPZ already present in `root`:

```python
import numpy as np
from medmnist import Evaluator

evaluator = Evaluator("pneumoniamnist", "test", size=64, root="./data")
y_score = np.asarray(...)                 # N or N x 2 for binary
assert y_score.shape[0] == evaluator.labels.shape[0]
metrics = evaluator.evaluate(y_score, save_folder="./results", run="run1")
print(metrics.AUC, metrics.ACC)
```

`Evaluator(flag, split, size=None, root="~/.medmnist")` maps `None` and `28`
to the unsuffixed NPZ. A non-28 size is written as `flag_size.npz`; the
available 2D sizes are 28/64/128/224 and 3D sizes are 28/64. The root must
exist and contain the exact file. `evaluate` computes a `Metrics(AUC, ACC)`
namedtuple and, when `save_folder` is supplied, writes the score matrix with
pandas using no header and an index column. Pass a stable `run` value when the
filename must be reproducible.

### Shape and metric decision table

| `INFO[flag]["task"]` | Accepted score shape | AUC | ACC |
|---|---|---|---|
| `binary-class` | `(N,)` or `(N, 2)` | ROC one-vs-rest on the positive score; for 2-D input the last column is used | threshold the selected score at `0.5` |
| `multi-label, binary-class` | `(N, L)` | compute ROC AUC independently for each label and average | threshold each label at `0.5`, compute per-label accuracy, then average |
| `multi-class` | `(N, C)` | one-vs-rest AUC for each class column and average | `argmax` over columns |
| `ordinal-regression` | `(N, C)` | same one-vs-rest loop as multiclass | `argmax` over columns |

Labels should be class indices `0..C-1` for multiclass/ordinal and binary
0/1 for binary. Every one-vs-rest target must contain both positive and
negative examples; otherwise scikit-learn cannot define ROC AUC. For
multilabel, retain the 2-D `(N, L)` shape even when inspecting one label.

`getAUC(y_true, y_score, task)` and `getACC(y_true, y_score, task,
threshold=0.5)` are the low-level functions. They call `squeeze()`, so an
unexpected singleton axis can change dimensionality; assert shapes before
calling them. Do not interpret ACC as a probability metric, and do not pass
already-argmaxed class labels in place of scores.

`get_dummy_prediction()` is useful for discovering a rough output shape, but
it is random and is not a reproducible test fixture. In the inspected version,
its multiclass branch derives the column count from `labels.max()`; construct
explicit `(N, C)` scores when all classes must be represented.

### Standard result filenames and round trips

With `metrics = Metrics(AUC, ACC)`, the standard name is:

```text
{flag}{size_flag}_{split}_[AUC]{auc:.3f}_[ACC]{acc:.3f}@{run}.csv
```

`size_flag` is empty for 28/default and `_64`, `_128`, or `_224` for the
corresponding 2-D size (or `_64` for a 3-D size). For example:
`pneumoniamnist_64_test_[AUC]1.000_[ACC]1.000@run1.csv`.
`run=None` uses the current time, so use a string or number for stable output.

`Evaluator.parse_and_evaluate(path, run=None)` parses the flag, optional size,
and split from the underscore-separated filename, reads the CSV with
`index_col=0, header=None`, sorts by that index, evaluates the resulting score
matrix, prints `Metrics(...)`, and writes a standardized evaluated CSV beside
it. If `run` is omitted, the filename must contain `@`. The parser constructs
an evaluator with the default root; direct evaluation with an explicit root is
safer for isolated fixtures. Put parsed inputs in an isolated output directory
because a matching standard name can be rewritten.

## Export and montage procedure

### 2-D

```python
from medmnist import PathMNIST

dataset = PathMNIST(split="test", root="./data", size=28)
dataset.save("./export", postfix="png", write_csv=True)
montage = dataset.montage(length=2, replace=True, save_folder="./export")
```

`MedMNIST2D.save` calls `save2d`, creates `export/{flag}{size_flag}/`, and
writes one image per sample plus `{flag}{size_flag}.csv` when `write_csv=True`.
The default postfix is `png`; the implementation can pass another image
extension accepted by Pillow. Image names are `{SPLIT}{index}_{labels}.{postfix}`
where `SPLIT` is `TRAIN`, `VALIDATION`, or `TEST`. The CSV is append-mode,
has no generated header, and contains split, filename, and label values;
re-running against the same CSV can append duplicates.

`montage(length=20, replace=False, save_folder=None)` randomly selects
`length * length` samples. For a tiny fixture, either use `replace=True` or
ensure the dataset has at least that many samples. A saved 2-D montage is
`{flag}{size_flag}_{split}_montage.jpg`; the method returns a PIL image.
Random selection is not deterministic unless the caller seeds NumPy before
calling it.

### 3-D

```python
from medmnist import OrganMNIST3D

dataset = OrganMNIST3D(split="test", root="./data", size=28)
dataset.save("./export", postfix="gif", write_csv=True)
frames = dataset.montage(length=2, replace=True, save_folder="./export")
```

`MedMNIST3D.save` requires `postfix="gif"`; it emits one GIF per volume and a
CSV under the same naming layout. A 3-D montage returns a list of frames and,
when saved, writes `{flag}{size_flag}_{split}_montage.gif`. The current 3-D
montage path requires a single channel. GIF output requires a nonempty volume
and compatible PIL frames.

## CLI procedure

The package exposes Fire commands. With data already local, use:

```bash
python -m medmnist available
python -m medmnist info --flag=pneumoniamnist
python -m medmnist save --flag=pneumoniamnist --folder=./export --postfix=png --download=False --size=28 --root=./data
python -m medmnist save --flag=organmnist3d --folder=./export --postfix=gif --download=False --size=28 --root=./data
python -m medmnist evaluate --path=./results/pneumoniamnist_test_[AUC]1.000_[ACC]1.000@run1.csv
```

`save` loops over all three splits, so all three corresponding NPZ arrays are
required. `--download=True` is a network operation and is intentionally not
part of a safe smoke test. `evaluate` has only `--path`; its parser resolves
the dataset through the default root rather than exposing a custom-root flag.
For a custom root, use the direct `Evaluator` API (or arrange the data in the
expected default root only with explicit user approval). `available` and
`info` are read-only metadata commands. Do not use `clean` in this skill: it
deletes downloaded `*mnist*.npz` files.

## Verification and return handoff

Run the bundled helper before relying on a new environment:

```bash
python scripts/medmnist_smoke.py --help
python scripts/medmnist_smoke.py
```

A successful run reports deterministic binary, multilabel, and multiclass
`AUC=1.000 ACC=1.000` checks, a `_64/@run` CSV parse round trip in a temporary
root, and 2-D/3-D export checks without network access. For a concise handoff,
report: **files** used or emitted; **evidence** (task, split, root, score
shapes); **checks** and metric values; **difficult cases** (singleton axes,
missing ROC classes, `_64/@run`, tiny montage sampling, 3-D GIF); **gaps** such
as default-root-only parsing or untested optional backends; and **intentional
omissions** (training, bulk downloads, default-root clean, and broad
`test()`).
