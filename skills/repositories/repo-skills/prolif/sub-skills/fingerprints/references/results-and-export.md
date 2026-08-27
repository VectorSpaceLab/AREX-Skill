# Results And Export

ProLIF stores completed fingerprint results in `fp.ifp`, then converts them to pandas or RDKit vector formats. Keep plotting separate; route plot construction to `../../visualization/` after validating fingerprint results here.

## Result Object Model

After `Fingerprint.run(...)` or `Fingerprint.run_from_iterable(...)`:

```python
fp.ifp == {
    frame_or_pose_index: IFP(...),
    ...,
}
```

Each `IFP` maps residue-pair keys to sparse interaction metadata:

```python
frame_ifp = fp.ifp[0]
residue_pair_data = frame_ifp["LIG1.G", "ASP129.A"]
only_asp129 = frame_ifp["ASP129.A"]
```

`IFP.interactions()` yields named tuples with fields:

- `ligand`: ligand `ResidueId`.
- `protein`: protein `ResidueId`.
- `interaction`: interaction name such as `Hydrophobic`.
- `metadata`: one metadata dictionary for one occurrence, including atom indices and interaction-specific values such as distances or angles when available.

## DataFrame Export

```python
df = fp.to_dataframe(
    count=None,
    dtype=None,
    drop_empty=True,
    index_col="Frame",
)
```

DataFrame columns are a pandas `MultiIndex` with levels:

1. `ligand`
2. `protein`
3. `interaction`

Rows correspond to trajectory frame numbers or iterable pose indices.

Recommended checks:

```python
assert hasattr(fp, "ifp")
df = fp.to_dataframe(dtype=int)
assert df.index.name in {"Frame", "Pose"}
print(df.shape)
print(df.columns.names)  # ['ligand', 'protein', 'interaction']
```

Options:

- `count=None` follows `fp.count`; pass `count=True` for count values or `count=False` for binary values.
- `dtype=None` uses `bool` for binary output and `np.uint8` for counts; pass `int` for easier display/export.
- `drop_empty=True` removes columns that are all false/zero.
- `drop_empty=False` preserves the complete residue-pair/interaction grid and is useful when comparing schemas.
- `index_col="Pose"` makes docking-pose tables clearer.

## Utility Conversion From Raw IFPs

Use utility functions when the result is not attached to a `Fingerprint` object.

```python
ifp = fp.generate(lig_mol, prot_mol, metadata=True)
df = plf.to_dataframe({0: ifp}, fp.interactions.keys())
```

For a manually assembled or loaded IFP dictionary:

```python
df = plf.to_dataframe(
    ifp_results,
    interactions=["Hydrophobic", "HBDonor", "HBAcceptor"],
    count=False,
    dtype=int,
    drop_empty=False,
)
```

The `interactions` order determines the exported column order and vector bit positions.

## Bitvectors

```python
bitvectors = fp.to_bitvectors()
```

or from an existing DataFrame:

```python
bitvectors = plf.to_bitvectors(df.astype(bool))
```

- Returns a list of RDKit `ExplicitBitVect` objects, one per DataFrame row.
- Bit positions follow the current DataFrame column order.
- Use bitvectors for binary Tanimoto/Jaccard-style similarity.
- If `df` has zero columns, returned bitvectors have no on bits and are not meaningful for similarity decisions.

## Countvectors

```python
fp_count = plf.Fingerprint(count=True)
fp_count.run(u.trajectory[:20], lig, prot, progress=False, n_jobs=1)
count_df = fp_count.to_dataframe(count=True, dtype=int)
countvectors = fp_count.to_countvectors()
```

or from an existing DataFrame:

```python
countvectors = plf.to_countvectors(count_df)
```

- Returns a list of RDKit `UIntSparseIntVect` objects.
- Counts represent the number of metadata occurrences for each residue-pair/interaction column.
- Count vectors are useful when repeated interactions per residue pair should influence comparisons.

## Docking Pose Comparison Case

Goal: compare docking poses by Tanimoto similarity and export both binary bitvectors and a count DataFrame.

```python
from rdkit import DataStructs
import prolif as plf

protein_mol = plf.Molecule.from_mda(protein_atomgroup)
pose_supplier = plf.sdf_supplier("poses.sdf")

fp = plf.Fingerprint()
fp.run_from_iterable(pose_supplier, protein_mol, n_jobs=1, progress=False)
pose_df = fp.to_dataframe(index_col="Pose", dtype=int)
pose_bitvectors = fp.to_bitvectors()
sim_to_pose0 = DataStructs.BulkTanimotoSimilarity(pose_bitvectors[0], pose_bitvectors)

pose_supplier = plf.sdf_supplier("poses.sdf")
fp_count = plf.Fingerprint(list(fp.interactions), count=True)
fp_count.run_from_iterable(pose_supplier, protein_mol, n_jobs=1, progress=False)
count_df = fp_count.to_dataframe(index_col="Pose", count=True, dtype=int)
countvectors = fp_count.to_countvectors()
```

Validation checks:

```python
assert len(pose_bitvectors) == len(fp.ifp)
assert count_df.shape[0] == pose_df.shape[0]
assert list(count_df.index) == list(pose_df.index)
```

Notes:

- Recreate `pose_supplier` before the second run because many suppliers are consumed by iteration.
- `Fingerprint(list(fp.interactions), count=True)` preserves the same interaction set for the count run.
- If you need identical columns between binary and count tables, use `drop_empty=False` in both exports.

## Reference Ligand Vs Docking Poses

Use a common schema when comparing a reference ligand to docking poses.

```python
fp_ref = plf.Fingerprint(list(fp.interactions))
fp_ref.run_from_iterable([ref_mol], protein_mol, n_jobs=1, progress=False)

df_ref = fp_ref.to_dataframe(index_col="Pose", drop_empty=False)
df_poses = fp.to_dataframe(index_col="Pose", drop_empty=False)
combined = pandas.concat([df_ref, df_poses]).fillna(False).astype(bool)

bitvectors = plf.to_bitvectors(combined)
similarities = DataStructs.BulkTanimotoSimilarity(bitvectors[0], bitvectors[1:])
```

If column schemas differ, align with pandas before vector conversion so bit positions represent the same interactions.

## Pickle Export

```python
payload = fp.to_pickle()
restored = plf.Fingerprint.from_pickle(payload)

fp.to_pickle("fingerprint.pkl")
restored = plf.Fingerprint.from_pickle("fingerprint.pkl")
```

Guidance:

- Pickles use `dill` and preserve the `Fingerprint`, configured interactions, and `fp.ifp`.
- Pickles are best for short-term reuse in a compatible Python/ProLIF/RDKit environment.
- Do not treat pickles as safe input from untrusted sources.
- For durable sharing, export DataFrames in a user-selected tabular format and record ProLIF/RDKit versions separately.

## Export Preconditions

Before any export:

```python
if not hasattr(fp, "ifp"):
    raise RuntimeError("Run fp.run(...) or fp.run_from_iterable(...) before exporting")
```

Fingerprint export methods raise ``AttributeError("Please use the `run` method before")`` when called before execution. Plotting helpers raise ProLIF `RunRequiredError` for the same precondition; route plotting issues to `../../visualization/`.
