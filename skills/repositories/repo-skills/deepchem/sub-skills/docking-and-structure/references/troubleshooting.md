# Docking and Structure Troubleshooting

Use this guide to triage structural failures without assuming the user's environment has every optional backend installed.

## Missing Optional Imports

### `ImportError: This function requires vina to be installed`

- The selected workflow uses `VinaPoseGenerator` and imports `from vina import Vina`.
- Confirm with `python scripts/check_structure_dependencies.py`.
- If the user only needs a plan, stop at dependency instructions. If they need execution, install the `vina` Python package in the active environment using the user's package policy.
- Re-run a small import smoke test before docking.

### `ImportError: This class requires mdtraj to be installed`

- `BindingPocketFeaturizer` and neighbor-list computation paths need `mdtraj`.
- Pocket finding itself may still work if structure loading works; only pocket residue features or neighbor lists are blocked.

### `ImportError: This class requires matminer/pymatgen/networkx to be installed`

- Material featurizers are optional and split by input type.
- `ElemNetFeaturizer` needs `pymatgen` composition behavior.
- `ElementPropertyFingerprint` and `SineCoulombMatrix` need `matminer`.
- `LCNNFeaturizer` needs `pymatgen`, `networkx`, and `scipy`, plus correctly annotated surface structures.

### `ModuleNotFoundError: torch` or DFT import failures

- DFT model modules import `torch` directly.
- If `torch` is intentionally absent, do not use `deepchem.models.dft` surfaces; report that DFT/XC workflows require optional torch and likely `dqc` extras.
- Missing TensorFlow/JAX does not block these DFT imports unless another chosen workflow needs them.

## Missing Binaries or Platform Issues

### GNINA not found or cannot execute

- DeepChem's GNINA generator is Linux-only and may download an executable into DeepChem's data directory.
- Check executable availability with the bundled helper and confirm the OS.
- CUDA >= 10.1 is recommended for fast CNN scoring; CPU-only behavior depends on the GNINA build and may be slow or unavailable.
- Do not treat a GNINA binary on `PATH` as enough: test `gnina --help` only when it is safe to run external commands.

### Vina command missing but Python `vina` imports

- DeepChem's `VinaPoseGenerator` uses the Python `vina` API, so the command-line `vina` binary is not necessarily required for DeepChem execution.
- The command is still useful as a human diagnostic; report both Python package and command availability separately.

## Input Format Failures

### Protein or ligand extension rejected

- `GninaPoseGenerator` requires protein `.pdb` and ligand `.sdf`.
- `VinaPoseGenerator` can convert protein `.pdb` and ligand `.sdf` to `.pdbqt`, or consume preprepared `.pdbqt` files.
- When both Vina inputs are `.pdbqt`, DeepChem returns scores rather than RDKit posed complexes.

### Tuple ordering mismatch

- Docking APIs use `(protein_file, ligand_file)`.
- Most complex featurizers use `(ligand_or_molecule_file, protein_file)` or names like `(mol_pdb_file, protein_pdb_file)`.
- If a featurizer silently returns `None` or logs molecule loading warnings, re-check ordering before changing chemistry settings.

### RDKit load or sanitization failures

- Confirm 3D coordinates exist and file content matches the extension.
- Try disabling sanitization only for featurizers that support it; some features require sanitization for aromaticity (`pi_stack`, `cation_pi`, `ecfp_ligand`).
- Ligands may need hydrogens, valid bond orders, and conformers. Proteins may need standard residues and cleanup.
- For docking preparation, `deepchem.utils.docking_utils.prepare_inputs` can add hydrogens and fix common PDB issues, but it requires RDKit, PDBFixer, and OpenMM and still needs human inspection.

### PDBQT conversion problems

- Conversion from PDB/SDF to PDBQT requires RDKit structure loading and charge/hydrogen handling.
- Preprepared PDBQT files can bypass conversion but may reduce what DeepChem returns.
- If output parsing fails, inspect whether the docking output contains `MODEL`, `ENDMDL`, and `REMARK VINA RESULT:` records expected by DeepChem's parser.

## Pocket Problems

### Too many or odd pockets

- `ConvexHullPocketFinder` is a simple geometric heuristic, not a learned pocket detector by default.
- Adjust `pad`, merge behavior expectations, or use a known ligand with `extract_active_site` for a more targeted box.
- If docking all pockets is too expensive, use `num_pockets` to restrict Vina docking after visually or chemically reviewing candidates.

### Pocket features all zeros or missing residues

- `BindingPocketFeaturizer` counts a fixed residue vocabulary and logs non-standard residues.
- Confirm the PDB residue names are standard and the pocket boxes overlap protein atoms.
- Confirm `mdtraj` loads the same protein file successfully.

## Complex Featurizer Problems

### `max_atoms was set too low`

- `AtomicConvFeaturizer` pads to fixed sizes. Increase `frag1_num_atoms`, `frag2_num_atoms`, or `complex_num_atoms` based on actual atom counts.
- Decide whether `strip_hydrogens=True` is appropriate before sizing.

### Empty or ignored feature channels

- `RdkitGridFeaturizer` ignores unknown feature names.
- `sybyl` is not implemented.
- Aromatic features are ignored unless `sanitize=True`.
- Flat features force flattened output; do not expect a voxel tensor when using `ecfp_ligand`, `ecfp_hashed`, `splif_hashed`, or `hbond_count`.

## Material and DFT Problems

### CGCNN initialization downloads data

- `CGCNNFeaturizer` downloads atom initialization data into the DeepChem data directory.
- If network access is blocked, initialization may warn and later feature computation may fail because atom features are unavailable.

### LCNN site-property errors

- `LCNNFeaturizer` requires primitive-cell and datapoint site properties for active/spectator sites.
- Validate `SiteTypes`, active species labels, occupation-site values, and periodic boundary settings before blaming DeepChem.

### DFT/dqc failures

- Confirm `torch` first, then `dqc`, then the DFT entry/system object.
- Start with a tiny CPU smoke case before GPU or batched work.
- Treat dtype/device mismatches as tensor-backend issues, not generic DeepChem import failures.
