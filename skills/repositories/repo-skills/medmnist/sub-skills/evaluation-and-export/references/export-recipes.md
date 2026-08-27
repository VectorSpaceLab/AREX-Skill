# Reproducible evaluation and export recipes

These recipes use local files only. They are intentionally small enough for a
CPU smoke check and do not call `download=True`. For a ready-to-run version,
see [`scripts/medmnist_smoke.py`](../scripts/medmnist_smoke.py).

## 1. Deterministic score fixtures

Use labels that contain both binary classes and scores with unambiguous
ranking. The following fixtures give AUC and ACC of exactly 1.0:

```python
import numpy as np
from medmnist.evaluator import getAUC, getACC

binary_y = np.array([[0], [1], [0], [1]])
binary_score = np.array([0.10, 0.90, 0.20, 0.80])
assert getAUC(binary_y, binary_score, "binary-class") == 1.0
assert getACC(binary_y, binary_score, "binary-class") == 1.0

multilabel_y = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
multilabel_score = np.array([
    [0.10, 0.20], [0.90, 0.80], [0.20, 0.70], [0.80, 0.30]
])
assert getAUC(multilabel_y, multilabel_score,
             "multi-label, binary-class") == 1.0
assert getACC(multilabel_y, multilabel_score,
              "multi-label, binary-class") == 1.0

multiclass_y = np.array([[0], [1], [2], [1]])
multiclass_score = np.array([
    [0.90, 0.05, 0.05], [0.05, 0.90, 0.05],
    [0.05, 0.05, 0.90], [0.05, 0.90, 0.05]
])
assert getAUC(multiclass_y, multiclass_score, "multi-class") == 1.0
assert getACC(multiclass_y, multiclass_score, "multi-class") == 1.0
```

A binary `(N, 2)` score fixture should put the positive score in the last
column because that is the column selected by the implementation. A multilabel
fixture must stay `(N, L)`; extracting one column and passing a 1-D array
changes the contract.

## 2. Local Evaluator output and `_64/@run` round trip

Create an NPZ named for the selected flag in an already-created temporary
root. It must contain the six standard keys. For example, a local
`pneumoniamnist_64.npz` can contain tiny `uint8` images and `(N, 1)` labels for
all three splits. Then:

```python
from medmnist import Evaluator

root = "./fixture-root"
results = "./results"
# os.makedirs(root, exist_ok=True); os.makedirs(results, exist_ok=True)
evaluator = Evaluator("pneumoniamnist", "test", size=64, root=root)
scores = np.array([0.1, 0.9, 0.2, 0.8])
metrics = evaluator.evaluate(scores, save_folder=results, run="smoke")
# -> pneumoniamnist_64_test_[AUC]1.000_[ACC]1.000@smoke.csv
```

The file contains an index column and score values without a header. To parse
it back, call `Evaluator.parse_and_evaluate` only when the evaluator can find
the matching NPZ through its default-root behavior. For an isolated custom
root, keep using the direct evaluator API; a small subclass that injects the
root can exercise the same parser in a test harness. The bundled smoke helper
uses this injection rather than touching the default root.

Use `run="smoke"` or another stable token in tests. If `run=None`, the name
contains a time value and exact path assertions become fragile. Keep the CSV
in a disposable results directory because parsing a standard filename can
rewrite the standardized output beside the source.

## 3. 2-D PNG and CSV export

```python
from medmnist import PathMNIST

dataset = PathMNIST(split="test", root=root, size=28)
dataset.save("./export", postfix="png", write_csv=True)
```

Expected layout for a 2-D flag is:

```text
export/
  pathmnist/
    TEST0_<label>.png
    ...
  pathmnist.csv
```

The exact label suffix depends on the label array. The CSV records are
`TEST,<filename>,<label...>` with no header. Use `write_csv=False` when a
consumer needs only images. The image directory is created by the utility;
choose a fresh export directory to avoid append-mode CSV duplication.

A montage call for a four-sample fixture should use replacement:

```python
np.random.seed(0)
image = dataset.montage(length=2, replace=True, save_folder="./export")
```

The saved montage is a JPG. Without `replace=True`, `length=2` requires at
least four samples.

## 4. 3-D GIF export

For a grayscale 3-D flag, use a tiny array shaped `(N, depth, height, width)`:

```python
from medmnist import OrganMNIST3D

dataset = OrganMNIST3D(split="test", root=root, size=28)
dataset.save("./export3d", postfix="gif", write_csv=True)
frames = dataset.montage(length=2, replace=True, save_folder="./export3d")
```

Expected output is a `{flag}` image folder containing one GIF per volume, a
CSV beside it, and a `{flag}_{split}_montage.gif`. A 3-D save with `png` fails
because the class asserts `postfix == "gif"`; a color 3-D montage fails the
single-channel assertion in the current implementation.

## 5. CLI export with local files

After placing all three split arrays in `root`, use:

```bash
python -m medmnist save --flag=pneumoniamnist --folder=./export \
  --postfix=png --download=False --size=28 --root=./fixture-root
python -m medmnist save --flag=organmnist3d --folder=./export3d \
  --postfix=gif --download=False --size=28 --root=./fixture-root
```

The CLI save loops over all splits and can be much larger than the tiny direct
recipe when pointed at a real dataset. Never pass `--download=True` as an
implicit fallback in a smoke test.
