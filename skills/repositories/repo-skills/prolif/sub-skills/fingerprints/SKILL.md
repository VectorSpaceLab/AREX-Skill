---
name: fingerprints
description: "Run ProLIF fingerprints on trajectories, ligand-pose iterables, or
  molecule pairs and export results safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProLIF Fingerprints

Use this sub-skill when an agent must execute a ProLIF interaction fingerprint, inspect the sparse `IFP` results, convert results to tabular or RDKit vector forms, compare frames or docking poses, or persist/reload a completed fingerprint.

## Route First

- Choose or parameterize interaction classes in `../interactions/` before constructing `prolif.Fingerprint(...)` with non-default interactions, `parameters`, `count=True`, `implicit_hydrogens=True`, bridged interactions, or custom `ignore` predicates.
- Prepare `MDAnalysis.AtomGroup`, iterable `prolif.Molecule`, supplier, residue, and `use_segid` inputs in `../molecules-and-io/` before running fingerprints.
- Create ligand-network, barcode, or 3D plots in `../visualization/` after a fingerprint has been run; this sub-skill only cross-links plotting preconditions.

## Choose The Execution API

- Use `Fingerprint.run(traj, lig, prot, ...)` for MDAnalysis trajectories, sliced trajectories, indexed frames, or a single timestep with ligand/protein `AtomGroup` objects.
- Use `Fingerprint.run_from_iterable(lig_iterable, prot_mol, ...)` for docking poses or any iterable yielding `prolif.Molecule` ligand conformers against one prepared protein `Molecule`.
- Use `Fingerprint.generate(lig_mol, prot_mol, ...)` for one ligand/protein `Molecule` pair when you want an immediate sparse `IFP` or bitvector dictionary without storing a trajectory-scale `fp.ifp`.
- Use `prolif.utils.select_over_trajectory(...)` before `run()` when a distance-based MDAnalysis selection must include atoms that appear near a reference over multiple frames.

## Core References

- `references/api-reference.md` lists the installed runtime signatures and result object contracts.
- `references/workflows.md` gives executable trajectory, docking-pose, single-pair, and parallel recovery recipes.
- `references/results-and-export.md` covers `to_dataframe`, `to_bitvectors`, `to_countvectors`, `to_pickle`, `from_pickle`, `IFP` indexing, Tanimoto comparison, and count fingerprints.
- `references/troubleshooting.md` covers run-before-export errors, empty results, residue-selection mistakes, multiprocessing differences, `converter_kwargs`, pickle portability, progress/noise, and `use_segid` surprises.

## Safe Smoke Check

Run the bundled helper to confirm the installed package can execute a minimal package-data fingerprint:

```bash
python scripts/run_fingerprint_smoke.py --no-progress
```

Expected JSON includes `dataframe_shape`, `frame_keys`, and `interactions`. A verified package-data run with three interactions produced shape `[1, 10]` and frame key `[0]`.
