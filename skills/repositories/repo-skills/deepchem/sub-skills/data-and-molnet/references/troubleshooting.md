# Data And MoleculeNet Troubleshooting

## CSV Loader Says A Column Is Missing

Symptoms:
- `KeyError` for a task, id, or feature column.
- Loaded labels are empty or all weights are zero.
- Dataset ids do not match expected compound ids.

Fixes:
- Print `pandas.read_csv(path).columns.tolist()` and compare exactly with `tasks`, `feature_field`, and `id_field`.
- Watch for whitespace, capitalization, duplicate headers, or compressed files read with the wrong delimiter.
- Use `feature_field="your_smiles_column"` when the SMILES column is not named `smiles`.
- Load a tiny subset first and print `dataset.y`, `dataset.w`, and `dataset.ids`.

## Invalid SMILES Or Failed Featurization

Symptoms:
- RDKit parse warnings.
- Feature rows are empty, `None`, or have unexpected shape.
- Fewer usable samples than CSV rows.

Fixes:
- Validate SMILES separately before full featurization.
- Check for salts, mixtures, blank strings, malformed quotes, or non-SMILES identifiers in the feature column.
- Use a small fingerprint featurizer for smoke tests, then switch to the intended featurizer.
- Route detailed featurizer behavior to `../featurization/`.

## SDF Loading Fails Or Drops Molecules

Symptoms:
- RDKit sanitization errors.
- Task properties are missing.
- Molecule ids are not the expected property values.

Fixes:
- Confirm property names in the SDF match `tasks` exactly.
- Try `sanitize=False` to diagnose whether chemistry sanitization is the blocker, or `sanitize=True` to fail early in strict workflows.
- Load a small SDF first and inspect `dataset.ids`, `dataset.y`, and `dataset.w`.

## Transformer Requires A Dataset

Symptoms:
- Normalization statistics are missing or nonsensical.
- Balancing does not change weights as expected.
- Validation/test performance is suspiciously high.

Fixes:
- Construct `NormalizationTransformer(..., dataset=train)` or `BalancingTransformer(dataset=train)` after splitting.
- Fit on train only, then apply the same transformer objects to valid/test.
- Use normalization for regression labels and balancing for classification labels.
- Keep transformers alongside the model for inverse transforms and reproducible inference.

## Split Leakage Or Empty Splits

Symptoms:
- Similar molecules appear in train and test.
- `ScaffoldSplitter` returns tiny or empty valid/test sets.
- Split sizes differ from requested fractions.

Fixes:
- Use `ScaffoldSplitter` for molecular generalization; use `RandomSplitter` only when random row-level evaluation is acceptable.
- Check split sizes immediately with `len(train), len(valid), len(test)`.
- For very small datasets, use larger validation/test fractions, `RandomSplitter`, or explicit user-provided splits.
- For grouped assays or time splits, consider `SpecifiedSplitter` or group-aware splitters instead of random splitting.

## MoleculeNet Downloads Unexpectedly

Symptoms:
- Loader attempts network access.
- Jobs fail offline.
- Cache directories are populated unexpectedly.

Fixes:
- Ask whether downloads are allowed before calling MoleculeNet loaders.
- Pass user-chosen `data_dir` and `save_dir` to control raw and featurized caches.
- Use `reload=True` to reuse existing featurized datasets.
- If downloads are forbidden and no cache exists, load a local CSV/SDF instead of MoleculeNet.

## MoleculeNet Unpacking Is Wrong

Symptoms:
- `ValueError` while unpacking datasets.
- Code expects train/valid/test but receives one dataset.

Fixes:
- With a splitter, unpack `tasks, (train, valid, test), transformers = ...`.
- With `splitter=None`, unpack `tasks, (dataset,), transformers = ...`.
- Print `len(datasets)` before unpacking in generic helper code.

## DiskDataset Directory Problems

Symptoms:
- Dataset shards are missing after cleanup.
- Multiple jobs overwrite each other.
- Large conversions are slow or fill temporary storage.

Fixes:
- Use a user-chosen `data_dir` for `DiskDataset.from_numpy` when persistence matters.
- Avoid reusing the same output directory for different datasets.
- Treat `DiskDataset` directories as part of the dataset; do not move or delete shard files manually unless using DeepChem dataset utilities.
- For small demos, prefer `NumpyDataset` to avoid directory lifecycle issues.

## Optional Backend Warnings

DeepChem may warn that optional Torch, TensorFlow, JAX, or other backend packages are missing. Data loading, fingerprints, simple splitters, and many transformers can still work without those optional backends. Do not install heavyweight backends unless the user’s model or featurizer explicitly requires them.
