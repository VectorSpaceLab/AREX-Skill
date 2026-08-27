# Fingerprint Workflows

The recipes below are intended for future agents to adapt in user projects. They rely only on installed ProLIF APIs and user-provided inputs. Use `../../molecules-and-io/` to prepare inputs and `../../interactions/` to choose interaction names or parameters.

## Package-Data Smoke Run

Use this before debugging user data. It proves the installed package, MDAnalysis, RDKit conversion, and ProLIF package data can run one frame.

```python
import json
import MDAnalysis as mda
import prolif as plf

u = mda.Universe(plf.datafiles.TOP, plf.datafiles.TRAJ)
lig = u.select_atoms("resname LIG")
prot = u.select_atoms("protein")

fp = plf.Fingerprint(["Hydrophobic", "HBDonor", "HBAcceptor"])
fp.run(u.trajectory[:1], lig, prot, n_jobs=1, progress=False)
df = fp.to_dataframe()

print(json.dumps({
    "dataframe_shape": list(df.shape),
    "frame_keys": sorted(map(int, fp.ifp.keys())),
    "interactions": list(fp.interactions),
}))
```

Validation checks:

- `hasattr(fp, "ifp")` is true.
- `sorted(fp.ifp)` contains the expected frame numbers.
- `df.shape[0]` equals the number of frames or poses analyzed.
- If `df.shape[1] == 0`, see `troubleshooting.md#empty-dataframe-or-empty-interactions`.

## MDAnalysis Trajectory Fingerprint

```python
import MDAnalysis as mda
import prolif as plf

u = mda.Universe("topology.pdb", "trajectory.xtc")
lig = u.select_atoms("resname LIG")
prot = u.select_atoms("protein")

fp = plf.Fingerprint()
fp.run(
    u.trajectory[:100],
    lig,
    prot,
    residues=None,
    n_jobs=1,
    progress=False,
)

df = fp.to_dataframe(dtype=int)
bitvectors = fp.to_bitvectors()
```

Use `n_jobs=1` first for a reproducible baseline. Increase `n_jobs` only after the serial result is valid.

## Distance-Based Selection Over A Trajectory

MDAnalysis selections are evaluated on the current frame by default. Use `select_over_trajectory` when a distance-based selection should include atoms or residues that appear near a reference at any point in the analyzed window.

```python
import MDAnalysis as mda
import prolif as plf

u = mda.Universe("topology.pdb", "trajectory.xtc")
lig = u.select_atoms("resname LIG")

pocket = plf.select_over_trajectory(
    u,
    u.trajectory[:200],
    "protein and byres around 6 group ligand",
    ligand=lig,
)

fp = plf.Fingerprint()
fp.run(u.trajectory[:200], lig, pocket, n_jobs=1, progress=False)
df = fp.to_dataframe()
```

For multiple related selections, later strings can reference earlier selected groups:

```python
protein_shell, water_shell = plf.select_over_trajectory(
    u,
    u.trajectory[:50],
    "protein and byres around 4 group ligand",
    "resname TIP3 and byres around 4 (group ligand or group {0})",
    ligand=lig,
)
```

## Docking Pose Or Ligand Iterable Fingerprint

Use `run_from_iterable` when each ligand pose is already yielded as a `prolif.Molecule` and the protein is one `prolif.Molecule`.

```python
import prolif as plf

protein_mol = plf.Molecule.from_mda(protein_atomgroup)
pose_iterable = plf.sdf_supplier("docking_poses.sdf")

fp = plf.Fingerprint()
fp.run_from_iterable(pose_iterable, protein_mol, n_jobs=1, progress=False)

df = fp.to_dataframe(index_col="Pose")
bitvectors = fp.to_bitvectors()
```

Validation checks:

- `len(fp.ifp)` should match the number of poses consumed.
- DataFrame index name can be set to `"Pose"` with `index_col="Pose"`.
- Recreate file suppliers before rerunning; many suppliers/generators are consumed.

