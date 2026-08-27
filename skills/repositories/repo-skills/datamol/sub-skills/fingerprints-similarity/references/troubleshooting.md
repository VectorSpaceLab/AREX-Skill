# Troubleshooting: Fingerprints, Similarity, Clustering, MCS, and Graph Helpers

Use this guide when datamol similarity workflows fail, return unexpected shapes, or produce surprising clusters. Keep molecule parsing and cleanup fixes in the sibling molecule-preparation skill; this reference focuses on feature, distance, clustering, MCS, and graph behavior.

## Invalid Molecules

Symptoms:

- `dm.to_fp` raises `ValueError` with text like `input molecule ... is invalid`.
- `dm.pdist` or `dm.cdist` fails inside fingerprint generation.
- A matrix construction step fails because one fingerprint is missing.

Likely causes:

- A SMILES string does not parse.
- A molecule became `None` after cleanup.
- Mixed raw strings and invalid molecules were passed directly to distance APIs.

Recovery:

1. Parse all SMILES with `dm.to_mol` before feature generation.
2. Filter or repair `None` values before calling `dm.to_fp`, `dm.pdist`, `dm.cdist`, or clustering functions.
3. Preserve original row identifiers so filtered molecules can be traced back.
4. Route standardization, salt handling, neutralization, and invalid-SMILES cleanup to `../molecule-io-prep/`.

Minimal guard:

```python
mols = [dm.to_mol(s) for s in smiles]
invalid = [i for i, mol in enumerate(mols) if mol is None]
if invalid:
    raise ValueError(f"Invalid molecules at positions: {invalid}")
```

## Unknown `fp_type`

Symptoms:

- `dm.to_fp(..., fp_type="...")` raises `ValueError` saying the fingerprint is not available.

Recovery:

1. Inspect `sorted(dm.list_supported_fingerprints())` in the runtime environment.
2. Use exact lowercase names such as `ecfp`, `fcfp`, `maccs`, `rdkit`, `pattern`, `layered`, `topological`, `atompair`, `erg`, `estate`, and available `*-count` variants.
3. Avoid assuming aliases like `morgan`, `ECFP4`, or `avalon` unless `dm.list_supported_fingerprints()` returns them.
4. Remember that source evidence includes `avalon-count`, but not an `avalon` key in the public supported mapping.

## Fingerprint Shape or Type Mismatches

Symptoms:

- `np.asarray(fps)` creates an object array instead of a numeric matrix.
- SciPy or sklearn distance functions reject input shapes.
- `dm.fold_count_fp` raises a wrong-type `ValueError`.
- Distances look inconsistent after mixing fingerprint settings.

Likely causes:

- Mixed fingerprint families or sizes in one matrix.
- Mixed dense arrays and native RDKit vectors.
- Count fingerprints folded for some molecules but not others.
- Passing a dense NumPy array into `dm.fold_count_fp`, which expects sparse bit/count vectors.

Recovery:

1. Pick one `fp_type`, one `fpSize` or `fold_size`, and one `as_array` mode per matrix.
2. For `dm.pdist` and `dm.cdist`, pass fingerprint arguments once to the distance call instead of precomputing mixed arrays.
3. Use `dm.fp_to_array(fp)` for supported native RDKit vectors that need dense arrays.
4. For folded count fingerprints, create native sparse/count vectors with `as_array=False`, then call `dm.fold_count_fp`.
5. Validate shape before modeling:

```python
matrix = np.asarray([dm.to_fp(mol, fp_type="ecfp") for mol in mols])
assert matrix.ndim == 2
assert matrix.shape[0] == len(mols)
```

## `n_jobs`, Chunking, and Parallel Failures

Symptoms:

- Multiprocessing is slower than serial execution for tiny inputs.
- Worker errors obscure the original invalid molecule or bad fingerprint argument.
- `dm.cdist(..., distances_chunk=True)` consumes too much memory or CPU.
- Results arrive but performance is unstable in constrained environments.

Recovery:

1. Reproduce with `n_jobs=1` or `n_jobs=None` first.
2. Increase parallelism only after the serial workflow is correct.
3. For `dm.cdist`, distinguish fingerprint parallelism (`n_jobs`) from chunked distance parallelism (`distances_n_jobs`).
4. Lower `distances_chunk_memory` when chunked cross distances stress memory.
5. Avoid `n_jobs=-1` in shared or CI environments unless the user asked for maximum local throughput.

## Distance Matrix Surprises

Symptoms:

