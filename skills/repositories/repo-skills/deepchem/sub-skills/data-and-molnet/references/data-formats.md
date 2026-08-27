# Data Format Assumptions

## DeepChem Dataset Fields

DeepChem datasets normally carry four aligned fields:

- `X`: featurized inputs. Shape is commonly `(n_samples, n_features)` for fixed fingerprints, but can be object arrays for graphs, sequences, images, or variable-sized structures.
- `y`: labels. Shape is commonly `(n_samples, n_tasks)`.
- `w`: weights. Shape usually matches `y`; zero weights mark missing or ignored labels.
- `ids`: sample identifiers. Use stable compound ids, SMILES strings, filenames, or sequence ids.

Always check `len(dataset)`, `dataset.X.shape`, `dataset.y.shape`, `dataset.w.shape`, and `dataset.ids[:5]` before splitting or training.

## CSV Tables

A molecular CSV for `CSVLoader` should have:

```text
compound_id,smiles,activity
cmpd-1,CCO,1.2
cmpd-2,c1ccccc1,0.4
```

Recommended mapping:
- `tasks=["activity"]`
- `feature_field="smiles"`
- `id_field="compound_id"`

For multitask data:

```text
compound_id,smiles,NR-AR,SR-p53
cmpd-1,CCO,1,
cmpd-2,c1ccccc1,0,1
```

Use `tasks=["NR-AR", "SR-p53"]`. Missing labels should be expected to affect `dataset.w`; inspect weights before applying balancing or metrics.

## SDF Files

SDF workflows store molecules plus property blocks. `SDFLoader(tasks=[...])` expects each task name to match an SDF property. Ids may come from molecule names or properties depending on the file and loader behavior. If the workflow requires stable ids, verify `dataset.ids` immediately after loading.

Set `sanitize=True` when invalid chemistry should be rejected during parsing. If many molecules fail, load a small subset and inspect RDKit parse errors before running a full featurization job.

## FASTA And Sequence Files

Use sequence loaders when the input is biological sequence data rather than molecules. Preserve sequence headers as ids where possible. Confirm whether the downstream featurizer expects raw strings, one-hot arrays, k-mers, or domain-specific encodings.

## Image Data

Image datasets usually have `X` as arrays with image dimensions and channels. Confirm:
- Channel order expected by the model or featurizer.
- Whether labels come from a separate table or directory structure.
- Whether images are loaded into memory or referenced from disk.

## NumPy Arrays

For `NumpyDataset`, keep arrays aligned by row:

```python
dataset = dc.data.NumpyDataset(X=X, y=y, w=w, ids=ids)
```

Shape conventions:
- Single-task regression/classification labels should be `(n_samples, 1)` or compatible one-dimensional arrays that DeepChem can reshape.
- Multitask labels should be `(n_samples, n_tasks)`.
- Weights should match labels when supplied.
- Ids should have length `n_samples`.

For persistent datasets, use:

```python
dataset = dc.data.DiskDataset.from_numpy(X, y=y, w=w, ids=ids, tasks=tasks)
```

Use a user-chosen `data_dir` if the location matters; otherwise let DeepChem create a temporary dataset directory.

## Split Assumptions

Splitters operate on rows. Molecular splitters may rely on molecule strings in ids or features. Before using `ScaffoldSplitter`, ensure the dataset retains parseable molecules or SMILES-like ids. For tiny datasets, scaffold grouping may produce empty validation or test splits even when fractions are nonzero.

## Transformer Assumptions

- `NormalizationTransformer(transform_y=True, dataset=train)` assumes continuous labels and computes statistics from the provided dataset.
- `BalancingTransformer(dataset=train)` assumes classification-like labels and computes weights from label frequencies.
- Fit on train only; applying a transformer fit on the full dataset leaks validation/test statistics.
- Save or return the transformer objects with the trained model so predictions can be inverse-transformed or interpreted correctly.

## MoleculeNet Return Format

MoleculeNet loaders return:

```python
tasks, datasets, transformers = dc.molnet.load_delaney(...)
```

If `splitter` is not `None`, `datasets` is usually `(train, valid, test)`. If `splitter=None`, it is a one-element tuple containing the full dataset. Always unpack according to the chosen splitter.

MoleculeNet weights are important: missing assay labels are represented through the weight matrix, commonly with zero weights. Do not drop rows solely because some multitask labels are missing unless the user requests it.
