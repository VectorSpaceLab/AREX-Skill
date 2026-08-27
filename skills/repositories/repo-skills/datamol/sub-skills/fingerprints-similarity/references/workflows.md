# Workflows: Fingerprints, Distances, Clustering, MCS, and Graph Matching

These recipes assume `import datamol as dm` and valid, cleaned molecules. If a SMILES list may contain invalid records, parse and filter it before using these workflows; route that preparation to `../molecule-io-prep/`.

## Create a Fingerprint Matrix

Use this when a downstream model or similarity calculation needs a dense NumPy matrix.

```python
import numpy as np
import datamol as dm

smiles = ["CCO", "CCN", "c1ccccc1", "CC(=O)O"]
mols = [dm.to_mol(s) for s in smiles]
if any(m is None for m in mols):
    raise ValueError("Clean or remove invalid molecules before fingerprinting")

fps = [dm.to_fp(mol, fp_type="ecfp", as_array=True) for mol in mols]
fp_matrix = np.asarray(fps)
```

Expected shape with defaults: `(len(mols), 2048)`. For count fingerprints, pass a count type such as `fp_type="ecfp-count"`. For reduced dimensionality, either pass `fold_size` to `dm.to_fp` or fold a sparse count vector explicitly:

```python
sparse_count_fp = dm.to_fp(mols[0], fp_type="ecfp-count", as_array=False)
folded = dm.fold_count_fp(sparse_count_fp, dim=512, binary=False)
```

Parameter choices:

- Use `fp_type="ecfp"` for a default general-purpose binary Morgan fingerprint.
- Use `fp_type="fcfp"` when feature atom invariants are more appropriate.
- Use `fp_type="maccs"` for a compact, interpretable 167-bit representation.
- Use `fp_type="ecfp-count"` plus folding for count-aware ML features.
- Keep one `fp_type` and one size across a matrix; mixing fingerprint families creates shape/type mismatches.

## Compute Descriptor Tables

Use datamol descriptors when a tabular property matrix is more useful than bits.

```python
import datamol as dm

mols = [dm.to_mol(s) for s in ["CCO", "CCN", "c1ccccc1"]]
descriptors = dm.descriptors.batch_compute_many_descriptors(
    mols,
    n_jobs=1,
    progress=False,
)
```

To compute only custom descriptors, disable default merging:

```python
props = dm.descriptors.compute_many_descriptors(
    mols[0],
    properties_fn={"max_partial_charge": "MaxPartialCharge"},
    add_properties=False,
)
```

Use callable values for custom Python descriptors and RDKit descriptor names as strings when they exist in `rdkit.Chem.Descriptors` or `rdkit.Chem.rdMolDescriptors`.

## Pairwise Distance Matrix

Use `dm.pdist` for all-vs-all distances inside one collection.

```python
import datamol as dm

mols = [dm.to_mol(s) for s in ["CCO", "CCN", "c1ccccc1", "CC(=O)O"]]
dist = dm.pdist(mols, fp_type="ecfp", n_jobs=1, squareform=True)
```

Expected return shape: `(n, n)`. The matrix is symmetric with diagonal zeros. For algorithms that expect SciPy condensed vectors, use:

```python
condensed = dm.pdist(mols, squareform=False)
```

Because `dm.pdist` forwards `**fp_args` to `dm.to_fp`, the same fingerprint arguments apply:

```python
dist = dm.pdist(mols, fp_type="maccs", n_jobs=1)
```

## Cross-Distance Matrix

Use `dm.cdist` for query-vs-library distance matrices.

```python
queries = [dm.to_mol(s) for s in ["CCO", "CCN"]]
library = [dm.to_mol(s) for s in ["c1ccccc1", "CC(=O)O", "CCCC"]]

cross = dm.cdist(
    queries,
    library,
    fp_type="ecfp",
    n_jobs=1,
    distances_chunk=False,
)
```

Expected shape: `(len(queries), len(library))`. Smaller values mean more similar fingerprints. For large libraries, enable chunked distance computation:

```python
cross = dm.cdist(
    queries,
    library,
    distances_chunk=True,
    distances_chunk_memory=512,
    distances_n_jobs=1,
)
```

Tune `n_jobs` for fingerprint computation separately from `distances_n_jobs` for sklearn's chunked distance computation.

