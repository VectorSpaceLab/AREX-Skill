# Dataset Formats

## Purpose

Read this when you need to generate, inspect, or validate a PFLlib dataset
split tree. The dataset generators all write the same client-oriented layout,
with small variations for image, text, and sensor data.

## Generated tree

A successful generator usually creates:

```text
dataset/<name>/
  config.json
  train/
    0.npz
    1.npz
    ...
  test/
    0.npz
    1.npz
    ...
  rawdata/        # optional; present when the generator downloads source data
```

### `config.json`

The exact keys vary slightly by generator, but the MNIST-style layout records:

- `num_clients`
- `num_classes`
- `non_iid`
- `balance`
- `partition`
- `Size of samples for labels in clients`
- `alpha`
- `batch_size`

The HAR utilities store the client and class counts plus the per-client label
histogram.

### Client `.npz` files

Each `train/<client>.npz` and `test/<client>.npz` file stores a single `data`
entry that round-trips to a Python dict.

Common keys inside that dict:

- `x`: feature array or token sequence
- `y`: label array

The loaders in `system/utils/data_utils.py` convert those payloads into
PyTorch-ready samples:

- image datasets become `(tensor, label)` pairs
- text datasets become `((tokens, lengths), label)` pairs
- Shakespeare becomes `(token_ids, label)` pairs
- HAR becomes sensor-window tensors plus labels after the HAR preprocessing
  helpers reshape the raw signals

## Split rules and defaults

The helper functions in `dataset/utils/dataset_utils.py` and `HAR_utils.py`
use 75% training / 25% testing by default. The label-skew helper also uses a
Dirichlet `alpha` of `0.1` for practical non-IID splits unless a generator
changes it.

## Validation checklist

A valid dataset tree should satisfy all of the following:

- `config.json` exists.
- `train/` and `test/` exist.
- The number of client files matches the recorded `num_clients`.
- The client indices are consecutive or at least complete for the expected
  client count.
- A sample `.npz` file contains a `data` object with `x` and `y`.
- The declared class count matches the dataset family.

## Notes by modality

### Image datasets

- MNIST, Fashion-MNIST, CIFAR-10, CIFAR-100, Tiny-ImageNet, and similar
  generators work with numeric arrays or image tensors.
- The helper launcher may download source data on first use unless the raw data
  already exists.

### Text datasets

- AG News and Sogou News require `torchtext` and the tokenization helpers in
  `dataset/utils/language_utils.py`.
- Text payloads store token IDs and sequence lengths so the model can pack and
  pad batches correctly.

### Feature-shift datasets

- Amazon Review and Digit5 rely on downloaded source archives and sparse or
  preprocessed numeric features.
- Their output layout still follows the same `config.json` / `train/` / `test/`
  pattern.

### Real-world sensor datasets

- HAR and PAMAP2 use sensor-window preprocessing and shape transforms from the
  HAR utility helpers.
- These datasets are good candidates for layout validation after raw download
  and split generation.
