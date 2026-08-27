# API Reference: Fingerprints, Similarity, Clustering, MCS, and Graph Helpers

This reference distills the datamol APIs owned by the `fingerprints-similarity` sub-skill. Inputs can be RDKit `Mol` objects unless a signature explicitly accepts SMILES strings too. Prefer passing cleaned, valid molecules for production workflows; use the sibling molecule-preparation skill for parsing and cleanup before feature generation.

## Fingerprints

### `dm.to_fp`

Signature from source:

```python
dm.to_fp(mol, as_array=True, fp_type="ecfp", fold_size=None, **fp_args)
```

- `mol`: SMILES string or RDKit `Mol`. Invalid strings or `None` raise `ValueError`.
- `as_array=True`: returns a NumPy array for normal fingerprints.
- `as_array=False`: returns the native RDKit vector where possible; useful for clustering functions that call RDKit Tanimoto directly.
- `fp_type="ecfp"`: default Morgan ECFP-like fingerprint with datamol defaults of `radius=3` and `fpSize=2048`.
- `fold_size`: when set, folds sparse/count vectors to the requested length and returns a NumPy array regardless of `as_array`.
- `**fp_args`: forwarded to the underlying RDKit generator/function after datamol fills its defaults.

Common choices:

| `fp_type` | Default size | Notes |
| --- | ---: | --- |
| `ecfp` | 2048 | Default binary Morgan fingerprint, radius 3. |
| `fcfp` | 2048 | Feature Morgan fingerprint. |
| `rdkit` | 2048 | RDKit path fingerprint. |
| `maccs` | 167 | MACCS keys. Useful for interpretable coarse screens. |
| `pattern` | 2048 | RDKit pattern fingerprint. |
| `layered` | 2048 | RDKit layered fingerprint. |
| `topological` | 2048 | Topological torsion bit fingerprint. |
| `atompair` | 2048 | Atom-pair bit fingerprint. |
| `erg` | 315 | ErG pharmacophore-like vector. |
| `estate` | 79 | E-State vector. |
| `*-count` | Usually 512 or 2048 | Count variants for supported Avalon, Morgan, topological, atom-pair, and RDKit fingerprints. |

Use `dm.list_supported_fingerprints()` to get the active mapping. Evidence tests expect these keys: `atompair`, `atompair-count`, `avalon-count`, `ecfp`, `fcfp`, `ecfp-count`, `erg`, `estate`, `fcfp-count`, `layered`, `maccs`, `pattern`, `rdkit`, `topological`, `topological-count`, and `rdkit-count`.

### `dm.fp_to_array`

Signature from source:

```python
dm.fp_to_array(fp)
```

- Converts supported RDKit fingerprint vectors or an existing NumPy array into a NumPy array.
- Supports sparse bit vectors, explicit bit vectors, and sparse integer count vectors.
- Raises `ValueError` for unsupported vector classes.
- Count vectors return integer counts; bit vectors return 0/1 values.

### `dm.fold_count_fp`

Signature from source:

```python
dm.fold_count_fp(fp, dim=1024, binary=False)
```

- Folds a sparse bit or sparse count fingerprint to `dim` using modulo indexing.
- Returns an integer NumPy array of length `dim`.
- With `binary=True`, clips folded counts to 0/1.
- Best used for count/sparse vectors; regular dense arrays are not accepted by this function.

## Descriptors

### `dm.descriptors.compute_many_descriptors`

Signature from source:

```python
dm.descriptors.compute_many_descriptors(mol, properties_fn=None, add_properties=True)
```

- Returns a `dict` of molecular descriptor names to values for one molecule.
- `properties_fn=None` uses datamol's default descriptor set, including molecular weight, Fsp3, Lipinski HBA/HBD, ring and hetero-atom counts, TPSA, QED, cLogP, SAS, and ring-class counts.
- `properties_fn` maps output names to callables or RDKit descriptor function names as strings.
- If `add_properties=True`, custom entries are added to the defaults; if `False`, only custom entries are computed.

### `dm.descriptors.batch_compute_many_descriptors`

Signature from source:

```python
dm.descriptors.batch_compute_many_descriptors(
    mols,
    properties_fn=None,
    add_properties=True,
    n_jobs=1,
    batch_size=None,
    progress=False,
    progress_leave=True,
)
```

- Returns a pandas `DataFrame` with one row per molecule and one column per descriptor.
- Uses datamol parallelization. Keep `n_jobs=1` or `None` for tiny/debug runs; use `-1` only after the workflow is stable.
- `batch_size` controls chunking through the datamol job helper.

## Distances

### `dm.pdist`

Signature from source:

```python
dm.pdist(mols, n_jobs=1, squareform=True, **fp_args)
```

- Computes all-vs-all Tanimoto/Jaccard distances after generating fingerprints with `dm.to_fp(as_array=True, **fp_args)`.
- `mols`: list of SMILES strings or RDKit `Mol` objects.
- `squareform=True`: returns an `(n, n)` symmetric NumPy matrix with zeros on the diagonal.
- `squareform=False`: returns a condensed vector of length `n * (n - 1) / 2`.
- `**fp_args`: pass `fp_type`, `fold_size`, `radius`, `fpSize`, and other fingerprint options.

### `dm.cdist`

Signature from source:

```python
dm.cdist(
    mols1,
    mols2,
    n_jobs=1,
    distances_chunk=False,
    distances_chunk_memory=1024,
    distances_n_jobs=-1,
    **fp_args,
)
```