## Single Ligand/Protein Molecule Pair

Use `generate` for direct one-pair analysis without a stored `fp.ifp`.

```python
import prolif as plf

lig_mol = plf.Molecule.from_mda(ligand_atomgroup)
prot_mol = plf.Molecule.from_mda(protein_atomgroup)

fp = plf.Fingerprint(["Hydrophobic", "HBDonor", "HBAcceptor"])
ifp = fp.generate(lig_mol, prot_mol, metadata=True)

for item in ifp.interactions():
    print(item.ligand, item.protein, item.interaction, item.metadata)

df = plf.to_dataframe({0: ifp}, fp.interactions.keys(), index_col="Pair")
```

Use `metadata=False` only when you need the lower-level residue-pair bit/count arrays and not the metadata-rich sparse `IFP`.

## Parallel Trajectory Execution

After a serial baseline succeeds:

```python
fp = plf.Fingerprint()
fp.run(
    u.trajectory[:500],
    lig,
    prot,
    n_jobs=4,
    parallel_strategy="queue",
    progress=False,
)
df_parallel = fp.to_dataframe()
```

Strategy guidance:

- `parallel_strategy="chunk"` splits frame indices and lets workers iterate chunks of the trajectory.
- `parallel_strategy="queue"` converts frames to ProLIF molecules in the parent process and sends lighter work items to workers.
- `parallel_strategy=None` uses ProLIF's trajectory pickle-size heuristic.
- If parallel output differs from serial output, compare `df_serial.equals(df_parallel)` on a small frame slice and see `troubleshooting.md#multiprocessing-differences`.

## Converter Keyword Recovery

When MDAnalysis-to-RDKit conversion needs custom options, pass exactly two dictionaries: the first for the ligand, the second for the protein.

```python
fp.run(
    u.trajectory[:10],
    lig,
    prot,
    converter_kwargs=(
        {"force": True},
        {"force": True},
    ),
    n_jobs=1,
    progress=False,
)
```

Do not pass a single dict, a one-item tuple, or a shared mutable object whose state is changed during the run.

## Count Fingerprint Workflow

Use `Fingerprint(count=True)` to retain multiple occurrences of an interaction for the same residue pair.

```python
fp_count = plf.Fingerprint(count=True)
fp_count.run(u.trajectory[:20], lig, prot, n_jobs=1, progress=False)
count_df = fp_count.to_dataframe(count=True, dtype=int)
countvectors = fp_count.to_countvectors()
```

Checks:

- `count_df.max().max()` can be greater than `1` when multiple occurrences exist.
- `to_countvectors()` returns RDKit `UIntSparseIntVect` objects.
- For binary fingerprints, use `count=False` or a non-count `Fingerprint` and `to_bitvectors()`.

## Tanimoto Similarity For Frames Or Poses

```python
from rdkit import DataStructs

bitvectors = fp.to_bitvectors()
reference = bitvectors[0]
similarities = DataStructs.BulkTanimotoSimilarity(reference, bitvectors)
```

For a full pairwise matrix:

```python
matrix = [DataStructs.BulkTanimotoSimilarity(bv, bitvectors) for bv in bitvectors]
```

If combining a reference ligand with docking poses, use the same interaction list and DataFrame schema for both runs, then convert the combined DataFrame with `plf.to_bitvectors`.

## Pickle And Reload

```python
fp.to_pickle("fingerprint.pkl")
loaded = plf.Fingerprint.from_pickle("fingerprint.pkl")
loaded_df = loaded.to_dataframe()

payload = fp.to_pickle()
loaded_from_bytes = plf.Fingerprint.from_pickle(payload)
```

Pickles are convenient for handoff within the same Python/ProLIF/RDKit environment. For long-term or cross-environment data exchange, prefer exporting DataFrames to a standard table format controlled by the caller.
