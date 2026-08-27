# Optional Dependencies and Binary Gates

DeepChem structural workflows are intentionally broad, but many require packages or binaries outside a minimal DeepChem install. Always check dependencies before promising that a workflow can run.

## Quick Check

Use the bundled helper without running docking:

```bash
python scripts/check_structure_dependencies.py
```

The helper reports DeepChem import/version, key Python imports, and whether external `vina` or `gnina` commands appear on `PATH`.

## Dependency Matrix

| Workflow | Required inputs | Python dependencies | External binaries / system gates |
| --- | --- | --- | --- |
| Convex-hull pocket finding | Protein structure, usually PDB | DeepChem core, RDKit stack used by molecule loading | None beyond structure parsing |
| Binding pocket residue features | Protein PDB plus pocket boxes | `mdtraj` | None |
| Vina docking through `VinaPoseGenerator` | Protein `.pdb` + ligand `.sdf`, or prepared `.pdbqt` files | `vina`, RDKit stack | Vina is not available on every OS; Windows is not supported by DeepChem's note |
| GNINA docking through `GninaPoseGenerator` | Protein `.pdb` + ligand `.sdf` | RDKit stack | Linux GNINA executable; CUDA >= 10.1 recommended for fast CNN scoring |
| Input preparation with `prepare_inputs` | Protein PDB/PDB ID and ligand PDB/SMILES | RDKit, `pdbfixer`, `openmm` | Network access if fetching by PDB ID |
| Complex fingerprints/voxel grids | Prepared 3D ligand/protein files | RDKit stack; some neighbor-list paths require `mdtraj` | None |
| Material composition features | Formula/composition | `pymatgen`; `matminer` for element-property features | None |
| Material structure features | `pymatgen.core.Structure` | `pymatgen`; `matminer` for Sine Coulomb; `networkx`/`scipy` for LCNN | Network may be needed for CGCNN atom init download |
| DFT/XC/SCF | DFT entries/systems | `torch`, `dqc`, related scientific stack | GPU optional; CPU smoke tests should be possible if deps are installed |

## File Format Gates

- Docking APIs use `(protein_file, ligand_file)` ordering.
- Many complex featurizers use `(ligand_or_molecule_file, protein_file)` ordering. Check class-specific docs before reusing docking tuples.
- `VinaPoseGenerator` accepts protein `.pdb` plus ligand `.sdf` for conversion, or preprepared `.pdbqt` files. When both are `.pdbqt`, generated RDKit complexes are not returned.
- `GninaPoseGenerator` requires protein `.pdb` and ligand `.sdf`.
- Pocket featurization with `BindingPocketFeaturizer` expects a protein PDB and `CoordinateBox` pockets.
- Material structure featurizers expect `pymatgen.core.Structure`, not molecule files or SMILES.
- Composition featurizers expect composition-like inputs, not PDB/SDF files.

## Environment Expectations

- A base DeepChem import plus simple molecular featurizers does not prove docking, material, or DFT workflows are available.
- Missing TensorFlow/JAX/Torch warnings during base import are not automatically failures for docking or pocket finding; they matter only when the selected workflow needs that backend.
- `torch` is required for DeepChem DFT model modules. Do not import DFT model surfaces in an environment where `torch` is intentionally absent.
- `tensorflow` and `jax` are not required for the docking APIs listed here, but may be relevant to unrelated model choices.
- CUDA availability should be checked separately from Python imports. GNINA CNN scoring and some torch models may benefit from GPU, but importability is the first gate.

## Safe Preflight Pattern

1. Identify the user goal and input files.
2. Run or adapt `scripts/check_structure_dependencies.py`.
3. Validate file extensions and tuple ordering before loading structures.
4. Start with a no-docking smoke action: import class, instantiate it, or parse the structure.
5. Use small `num_modes` and low `exhaustiveness` only after preflight passes.
6. Record which optional gate failed instead of installing broad extras unprompted.