## Butina Clustering

Use `dm.cluster_mols` when a similarity threshold should define clusters.

```python
mols = [dm.to_mol(s) for s in ["CCO", "CCCO", "CCCCO", "c1ccccc1", "c1ccncc1"]]
cluster_indices, cluster_mols = dm.cluster_mols(mols, cutoff=0.4, n_jobs=1)
cluster_sizes = [len(group) for group in cluster_mols]
```

Return interpretation:

- `cluster_indices` contains input indices grouped by Butina.
- `cluster_mols` contains the corresponding molecules; singleton clusters are one-element lists.
- Lower `cutoff` is stricter because it clusters by Tanimoto distance.
- Higher `cutoff` joins more distant molecules into the same cluster.

To use a non-default fingerprint, pass a `feature_fn` that returns RDKit fingerprint vectors:

```python
from functools import partial

feature_fn = partial(dm.to_fp, as_array=False, fp_type="maccs")
cluster_indices, cluster_mols = dm.cluster_mols(mols, cutoff=0.3, feature_fn=feature_fn)
```

## Diverse Picking

Use `dm.pick_diverse` to select structurally spread-out molecules.

```python
indices, picked = dm.pick_diverse(mols, npick=3, seed=19, n_jobs=1)
picked_smiles = [dm.to_smiles(mol) for mol in picked]
```

Guidance:

- `npick` includes any `initial_picks`.
- Use `seed` for reproducibility.
- Ensure `npick <= len(mols)` to avoid picker failures.
- Force known actives or controls with `initial_picks=[0, 5]` when needed.

## Centroid Picking and Assignment

Use `dm.pick_centroids` to select representatives, then `dm.assign_to_centroids` to attach molecules to the closest representative.

```python
centroid_indices, centroids = dm.pick_centroids(
    mols,
    npick=3,
    threshold=0.4,
    method="sphere",
    n_jobs=1,
)
clusters_map, clusters_list = dm.assign_to_centroids(mols, centroids, n_jobs=1)
```

Method choices:

- `method="sphere"`: good default for representative selection under a minimum-distance threshold.
- `method="maxmin"`: useful when maximizing spread with a fixed pick size.
- Hierarchical methods such as `centroid`, `clink`, or `upgma`: require `npick` and use RDKit `HierarchicalClusterPicker`.

Remember that `clusters_list` contains assigned input molecules and does not automatically add centroid molecules as separate labels or headers.

## Maximum Common Substructure Checks

Use `dm.find_mcs` for a SMARTS pattern shared across related molecules.

```python
series = [
    "CCOc1ccccc1C(=O)N",
    "CCNc1ccccc1C(=O)N",
    "COc1ccccc1C(=O)N",
]
mols = [dm.to_mol(s) for s in series]
smarts = dm.find_mcs(
    mols,
    timeout=5,
    threshold=0.8,
    ring_matches_ring_only=True,
    complete_rings_only=False,
)
```

Use `with_details=True` when timeout or match-quality status matters:

```python
result = dm.find_mcs(mols, timeout=2, with_details=True)
smarts = result.smartsString or None
```

MCS is sensitive to RDKit version, timeout, compare modes, chirality, valence matching, and ring constraints. Treat the SMARTS as a chemistry hypothesis to inspect, not as a stable text hash across environments.

## Molecular Graph Matching

Use graph matching for atom-index correspondences between molecules with compatible graph topology.

```python
mol1 = dm.to_mol("C1CCOCC1", ordered=False)
mol2 = dm.to_mol("C1CCOCC1", ordered=True)
matches = dm.match_molecular_graphs(
    mol1,
    mol2,
    match_atoms_on=["atomic_num"],
    match_bonds_on=["bond_type"],
)
```

Use empty match lists to relax constraints:

```python
shape_only_matches = dm.match_molecular_graphs(mol1, mol2, match_atoms_on=[], match_bonds_on=[])
```

For graph inspection, `dm.to_graph(mol)` returns a `networkx.Graph` with atom attributes on nodes and `bond_type` on edges. This requires `networkx` to be installed.

## Drawing or Reporting Results

This sub-skill stops at numeric selections, SMARTS, graph matches, and molecule groups. For grids of clusters, highlighted MCS, lasso overlays, or image export, use `../visualization-utilities/` after computing indices or molecule groups here.
