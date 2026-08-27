# Data Loading And Split/Transform Workflows

## Load A CSV Of SMILES And Labels

Use `CSVLoader` when a table has one molecule column and one or more task columns.

```python
import deepchem as dc

loader = dc.data.CSVLoader(
    tasks=["activity"],
    feature_field="smiles",
    id_field="compound_id",
    featurizer=dc.feat.CircularFingerprint(size=1024),
)
dataset = loader.create_dataset("assay.csv")
print(dataset.X.shape, dataset.y.shape, dataset.w.shape, dataset.ids[:3])
```

Checklist:
- Make `tasks` exactly match label column names.
- Use `feature_field` for the SMILES column when the column is not named `smiles`.
- Use `id_field` for stable compound identifiers.
- Inspect `dataset.w` after loading; missing labels often become zero weights.

## Load SDF Properties

Use `SDFLoader` when molecules and labels are in an SDF file.

```python
import deepchem as dc

loader = dc.data.SDFLoader(
    tasks=["logS"],
    featurizer=dc.feat.CircularFingerprint(size=1024),
    sanitize=True,
)
dataset = loader.create_dataset("molecules.sdf")
```

Set `sanitize=True` when invalid valence, aromaticity, or malformed chemistry should be caught during loading. Leave it `False` only when the workflow intentionally preserves unsanitized molecules.

## Build From NumPy Arrays

Use `NumpyDataset` for arrays already in memory.

```python
import numpy as np
import deepchem as dc

X = np.asarray([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
y = np.asarray([[1.2], [0.3], [0.8]])
ids = np.asarray(["cmpd-1", "cmpd-2", "cmpd-3"])
dataset = dc.data.NumpyDataset(X=X, y=y, ids=ids)
```

Use `DiskDataset.from_numpy` when the dataset should be persisted or is too large for comfortable in-memory manipulation.

```python
dataset = dc.data.DiskDataset.from_numpy(X, y=y, ids=ids, tasks=["response"])
```

## Split Then Transform

Fit transformers only on the training split to avoid leakage.

```python
import deepchem as dc

splitter = dc.splits.RandomSplitter()
train, valid, test = splitter.train_valid_test_split(dataset, seed=123)

transformers = [dc.trans.NormalizationTransformer(transform_y=True, dataset=train)]
for transformer in transformers:
    train = transformer.transform(train)
    valid = transformer.transform(valid)
    test = transformer.transform(test)
```

For imbalanced classification, use `BalancingTransformer` instead:

```python
balancer = dc.trans.BalancingTransformer(dataset=train)
train = balancer.transform(train)
valid = balancer.transform(valid)
test = balancer.transform(test)
```

## Choose Random Versus Scaffold Splits

Use `RandomSplitter` for:
- Non-molecular data.
- Quick smoke tests.
- Small examples where scaffold grouping would produce empty splits.

Use `ScaffoldSplitter` for:
- Molecular property prediction with SMILES-like molecule ids/features.
- Estimating generalization to new chemical scaffolds.
- Benchmarks that should not put close analogs in both train and test.

Scaffold splits can be uneven on small datasets. Check split sizes before training.

```python
splitter = dc.splits.ScaffoldSplitter()
train, valid, test = splitter.train_valid_test_split(dataset, frac_train=0.8, frac_valid=0.1, frac_test=0.1)
print(len(train), len(valid), len(test))
```

## Use MoleculeNet Without Surprises

MoleculeNet is convenient, but many loaders download raw data and write cache directories.

Safe decision flow:
1. If the user forbids downloads, do not call MoleculeNet unless they provide a populated `data_dir`/`save_dir` cache.
2. If reproducibility matters, set explicit `data_dir` and `save_dir` paths supplied by the user.
3. Use `reload=True` to reuse featurized caches.
4. Use `splitter=None` when the user wants the full dataset without DeepChem splitting.
5. For multitask loaders, pass `tasks=[...]` to restrict labels when supported.

```python
import deepchem as dc

tasks, (train, valid, test), transformers = dc.molnet.load_tox21(
    featurizer="ECFP",
    splitter="scaffold",
    transformers=["balancing"],
    reload=True,
    data_dir="/path/chosen/by/user/raw-cache",
    save_dir="/path/chosen/by/user/featurized-cache",
    tasks=["NR-AR", "SR-p53"],
)
```

When writing reusable public guidance, describe `data_dir` and `save_dir` as user-chosen cache paths; do not hard-code private machine paths.

## Debug A Loader Column Problem

1. Print the CSV/SDF property names before constructing the loader.
2. Ensure every `tasks` entry exists exactly, including case and punctuation.
3. Ensure the molecular feature column is passed as `feature_field` or `smiles_field`.
4. Confirm ids are strings or values that can round-trip safely.
5. Load a 3-row subset first, then scale to the full file.
6. Inspect `dataset.X.shape`, `dataset.y.shape`, `dataset.w.shape`, `dataset.ids[:5]`.

## Keep Scripts Self-Contained

When creating helper scripts for users:
- Generate tiny default input data if no path is provided.
- Accept task, feature, and id column names as CLI arguments.
- Print shapes and split sizes, not entire datasets.
- Avoid implicit MoleculeNet downloads unless a `--allow-download` style flag is explicit.
