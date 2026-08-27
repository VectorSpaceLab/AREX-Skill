# ProLIF Package Overview

ProLIF, short for Protein-Ligand Interaction Fingerprints, computes residue-pair interaction fingerprints for complexes from molecular dynamics trajectories, docking simulations, and experimental structures. Agents should treat ProLIF as a Python API package that bridges RDKit molecules, MDAnalysis atom selections, interaction definitions, pandas/RDKit result exports, and optional plotting helpers.

## Main Concepts

| Concept | What it means | Owning route |
| --- | --- | --- |
| `Molecule` | RDKit-backed molecule wrapper carrying residue information and coordinates | `sub-skills/molecules-and-io/` |
| `ResidueId`, `Residue`, `ResidueGroup` | Residue labels and residue collections used as fingerprint axes | `sub-skills/molecules-and-io/` |
| Interaction class | SMARTS/geometric detector such as `Hydrophobic`, `HBDonor`, `PiStacking`, `VdWContact`, or `WaterBridge` | `sub-skills/interactions/` |
| `Fingerprint` | Configured runner that stores sparse per-frame interaction results in `fp.ifp` | `sub-skills/fingerprints/` |
| Exports | pandas DataFrames, RDKit bitvectors/countvectors, and pickled fingerprints | `sub-skills/fingerprints/` |
| Plots | Ligand interaction networks, barcode plots, 3D complex views, and residue grids | `sub-skills/visualization/` |

## Installation Surfaces

- Base ProLIF depends on scientific Python packages including pandas, NumPy, SciPy, MDAnalysis, NetworkX, tqdm, multiprocess, dill, psutil, and gemmi.
- RDKit is required by normal ProLIF usage and tutorial-style workflows even when it is not listed in the base metadata dependencies in every release context.
- Plotting workflows need optional extras: `py3Dmol` and `matplotlib` through `prolif[plots]`, and tutorial workflows commonly use `prolif[tutorials]` for RDKit, plotting, seaborn, and pyvis.
- ProLIF has no public console-script CLI in the inspected package metadata; use Python scripts or notebooks.

## Stage Boundaries

1. **Input preparation** produces molecules, atom selections, residue labels, and suppliers. Stop here if files cannot be parsed, residue labels are unstable, or hydrogens/templates are wrong.
2. **Interaction setup** chooses names and parameters. Stop here for unknown interactions, count behavior, water bridges, implicit hydrogens, or direct residue-level checks.
3. **Fingerprint execution** runs over trajectories, pose iterables, or single pairs and owns exports. Stop here for empty `fp.ifp`, DataFrame shape surprises, parallel issues, or pickle/vector output questions.
4. **Visualization** consumes completed fingerprints and matching molecules. Stop here for notebook/display/backend issues or saved HTML/image output.

## Safe Package-Data Smoke Path

A minimal smoke workflow uses installed package data and does not need files from the original repository:

```python
import MDAnalysis as mda
import prolif as plf

u = mda.Universe(plf.datafiles.TOP, plf.datafiles.TRAJ)
lig = u.select_atoms("resname LIG")
prot = u.select_atoms("protein")
fp = plf.Fingerprint(["Hydrophobic", "HBDonor", "HBAcceptor"])
fp.run(u.trajectory[:1], lig, prot, n_jobs=1, progress=False)
print(fp.to_dataframe().shape)
```

Use `sub-skills/fingerprints/scripts/run_fingerprint_smoke.py` when a reusable script is preferable.
