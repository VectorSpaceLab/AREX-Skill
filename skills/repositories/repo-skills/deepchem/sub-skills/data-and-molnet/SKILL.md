---
name: data-and-molnet
description: "Load user data into DeepChem datasets, split datasets, apply
  transformers, and use MoleculeNet loaders safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepChem Data And MoleculeNet

Use this sub-skill when the task is about `deepchem.data`, `deepchem.splits`, `deepchem.trans`, or `deepchem.molnet`: loading CSV/SDF/FASTA/image/numpy data, debugging loader columns, creating train/valid/test splits, applying transformers, or choosing MoleculeNet loader options.

Route elsewhere when the user asks for:
- Featurizer internals or molecular representation choices: `../featurization/`.
- Model fitting, metrics, prediction, or evaluation loops: `../model-training/`.
- Docking, protein complexes, PDBBind structure preparation, or structural biology workflows: `../docking-and-structure/`.

## Fast Path

1. Identify the source format: CSV table, SDF properties, FASTA sequences, image files, in-memory arrays, or MoleculeNet.
2. Confirm the task column names, feature column (`smiles` by default for molecular CSV), id column, and whether missing labels should become zero weights.
3. Load into a `dc.data.Dataset` with `CSVLoader`, `SDFLoader`, `NumpyDataset`, or `DiskDataset.from_numpy`.
4. Split with `dc.splits.RandomSplitter()` for generic ML baselines or `dc.splits.ScaffoldSplitter()` for molecular generalization tests.
5. Fit transformers on the training dataset only, then apply the same transformers to valid/test.
6. For MoleculeNet, decide whether network downloads and disk cache writes are acceptable before calling a loader.

## Common APIs

```python
import deepchem as dc

loader = dc.data.CSVLoader(
    tasks=["activity"],
    feature_field="smiles",
    id_field="compound_id",
    featurizer=dc.feat.CircularFingerprint(size=1024),
)
dataset = loader.create_dataset("data.csv")

splitter = dc.splits.ScaffoldSplitter()
train, valid, test = splitter.train_valid_test_split(dataset, seed=123)

transformer = dc.trans.NormalizationTransformer(transform_y=True, dataset=train)
train = transformer.transform(train)
valid = transformer.transform(valid)
test = transformer.transform(test)
```

For detailed parameter notes, see `references/api-reference.md`.
For complete recipes, see `references/workflows.md`.
For column and shape assumptions, see `references/data-formats.md`.
For failure symptoms and fixes, see `references/troubleshooting.md`.

## Bundled Helpers

- `scripts/load_tiny_csv_dataset.py` creates or loads a tiny CSV and converts it to a DeepChem dataset.
- `scripts/split_tiny_dataset.py` builds deterministic tiny splits with `RandomSplitter` or `ScaffoldSplitter`.

Run either helper with `--help` first. They create tiny local demo data by default and do not depend on repository examples.
