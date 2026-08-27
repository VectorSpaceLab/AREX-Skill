# Dataset and metric workflows

## 1. Inspect without network

Start in a clean Python process and never construct a class whose source
constructor downloads missing files. The bundled checker is intentionally
independent of AIX360 imports:

```bash
python sub-skills/datasets-and-metrics/scripts/check_dataset_contract.py --help
python sub-skills/datasets-and-metrics/scripts/check_dataset_contract.py \
  --dataset heloc --data-dir ./data/heloc_data --no-network
```

The checker validates filenames, parseability, required columns, and simple
shape invariants. A missing local file is a clear failure, not a signal to
retry with a downloader. `--json` is useful for CI or an agent handoff.

For a local constructor, validate first and then use an explicit path:

```python
from aix360.datasets import HELOCDataset

heloc = HELOCDataset(dirpath="./data/heloc_data")
raw = heloc.dataframe()
processed = heloc.data()
```

This is safe only after `heloc_dataset.csv` has been verified. The equivalent
classes with fixed filenames are `COMPASDataset` (`compas.csv`),
`MEPSDataset` (`h181.csv`), and `TEDDataset` (`Retention.csv`). Their
`dirpath` means a directory, not the CSV filename itself.

For MNIST/CIFAR/CelebA/e-SNLI, validate the complete local file set first. For
Ford, Sunspots, Climate, Diabetes, CDC, and Fashion-MNIST, the 0.3.0 classes
have no fully local constructor contract: a missing cache can cause network
access (and some also need optional frameworks). Use the checker and stop or
supply the dependencies rather than monkey-patching a download call.

## 2. Preprocess while preserving alignment

Make preprocessing explicit and record it with the model/explanation artifact:

1. Keep a raw copy and identify the target before dropping or mutating columns.
2. Run the dataset's default callback or a callback designed for the exact raw
   schema. Do not feed a preprocessed array into a callback expecting a frame.
3. Capture feature names in the same order as the final model input.
4. Record row filters and sentinel policy (`-7/-8/-9` to zero for HELOC
   default, missing values for `nan_preprocessing`, negative-code filtering in
   MEPS, date parsing and invalid-row filtering in COMPAS).
5. Split after preprocessing with an explicit seed. For HELOC, prefer
   `HELOCDataset.split(random_state=0)` when its one-hot target output is what
   the consuming algorithm expects. For Diabetes, pass `test_size` and
   `random_state` to `load_data`.
6. For image/time-series data, preserve the class output shape. A model that
   expects `(n,28,28,1)` must not receive flattened MNIST vectors; a windowed
   climate/series model must receive its `(n, sequence_length, features)`
   convention.

A useful handoff record includes: source name/version or checksum, local file
layout, preprocessing function, feature list, target encoding, row count before
and after filtering, split rule/seed, normalization rule, and output shapes.

## 3. Evaluate a single explanation safely

The metrics are local and require an already-fitted classifier. Build a dense
coefficient vector in the model's feature order:

```python
import numpy as np
from aix360.metrics import faithfulness_metric, monotonicity_metric

row = np.asarray(row, dtype=float).reshape(-1)
weights = np.zeros(row.size, dtype=float)
# Example only: selected explanation pairs are (feature_index, signed_weight).
for index, weight in selected_pairs:
    weights[int(index)] = float(weight)
base = np.zeros(row.size, dtype=float)  # choose a domain-valid absence value

if not (row.size == weights.size == base.size):
    raise ValueError("x, coefs, and base must share one feature order")
prob = np.asarray(model.predict_proba(row.reshape(1, -1)))
if prob.shape[0] != 1 or prob.ndim != 2:
    raise ValueError("model.predict_proba must return one 2-D row")

faith = faithfulness_metric(model, row, weights, base)
mono = monotonicity_metric(model, row, weights, base)
```

Interpret faithfulness together with the actual perturbed probabilities; a
positive value is not automatically evidence of a useful explanation if the
base value is invalid or the model is extrapolating. Interpret monotonicity as
a finite local ordering check. Aggregate only after handling `nan` faithfulness
scores and recording the number of valid rows.

## 4. Offline fixture smoke check

Use a tiny local CSV/JSON fixture to test path and schema handling, not to claim
benchmark quality. A minimal HELOC fixture has the target
`RiskPerformance` plus numeric feature columns and both `Good` and `Bad`
labels. A minimal TED fixture has one or more feature columns followed by
`Y,E`. A metric fixture can use a tiny sklearn classifier with two classes and a
single dense row.

The bundled checker creates its own in-memory/no-network fixture when invoked
with `--fixture`; it does not call any AIX360 dataset constructor. This catches
regressions in parser behavior without downloading or altering a user's data.

## 5. Acquisition handoff

When a required file is missing, report the exact filename, expected directory,
source owner, and whether a license/form or conversion tool is required:

- HELOC: obtain the FICO challenge file and place the exact CSV after accepting
  its access terms.
- MEPS: obtain the 2015 full-year H181 source under AHRQ terms, then convert to
  `h181.csv` with an approved R/SPSS workflow outside this no-network helper.
- CDC: obtain the NHANES questionnaire XPT files and ensure `xport` is
  installed before conversion.
- e-SNLI/CelebA and other image sources: obtain the source or generated files
  according to their terms; do not silently substitute a different corpus.

Do not execute the full tutorial/notebook downloads or training workflow as a
validation shortcut. Route fitting and explanation generation to the owning
algorithm route after this data handoff is complete.