- `dm.pdist` returns a 1D vector instead of a square matrix.
- Cross-distance output shape seems transposed.
- Distances are high even for molecules that feel chemically related.

Recovery:

- `dm.pdist(..., squareform=False)` intentionally returns a condensed vector of length `n * (n - 1) / 2`; set `squareform=True` for an `(n, n)` matrix.
- `dm.cdist(mols1, mols2)` returns shape `(len(mols1), len(mols2))`; rows are queries from the first argument.
- Distances are Jaccard/Tanimoto distances over selected fingerprints, where `0.0` means identical bit sets and larger values mean less similar.
- Try a different `fp_type`, radius, count fingerprint, or chemistry-specific preprocessing when distances do not match domain expectations.

## Empty or Unexpected Clusters

Symptoms:

- `dm.cluster_mols` returns many singleton clusters.
- One large cluster absorbs most molecules.
- `operator.itemgetter`-based grouping errors on empty input.
- Cluster representatives are not the molecules expected by domain logic.

Likely causes:

- `cutoff` is too strict or too loose for the chosen fingerprint.
- Input list is empty or contains invalid molecules.
- Feature function returns dense arrays instead of RDKit vectors for cluster functions expecting Tanimoto on RDKit fingerprints.

Recovery:

1. Ensure `len(mols) > 0` before clustering or picking.
2. Filter invalid molecules before clustering.
3. Start with `cutoff=0.2` to `0.7` and inspect cluster-size distributions.
4. If overriding `feature_fn`, return RDKit fingerprint vectors, commonly with `dm.to_fp(..., as_array=False)`.
5. Use `pick_centroids` or `pick_diverse` when representative selection is the real goal, not full cluster assignment.

## Diversity and Centroid Picker Errors

Symptoms:

- Picker raises errors or returns fewer picks than expected.
- `pick_centroids` raises `ValueError` about unsupported method/number of elements.
- Initial picks are ignored by hierarchical centroid methods.

Recovery:

- Keep `npick <= len(mols)`.
- Count `initial_picks` inside `npick`.
- Use `method="sphere"` or `method="maxmin"` for the common paths.
- For hierarchical methods, provide `npick` and do not rely on `initial_picks`; source behavior warns and discards initial picks for those methods.
- Fix `seed` in `pick_diverse` and max-min centroid selection when reproducibility matters.

## MCS Timeout, Threshold, or Empty Results

Symptoms:

- `dm.find_mcs` returns `None`.
- Result changes across RDKit versions.
- MCS is small, too generic, or misses an expected ring system.
- MCS search is slow or times out.
- Invalid compare strings raise `ValueError`.

Recovery:

1. Set a bounded `timeout` for interactive or automated workflows.
2. Use `with_details=True` to inspect the RDKit result object and determine whether the search completed or timed out.
3. Raise `threshold` toward `1.0` when the MCS must appear in most or all molecules; lower it when partial-series overlap is acceptable.
4. Tighten ring behavior with `ring_matches_ring_only=True` and `complete_rings_only=True` when ring integrity matters.
5. Use valid compare modes only:
   - `atom_compare`: `CompareAny`, `CompareAnyHeavyAtom`, `CompareElements`, `CompareIsotopes`.
   - `bond_compare`: `CompareAny`, `CompareOrder`, `CompareOrderExact`.
   - `ring_compare`: `IgnoreRingFusion`, `PermissiveRingFusion`, `StrictRingFusion`.
6. Treat the SMARTS text as RDKit-version-sensitive; validate chemically instead of comparing exact strings across environments.

## Graph Helper Failures

Symptoms:

- `dm.to_graph` or `dm.match_molecular_graphs` raises `ImportError` for `networkx`.
- Matching returns zero matches for molecules that seem identical.
- Matching returns many matches for symmetric or explicit-hydrogen molecules.

Recovery:

- Install or enable `networkx` in the runtime environment when graph helpers are required.
- Ensure both molecules use compatible explicit/implicit hydrogen representations.
- Start strict with `match_atoms_on=["atomic_num"]` and `match_bonds_on=["bond_type"]`, then relax to empty lists only when topology-only matching is intended.
- Expect many matches for symmetric rings and explicit hydrogens; choose a deterministic first match only if the downstream task can tolerate symmetry ambiguity.

## When Visualization Is Needed

This sub-skill returns numeric matrices, index groups, molecule groups, SMARTS strings, and graph matches. For depiction, grids, lasso highlights, or MCS visualization, hand off the computed molecules and indices to `../visualization-utilities/` rather than adding drawing code to similarity workflows.
