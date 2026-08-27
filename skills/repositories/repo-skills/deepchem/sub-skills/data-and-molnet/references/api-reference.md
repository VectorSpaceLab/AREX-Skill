# Data, Splitter, Transformer, And MoleculeNet API Notes

## Dataset Containers

- `dc.data.NumpyDataset(X, y=None, w=None, ids=None, n_tasks=1)` stores arrays in memory and is best for small/medium data or already-featurized examples.
- `dc.data.DiskDataset.from_numpy(X, y=None, w=None, ids=None, tasks=None, data_dir=None)` writes a dataset directory for larger data or workflows that need persistence.
- Dataset fields are normally accessed as `dataset.X`, `dataset.y`, `dataset.w`, and `dataset.ids`; `len(dataset)` returns sample count.
- `dataset.to_dataframe()` is useful for quick inspection, but avoid it for very large `DiskDataset` objects.

## CSV Loader

`dc.data.CSVLoader(tasks, featurizer, feature_field=None, id_field=None, smiles_field=None, log_every_n=1000)` creates a dataset from CSV rows.

Key parameters:
- `tasks`: list of label column names. For multitask data, pass all task columns in the desired order.
- `feature_field`: input column to featurize. For molecular CSV data, this is usually the SMILES column such as `"smiles"`.
- `smiles_field`: older molecular-column name accepted by DeepChem. Prefer `feature_field` in new code unless preserving legacy behavior.
- `id_field`: stable identifier column. If omitted, DeepChem generates ids or uses available defaults depending on loader behavior.
- `featurizer`: a DeepChem featurizer object, such as `dc.feat.CircularFingerprint(size=1024)`.
- `create_dataset(input_files)`: accepts a CSV path or list of paths and returns a DeepChem dataset, typically a `DiskDataset`.

Typical use:

```python
loader = dc.data.CSVLoader(
    tasks=["pIC50"],
    feature_field="canonical_smiles",
    id_field="compound_id",
    featurizer=dc.feat.CircularFingerprint(size=1024),
)
dataset = loader.create_dataset("assay.csv")
```

## SDF Loader

`dc.data.SDFLoader(tasks, featurizer, sanitize=False, log_every_n=1000)` reads molecules and properties from SDF files.

Key points:
- `tasks` must match SDF property names that contain labels.
- `sanitize=False` is the default; set `sanitize=True` when RDKit sanitization is wanted and invalid chemistry should fail or be cleaned early.
- SDF loading is useful when labels and ids are stored as molecule properties rather than CSV columns.

## FASTA, Image, And Other Loaders

- `dc.data.FASTALoader` creates sequence datasets from FASTA files and is appropriate for biological sequence features.
- `dc.data.ImageLoader` creates image datasets from image files or image arrays.
- JSON, FASTQ, SAM/BAM/CRAM, and specialized loaders exist, but verify optional dependencies before recommending them.
- If the user already has NumPy arrays, prefer `NumpyDataset` or `DiskDataset.from_numpy` over writing temporary CSV files.

## Splitters

Common splitter methods return dataset objects, not raw indices:

```python
splitter = dc.splits.RandomSplitter()
train, valid, test = splitter.train_valid_test_split(dataset, seed=123)
train, test = splitter.train_test_split(dataset, seed=123)
folds = splitter.k_fold_split(dataset, k=5)
```

- `RandomSplitter()` is the baseline for generic datasets and quick debugging.
- `ScaffoldSplitter()` groups molecules by Bemis-Murcko scaffold to evaluate chemical scaffold generalization. Use it only when dataset ids or features can be interpreted as molecules/SMILES by the splitter.
- `IndexSplitter()` preserves row order and is useful for deterministic demos, not unbiased evaluation.
- `RandomStratifiedSplitter()` and `SingletaskStratifiedSplitter()` are better when label balance matters.
- `SpecifiedSplitter` is appropriate when the input file has explicit split assignments.

## Transformers

`dc.trans.NormalizationTransformer(transform_X=False, transform_y=False, transform_w=False, dataset=None, transform_gradients=False, move_mean=True)` computes normalization statistics from `dataset`.

Use it for regression labels:

```python
normalizer = dc.trans.NormalizationTransformer(transform_y=True, dataset=train)
train = normalizer.transform(train)
valid = normalizer.transform(valid)
test = normalizer.transform(test)
```

`dc.trans.BalancingTransformer(dataset)` computes class weights from a classification dataset.

Use it for imbalanced classification labels:

```python
balancer = dc.trans.BalancingTransformer(dataset=train)
train = balancer.transform(train)
valid = balancer.transform(valid)
test = balancer.transform(test)
```

Rules:
- Fit transformer statistics on training data only.
- Apply the same fitted transformer objects to validation and test data.
- Keep the transformer list for inverse transforms or model evaluation pipelines.
- Use normalization for continuous regression targets; use balancing for binary or multiclass classification weights.

## MoleculeNet Loaders

MoleculeNet loaders return `(tasks, datasets, transformers)`.

```python
tasks, (train, valid, test), transformers = dc.molnet.load_delaney(
    featurizer="ECFP",
    splitter="scaffold",
    transformers=["normalization"],
    reload=True,
)
```

Important loader parameters:
- `featurizer`: string shortcut such as `"ECFP"` or a featurizer object.
- `splitter`: string shortcut such as `"scaffold"`, a splitter object, or `None`. If `None`, datasets is a one-element tuple containing the full dataset.
- `transformers`: strings such as `"normalization"` or `"balancing"`, or transformer generator objects.
- `reload`: when `True`, DeepChem caches featurized datasets and reloads them on later calls.
- `data_dir`: raw dataset download/cache directory.
- `save_dir`: featurized dataset cache directory.
- `tasks`: supported by selected multitask loaders such as `load_tox21` to restrict task columns.

Examples:

```python
# Regression benchmark: Delaney solubility.
tasks, (train, valid, test), transformers = dc.molnet.load_delaney(
    featurizer="ECFP", splitter="scaffold", transformers=["normalization"])

# Multitask toxicity with selected tasks and class balancing.
tasks, (train, valid, test), transformers = dc.molnet.load_tox21(
    featurizer="ECFP",
    splitter="scaffold",
    transformers=["balancing"],
    tasks=["NR-AR", "SR-p53"],
)
```

Network/cache warning: many MoleculeNet loaders download raw data if it is absent. For offline or reproducible tasks, ask the user for existing `data_dir`/`save_dir`, set `reload=True` to reuse caches, or avoid MoleculeNet loaders and load local files directly.