- Computes cross distances from every molecule in `mols1` to every molecule in `mols2`.
- Returns a NumPy matrix shaped `(len(mols1), len(mols2))`.
- Converts fingerprint arrays to boolean before SciPy/sklearn Jaccard distance calculation.
- `distances_chunk=True` uses sklearn chunking for large libraries; tune `distances_chunk_memory` in MB and `distances_n_jobs` for the distance calculation separately from fingerprint generation.

## Clustering and Picking

### `dm.cluster_mols`

Signature from source:

```python
dm.cluster_mols(mols, cutoff=0.2, feature_fn=None, n_jobs=1)
```

- Clusters molecules with RDKit Butina using Tanimoto distances over features.
- Default `feature_fn` is equivalent to `functools.partial(dm.to_fp, as_array=False)`.
- Returns `(cluster_indices, cluster_mols)`.
- `cluster_indices`: tuple-like clusters of integer input indices.
- `cluster_mols`: parallel list of molecule groups; singleton clusters are normalized to one-element lists.
- Larger `cutoff` allows more distant molecules into the same cluster; smaller `cutoff` is stricter.

### `dm.pick_diverse`

Signature from source:

```python
dm.pick_diverse(mols, npick, initial_picks=None, feature_fn=None, dist_fn=None, seed=42, n_jobs=1)
```

- Uses RDKit `MaxMinPicker` to select `npick` diverse molecules.
- Returns `(picked_indices, picked_mols)` where `picked_indices` is a NumPy array.
- `initial_picks` are forced into the picked set and count toward `npick`.
- Use a fixed `seed` for reproducible picks.
- Override `feature_fn` or `dist_fn` only when you need non-default features or a precomputed distance function.

### `dm.pick_centroids`

Signature from source:

```python
dm.pick_centroids(
    mols,
    npick=0,
    initial_picks=None,
    threshold=0.5,
    feature_fn=None,
    dist_fn=None,
    seed=42,
    method="sphere",
    n_jobs=1,
)
```

- Selects representative centroid molecules.
- Returns `(picked_indices, picked_mols)`.
- `method="sphere"`: leader picking with a distance `threshold`; common default for representative sets.
- `method="maxmin"`: max-min picking with threshold support.
- Hierarchical methods are supported when `method.upper()` is an RDKit `ClusterMethod` name such as `CENTROID`, `CLINK`, or `UPGMA`, but require `npick`.
- Unsupported method/`npick` combinations raise `ValueError`.

### `dm.assign_to_centroids`

Signature from source:

```python
dm.assign_to_centroids(mols, centroids, feature_fn=None, dist_fn=None, n_jobs=1)
```

- Assigns each query molecule to the nearest centroid by Tanimoto distance.
- Returns `(clusters_map, clusters_list)`.
- `clusters_map`: dictionary-like mapping centroid index to input molecule indices.
- `clusters_list`: list aligned to centroid order, each containing assigned input molecules.
- The centroid molecules themselves are not automatically added to `clusters_list`; assignments are for `mols` relative to `centroids`.

## Maximum Common Substructure

### `dm.find_mcs`

Signature from source:

```python
dm.find_mcs(
    mols,
    maximize_bonds=True,
    threshold=0.0,
    timeout=5,
    verbose=False,
    match_valences=False,
    ring_matches_ring_only=True,
    complete_rings_only=False,
    match_chiral_tag=False,
    seed_smarts="",
    atom_compare="CompareElements",
    bond_compare="CompareOrder",
    ring_compare="IgnoreRingFusion",
    with_details=False,
    **kwargs,
)
```

- Returns a SMARTS string for the maximum common substructure, or `None` when RDKit returns an empty SMARTS string.
- With `with_details=True`, returns the RDKit MCS result object, including timeout/completion details available in that RDKit version.
- Allowed `atom_compare`: `CompareAny`, `CompareAnyHeavyAtom`, `CompareElements`, `CompareIsotopes`.
- Allowed `bond_compare`: `CompareAny`, `CompareOrder`, `CompareOrderExact`.
- Allowed `ring_compare`: `IgnoreRingFusion`, `PermissiveRingFusion`, `StrictRingFusion`.
- Invalid compare mode strings raise `ValueError` before calling RDKit.

## Molecular Graph Helpers

### `dm.to_graph`

Signature from source:

```python
dm.to_graph(mol)
```

- Converts a molecule into a `networkx.Graph`.
- Nodes are atom indices with attributes: `atomic_num`, `formal_charge`, `chiral_tag`, `hybridization`, `num_explicit_hs`, `implicit_valence`, `degree`, `symbol`, `ring_atom`, and `is_aromatic`.
- Edges carry `bond_type`.
- Requires `networkx` to be importable; otherwise raises `ImportError`.

### `dm.match_molecular_graphs`

Signature from source:

```python
dm.match_molecular_graphs(
    mol1,
    mol2,
    match_atoms_on=["atomic_num"],
    match_bonds_on=["bond_type"],
)
```

- Returns a list of dictionaries mapping atom indices from `mol1` to corresponding atom indices in `mol2`.
- `match_atoms_on` can be a string, list of node attributes, or empty list to ignore atom attributes.
- `match_bonds_on` can be a string, list of edge attributes, or empty list to ignore bond attributes.
- Matching implicit hydrogens in one molecule against explicit hydrogens in another usually fails; fully explicit hydrogens can create many symmetry matches.
