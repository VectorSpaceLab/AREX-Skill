# Featurizer API Reference

Import featurizers from `deepchem.feat` unless a lower-level module is needed for extension work.

## Base Contracts

### `Featurizer.featurize(datapoints, log_every_n=1000, **kwargs)`

- Converts `datapoints` to a list and calls `_featurize()` for each item.
- Returns `np.asarray(features)`.
- On per-item exception, logs a warning and appends `np.array([])`.
- `featurizer(datapoints)` calls `featurize(datapoints)`.

### `MolecularFeaturizer.featurize(datapoints, log_every_n=1000, **kwargs)`

- Accepts a single SMILES string, a single RDKit `Mol`, or an iterable of SMILES/Mol objects.
- Converts SMILES to RDKit molecules and canonical atom order by default.
- If `use_original_atoms_order=True` is supported and set, preserves original atom order after SMILES parsing.
- On invalid SMILES or featurizer failure, appends an empty array and logs the molecule/failure message.
- Returns a normal numpy array when output shapes are uniform, otherwise an object array.

### Other Base Families

- `MaterialStructureFeaturizer`: accepts pymatgen `Structure` objects or compatible structure dicts; requires `pymatgen` and sometimes `matminer`.
- `MaterialCompositionFeaturizer`: accepts composition strings and converts them with pymatgen `Composition`.
- `PolymerFeaturizer`: accepts polymer string representations; invalid entries become empty arrays.
- `ComplexFeaturizer`: accepts ligand/protein filename tuples; failed entries are replaced by a dummy successful-shape value when possible.

## Common Featurizer Signatures and Outputs

### `CircularFingerprint`

Signature:

```python
dc.feat.CircularFingerprint(
    radius=2,
    size=2048,
    chiral=False,
    bonds=True,
    features=False,
    sparse=False,
    smiles=False,
    is_counts_based=False,
)
```

Output:

- Default: one dense numpy vector per molecule with shape `(size,)` and binary bit values.
- `is_counts_based=True`: dense vector `(size,)` with counts that can exceed 1.
- `sparse=True`: dict per molecule mapping fragment identifiers to counts.
- `sparse=True, smiles=True`: dict values contain `count` and fragment `smiles`.

Validation:

```python
features = dc.feat.CircularFingerprint(size=16).featurize(["CCO"])
assert features.shape == (1, 16)
```

### `MolGraphConvFeaturizer`

Signature:

```python
dc.feat.MolGraphConvFeaturizer(
    use_edges=False,
    use_chirality=False,
    use_partial_charge=False,
)
```

Output:

- One `dc.feat.GraphData` object per successful molecule.
- Default node feature length: 30.
- `use_chirality=True`: node feature length 32.
- `use_partial_charge=True`: node feature length 31 and computes Gasteiger charges when absent.
- `use_edges=True`: adds edge feature length 11.
- Requires molecules with more than one atom; single-atom molecules fail for this featurizer.

Validation:

```python
graph = dc.feat.MolGraphConvFeaturizer(use_edges=True).featurize(["CCO"])[0]
assert graph.node_features.shape[0] == graph.num_nodes
assert graph.edge_index.shape[0] == 2
assert graph.edge_features is None or graph.edge_features.shape[0] == graph.edge_index.shape[1]
```

### `GraphData`

Constructor:

```python
dc.feat.GraphData(node_features, edge_index, edge_features=None, node_pos_features=None, **kwargs)
```

Required shapes:

- `node_features`: numpy array `[num_nodes, num_node_features]`.
- `edge_index`: integer numpy array `[2, num_edges]`.
- `edge_features`: optional numpy array `[num_edges, num_edge_features]`.
- `node_pos_features`: optional numpy array `[num_nodes, num_dimensions]`.

Useful attributes:

- `num_nodes`, `num_node_features`, `num_edges`, and `num_edge_features` when edge features exist.
- `to_pyg_graph()` requires PyTorch Geometric.
- `to_dgl_graph()` requires DGL.
- `numpy_to_torch()` requires PyTorch.

### `RDKitDescriptors`

Signature:

```python
dc.feat.RDKitDescriptors(
    descriptors=[],
    is_normalized=False,
    use_fragment=True,
    ipc_avg=True,
    use_bcut2d=True,
    labels_only=False,
)
```

Output:

- Dense vector per molecule with length `len(featurizer.reqd_properties)`.
- Empty `descriptors` means use RDKit descriptor list filtered by `use_fragment` and `use_bcut2d`.
- `is_normalized=True` applies built-in CDF normalization and removes descriptors without normalization parameters.
- `labels_only=True` converts nonzero descriptor values to 1, but normalized mode takes precedence.

Validation:

```python
featurizer = dc.feat.RDKitDescriptors(use_bcut2d=False)
features = featurizer.featurize(["CCO"])
assert features.shape == (1, len(featurizer.reqd_properties))
```

### `MordredDescriptors`

Signature:

```python
dc.feat.MordredDescriptors(ignore_3D=True)
```

Output:

- Dense vector per molecule.
- With `ignore_3D=True`, common output length is 1613.
- With `ignore_3D=False`, common output length is 1826.
- Requires optional `mordred`; missing/error descriptor values are converted to `0.0`.

### `PubChemFingerprint`

Signature:

```python
dc.feat.PubChemFingerprint()
```

Output:

- Dense vector length 881.
- Requires optional `pubchempy`, RDKit, and internet access to PubChem.

### `CoulombMatrix`

Signature:

```python
dc.feat.CoulombMatrix(
    max_atoms,
    remove_hydrogens=False,
    randomize=False,
    upper_tri=False,
    n_samples=1,
    seed=None,
)
```

Output:

- Default single-conformer output per molecule: `(max_atoms, max_atoms)`, batched as `(batch, max_atoms, max_atoms)`.
- Multi-conformer molecules: `(num_confs, max_atoms, max_atoms)` per molecule.
- `upper_tri=True`: flattened upper triangle length `max_atoms * (max_atoms + 1) // 2`.
- `randomize=True`: produces `n_samples` randomized matrices per conformer.
- If no conformer is present, DeepChem may add hydrogens and embed one.

### `CoulombMatrixEig`

Signature:

```python
dc.feat.CoulombMatrixEig(max_atoms, remove_hydrogens=False, randomize=False, n_samples=1, seed=None)
```

Output:

- Eigenvalue vector length `max_atoms` for a single conformer.
- Multi-conformer output includes a conformer dimension.

### `FASTAFeaturizer`

Signature:

```python
dc.feat.FASTAFeaturizer()
```

Output:

- Accepts FASTA file paths.
- Per FASTA file, returns an object array of rows `[sequence_name, sequence]`.
- A file with three sequences yields inner shape `(3, 2)` and a one-file batch shape like `(1, 3, 2)`.
- Requires optional sequence dependency support; if unavailable, the class may not be imported into `deepchem.feat`.

### Material Featurizers

- `ElementPropertyFingerprint(data_source='matminer')`: composition strings to fixed property vector; material dependencies required.
- `SineCoulombMatrix(max_atoms=100, flatten=True)`: pymatgen structures to eigenvalue vector `(max_atoms,)` when flattened or padded matrix when not.
- `CGCNNFeaturizer(radius=8.0, max_neighbors=12, step=0.2)`: pymatgen structures to `GraphData`; node feature length is commonly 92 and edge feature length depends on `radius / step + 1`.
- `ElemNetFeaturizer()`: composition strings to element fraction vector.

## Shape Inspection Utilities

Use a generic shape summarizer before training:

```python
def describe_feature(x):
    if hasattr(x, "shape"):
        return {"type": type(x).__name__, "shape": tuple(x.shape)}
    if hasattr(x, "node_features") and hasattr(x, "edge_index"):
        return {
            "type": type(x).__name__,
            "node_features": tuple(x.node_features.shape),
            "edge_index": tuple(x.edge_index.shape),
            "edge_features": None if x.edge_features is None else tuple(x.edge_features.shape),
        }
    return {"type": type(x).__name__}
```

The bundled `scripts/inspect_featurizer_outputs.py` automates this for common SMILES featurizers and optional FASTA files.
