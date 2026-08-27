# Fingerprint API Reference

This reference summarizes the ProLIF fingerprint runtime APIs verified from the installed package and source tests. For interaction names and parameters, route to `../../interactions/`; for input conversion, route to `../../molecules-and-io/`.

## `prolif.Fingerprint`

```python
prolif.Fingerprint(
    interactions=None,
    parameters=None,
    count=False,
    vicinity_cutoff=6.0,
    use_segid=None,
    implicit_hydrogens=False,
    ignore=prolif.residue.ignore_self_interactions,
)
```

Important behavior:

- `interactions=None` uses ProLIF defaults: `Hydrophobic`, `HBDonor`, `HBAcceptor`, `PiStacking`, `Anionic`, `Cationic`, `CationPi`, `PiCation`, and `VdWContact`.
- `interactions="all"` requests all non-implicit non-bridged interaction classes; bridged interactions such as `WaterBridge` need explicit setup in `parameters`.
- `count=True` stores all occurrences for a residue pair and lets count exports report occurrence counts instead of first-hit bits.
- `vicinity_cutoff` controls automatic nearby-residue selection when `residues=None`; it is ignored when `residues` is a list or `"all"`.
- `use_segid=None` lets ProLIF choose segment-index labels when inputs have more segments than chains; pin it to `True` or `False` only when you need stable residue identifiers.

## Trajectory Execution: `Fingerprint.run`

```python
fp.run(
    traj,
    lig,
    prot,
    *,
    residues=None,
    converter_kwargs=None,
    progress=True,
    n_jobs=None,
    parallel_strategy=None,
)
```

Use this for MDAnalysis trajectory-like objects and `AtomGroup` inputs.

- `traj` accepts a full trajectory, a sliced trajectory, indexed frames, or a single `Timestep`.
- `lig` and `prot` are MDAnalysis ligand/protein `AtomGroup` objects.
- `residues=None` recomputes nearby protein residues per ligand and frame using `vicinity_cutoff`.
- `residues="all"` converts all protein residues once and uses them for every frame.
- `residues=["ASP129.A", ...]` restricts the calculation to those residue ids.
- `converter_kwargs` must be a two-item tuple of dicts: `(ligand_kwargs, protein_kwargs)` passed to the MDAnalysis RDKit converter.
- `n_jobs=1` runs serially; `n_jobs=None` uses ProLIF's job-selection helper; invalid values `<= 0` raise `ValueError`.
- `parallel_strategy` can be `"chunk"`, `"queue"`, or `None`; `None` chooses based on trajectory pickle size.
- The method returns the same `Fingerprint` instance and stores `fp.ifp` as `{frame_number: IFP}`.

## Iterable Pose Execution: `Fingerprint.run_from_iterable`

```python
fp.run_from_iterable(
    lig_iterable,
    prot_mol,
    *,
    residues=None,
    progress=True,
    n_jobs=None,
)
```

Use this for docking poses, conformer collections, or any iterable yielding `prolif.Molecule` ligand objects against one prepared protein `Molecule`.

- Frame keys in `fp.ifp` are the iterable positions: `0`, `1`, `2`, ...
- `residues` has the same `None`, `"all"`, or explicit-list meaning as `run()`.
- `n_jobs=1` is serial; `n_jobs=None` can use all logical cores because iterable execution is not capped by the trajectory-specific maximum.
- Suppliers/generators can be consumed by a run. Recreate them before running serial/parallel comparisons.

## Single-Pair Execution: `Fingerprint.generate`

```python
ifp = fp.generate(lig_mol, prot_mol, residues=None, metadata=False)
```

Use this when both sides are already `prolif.Molecule` objects and you only need one fingerprint.

- `metadata=False` returns a dictionary keyed by `(ligand_residue_id, protein_residue_id)` with numpy bit/count arrays.
- `metadata=True` returns an `IFP` object whose values are sparse interaction metadata dictionaries.
- To convert a generated `IFP` to a DataFrame, wrap it in a frame dictionary and call the utility function:

```python
single_ifp = fp.generate(lig_mol, prot_mol, metadata=True)
df = prolif.to_dataframe({0: single_ifp}, fp.interactions.keys())
```

## Export Methods On Completed `Fingerprint`

These methods require `fp.ifp`, which is created by `run()` or `run_from_iterable()`.

```python
fp.to_dataframe(count=None, dtype=None, drop_empty=True, index_col="Frame")
fp.to_bitvectors()
fp.to_countvectors()
fp.to_pickle(path=None)
prolif.Fingerprint.from_pickle(path_or_bytes)
```

- `to_dataframe()` creates a pandas DataFrame with a three-level column index: `ligand`, `protein`, `interaction`.
- `count=None` uses `fp.count`; pass `count=True` to force count output from metadata-rich IFPs.
- `drop_empty=True` removes all-empty interaction columns; use `drop_empty=False` for fixed-width comparison matrices.
- `to_bitvectors()` returns one RDKit `ExplicitBitVect` per frame or pose.
- `to_countvectors()` returns one RDKit `UIntSparseIntVect` per frame or pose and is most useful with `Fingerprint(count=True)`.
- `to_pickle()` with no path returns bytes; with a path it writes via `dill` and returns `None`.
- `from_pickle()` accepts either bytes or a path.

## Utility Functions

```python
prolif.to_dataframe(ifp, interactions, count=False, dtype=None, drop_empty=True, index_col="Frame")
prolif.to_bitvectors(df)
prolif.to_countvectors(df)
prolif.select_over_trajectory(u, trajectory, *selections, **kwargs)
```

Use the utilities when you have `IFP` dictionaries or DataFrames rather than a completed `Fingerprint` object.

- `prolif.to_dataframe` expects `{frame_number: IFP}` and an ordered collection of interaction names.
- `prolif.to_bitvectors` and `prolif.to_countvectors` convert rows of an existing DataFrame.
- `select_over_trajectory` evaluates one or more MDAnalysis selection strings over all requested frames and returns AtomGroups containing the union of selected atoms.
- In `select_over_trajectory`, additional selections can reference previous groups with `group {0}`, `group {1}`, and so on.

## `IFP` Inspection

`fp.ifp[frame]` is an `IFP`, a mapping from `(ligand_residue, protein_residue)` to interaction metadata.

```python
frame_ifp = fp.ifp[0]
metadata = frame_ifp["LIG1.G", "ASP129.A"]
filtered = frame_ifp["ASP129.A"]
for item in frame_ifp.interactions():
    print(item.ligand, item.protein, item.interaction, item.metadata)
```

- Tuple keys can be `ResidueId` objects or residue strings such as `"LIG1.G"`.
- A single residue string or `ResidueId` filters the `IFP` to interactions involving that residue.
- `IFP.interactions()` yields `InteractionData(ligand, protein, interaction, metadata)` named tuples.
- Invalid keys raise `KeyError` with guidance about tuple keys or single-residue filtering.

## Parallel Helpers

```python
prolif.parallel.get_n_jobs(n_jobs=None, capped=False)
prolif.parallel.get_mda_parallel_strategy(strategy, traj)
```

- `get_n_jobs` prioritizes explicit `n_jobs`, then `PROLIF_N_JOBS`, then logical CPU count; with `capped=True`, trajectory runs are capped by `PROLIF_MAX_JOBS` unless the user passed `n_jobs` explicitly.
- `get_mda_parallel_strategy(None, traj)` chooses `"queue"` when the pickled trajectory object exceeds ProLIF's threshold and `"chunk"` otherwise.
- Explicit `parallel_strategy="chunk"` or `"queue"` bypasses the heuristic.
