# Featurization Troubleshooting

## Invalid SMILES or RDKit Parse Failures

Symptoms:

- Warnings like failed to featurize a datapoint.
- Feature entries are empty arrays with shape `(0,)`.
- Batch output becomes an object array because valid and invalid entries have different shapes.
- Dataset loaders may silently drop invalid rows after featurization.

Actions:

1. Reproduce with a tiny list containing one known-valid SMILES and the suspect SMILES.
2. Inspect each entry, not only the batch shape.
3. Canonicalize or validate SMILES with RDKit before large featurization runs.
4. Keep a map from input index to output feature so dropped or empty entries can be traced.
5. For graph featurizers, remember that single-atom molecules are not valid for `MolGraphConvFeaturizer`.

Example:

```python
features = dc.feat.CircularFingerprint(size=16).featurize(["CCO", "bad_smiles"])
for smiles, feature in zip(["CCO", "bad_smiles"], features):
    print(smiles, type(feature), getattr(feature, "shape", None), len(feature) if hasattr(feature, "__len__") else None)
```

## `None`, Empty, or Object Features

DeepChem featurizers generally catch per-item exceptions and append `np.array([])`. This is convenient for long batches but dangerous if failures are not checked.

Treat these as failed entries:

- `np.ndarray` with `shape == (0,)`.
- `None` where a feature object is expected.
- `dtype=object` batch arrays caused by mixed feature shapes.
- `GraphData` missing required edge features for a model that expects edge attributes.

Actions:

- Filter or repair invalid inputs before splitting into train/test when possible.
- Fail fast in automation if any entry is empty.
- Use the same featurizer settings across all data splits and inference.

## Optional Dependency Warnings

Many DeepChem featurizers are importable only when optional packages are installed. Missing optional torch/tensorflow/jax backends can also produce warnings in a lean inspection environment; these are not necessarily featurizer failures unless the selected featurizer/model requires them.

Common optional dependency cases:

- RDKit: required for molecular featurizers that parse SMILES or use RDKit `Mol` objects.
- Mordred: required for `MordredDescriptors`.
- PubChemPy plus internet access: required for `PubChemFingerprint`.
- Pysam: required for `FASTAFeaturizer` support.
- pymatgen and matminer: required for many material featurizers.
- transformers/tokenizer packages: required for `HuggingFaceFeaturizer` and tokenizer-backed workflows.
- PyTorch Geometric, DGL, or PyTorch: required only when converting `GraphData` to those graph frameworks or training models that depend on them.

Actions:

1. Instantiate the exact featurizer in a tiny smoke script.
2. If import fails, decide whether to install the optional package or choose a featurizer available in the current environment.
3. Do not install heavy ML backends just to inspect vector featurizers such as `CircularFingerprint` or `RDKitDescriptors`.

## Graph Shape Mismatches

Symptoms:

- Downstream graph model complains about missing `edge_attr`, unexpected node feature size, or invalid `edge_index` shape.
- Batching fails because graph objects do not match model assumptions.

Expected `MolGraphConvFeaturizer` shapes:

- `edge_index.shape[0] == 2`.
- `node_features.shape[0] == graph.num_nodes`.
- Default `node_features.shape[1] == 30`.
- `use_chirality=True` changes node feature length to 32.
- `use_partial_charge=True` changes node feature length to 31.
- `use_edges=True` adds `edge_features.shape[1] == 11`; otherwise `edge_features is None`.

Actions:

- If a model expects edge features, instantiate `MolGraphConvFeaturizer(use_edges=True)`.
- If chirality is important, set `use_chirality=True` before generating all splits.
- If partial charges are needed, expect slower featurization and occasional charge-computation failures.
- Validate one graph from each dataset split before training.

## Chirality-Sensitive Tasks

Problems arise when stereochemical SMILES are featurized without chirality-aware settings. For enantiomers or stereoisomers, non-chiral fingerprints/graphs may omit the signal the user expects.

Actions:

- For fixed vectors, use `CircularFingerprint(chiral=True)`.
- For graph models, use `MolGraphConvFeaturizer(use_chirality=True)`.
- Compare two stereochemical SMILES in a tiny smoke run and confirm feature differences or expected graph node feature size.
- Document the chirality setting as part of the experiment configuration.

## Coulomb Matrix and `max_atoms` Problems

Symptoms:

- Shape is not what the downstream model expects.
- Molecules with more atoms than `max_atoms` fail or are truncated/padded unexpectedly by padding utilities.
- Multi-conformer molecules add an extra conformer dimension.

Actions:

1. Choose `max_atoms` from the maximum atom count in the intended dataset, considering whether hydrogens are explicit.
2. Decide whether `remove_hydrogens=True` is appropriate before selecting `max_atoms`.
3. Use `upper_tri=True` when a flattened fixed vector is desired.
4. Inspect a molecule with no conformer and one with explicit conformers to confirm dimensionality.
5. Keep `randomize`, `n_samples`, and `seed` fixed for reproducible experiments.

## RDKit Descriptor Normalization Warnings

`RDKitDescriptors(is_normalized=True)` removes descriptors that lack normalization parameters and logs warnings. BCUT2D descriptors are a common source of missing normalization support.

Actions:

- Check `len(featurizer.reqd_properties)` after construction, not a hard-coded descriptor count.
- Disable unsupported descriptor families with `use_bcut2d=False` when appropriate.
- Avoid combining `labels_only=True` expectations with normalized output; normalization takes precedence.
- Persist the exact descriptor list if downstream code depends on column order.

## FASTA Featurization Issues

Symptoms:

- `FASTAFeaturizer` is unavailable from `deepchem.feat`.
- A FASTA path produces an empty entry or file-read error.
- Output shape surprises users expecting numeric sequence embeddings.

Actions:

- Confirm the optional sequence dependency is installed.
- Pass file paths, not raw FASTA strings.
- Remember the output is sequence names and raw sequence strings, not learned embeddings.
- Convert or tokenize sequences separately if the downstream model needs numeric encodings.

## Material Featurizer Issues

Symptoms:

- `pymatgen` or `matminer` import errors.
- `CGCNNFeaturizer` cannot initialize atom features or neighbor graphs.
- Composition featurizers receive structures, or structure featurizers receive formula strings.

Actions:

- Use composition featurizers for formula strings and structure featurizers for pymatgen structures/dicts.
- Validate one material sample and print the output type/shape.
- For `CGCNNFeaturizer`, inspect `graph.node_features.shape`, `graph.edge_index.shape`, and `graph.edge_features.shape`.
- If network access or cached atom initialization data is unavailable, choose a featurizer that does not need download-time resources.

## Mixed-Validity Batch Diagnosis

For a user report like “some SMILES work but training crashes,” run a small inspection that preserves indexes:

```python
smiles = ["CCO", "bad_smiles", "C1=CC=CC=C1"]
features = dc.feat.MolGraphConvFeaturizer(use_edges=True).featurize(smiles)
for index, (raw, feature) in enumerate(zip(smiles, features)):
    empty = getattr(feature, "shape", None) == (0,)
    print(index, raw, type(feature).__name__, "empty=" + str(empty))
```

Then either repair invalid records or filter them with an explicit audit trail before model training.
