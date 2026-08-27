# Docking and Structure API Reference

This reference lists the DeepChem APIs most relevant to structural workflows. It is intentionally dependency-aware: many objects import in base DeepChem but fail only when optional packages or external binaries are used.

## Docking APIs

### `deepchem.dock.ConvexHullPocketFinder(scoring_model=None, pad=5.0)`

Finds candidate protein pockets with a convex-hull geometry heuristic.

- `find_pockets(macromolecule_file)`: loads a structure, builds hull-face boxes, merges overlapping boxes, and returns `CoordinateBox` objects.
- `find_all_pockets(protein_file)`: returns all hull-face boxes without the same final pocket selection behavior.
- `scoring_model`: accepted but basic usage leaves it as `None`.
- `pad`: angstrom padding around pocket atoms.

### `deepchem.dock.extract_active_site(protein_file, ligand_file, cutoff=4.0)`

Computes a known-ligand active-site box by selecting protein atoms close to ligand atoms. It loads the protein without hydrogens and the ligand with hydrogens/charges.

### `deepchem.dock.VinaPoseGenerator(pocket_finder=None)`

Generates AutoDock Vina poses and scores through the Python `vina` package.

Important call arguments for `generate_poses((protein_file, ligand_file), ...)`:

- `centroid`: optional length-3 NumPy array for the box center.
- `box_dims`: optional length-3 NumPy array for box dimensions.
- `exhaustiveness`: search effort; use low values for smoke tests.
- `num_modes`: number of requested binding modes.
- `num_pockets`: requires `pocket_finder` at construction time and docks only the first selected pockets.
- `out_dir`: output directory for generated intermediate and pose files.
- `generate_scores`: returns Vina scores when true.
- Extra kwargs: `cpu`, `min_rmsd`, `max_evals`, `energy_range`.

Input behavior:

- Protein `.pdb` and ligand `.sdf` are converted to PDBQT after adding hydrogens/charges.
- If both inputs are `.pdbqt`, DeepChem returns scores only when `generate_scores=True`; it does not return RDKit complex objects.
- If `num_pockets` is set with no pocket finder, DeepChem raises a `ValueError`.

### `deepchem.dock.GninaPoseGenerator()`

Generates GNINA poses and score matrix through a GNINA executable.

- Linux-only in DeepChem's generator.
- Protein must be `.pdb`; ligand must be `.sdf`.
- `generate_poses(..., generate_scores=True)` returns `(docked_complexes, scores)` where scores include affinity, CNN pose score, and CNN affinity.
- Extra kwargs are written into the GNINA configuration file.
- CUDA support is a deployment question; do not assume it from DeepChem alone.

### `deepchem.dock.Docker(pose_generator, featurizer=None, scoring_model=None)`

A generic wrapper around a pose generator and optional scoring model.

- `featurizer` and `scoring_model` must both be set or both omitted.
- `dock((protein_file, ligand_file), use_pose_generator_scores=True)` yields `(posed_complex, score)` using pose-generator scores.
- If `scoring_model` is supplied, DeepChem featurizes and scores generated poses itself; use this only after validating the complex featurizer and model input shape.

## Complex and Pocket Featurizers

### `deepchem.feat.BindingPocketFeaturizer()`

Counts residue types in each pocket box for a protein. Requires `mdtraj` and pockets from a binding pocket finder. Output shape is `(len(pockets), 24)` for the built-in residue vocabulary.

### `deepchem.feat.AtomicConvFeaturizer(...)`

Creates AtomicConv-style coordinates, neighbor lists, and atomic-number arrays for two fragments and their complex.

Key parameters:

- `frag1_num_atoms`, `frag2_num_atoms`, `complex_num_atoms`: hard maximums; too-small values cause skipped complexes.
- `max_num_neighbors`, `neighbor_cutoff`: neighbor-list construction.
- `strip_hydrogens=True`: removes hydrogens before feature packing.

### `deepchem.feat.NeighborListComplexAtomicCoordinates(max_num_neighbors=None, neighbor_cutoff=4)`

Returns `(system_coords, system_neighbor_list)` for a `(molecule_file, protein_file)` pair. Requires `mdtraj` for neighbor-list computation.

### `deepchem.feat.RdkitGridFeaturizer(...)`

Flexible flat/voxel structure featurizer.

- Default `feature_types=['ecfp']`.
- Flat features include `ecfp_ligand`, `ecfp_hashed`, `splif_hashed`, `hbond_count`.
- Voxel features include `ecfp`, `splif`, `salt_bridge`, `charge`, `hbond`, `pi_stack`, `cation_pi`.
- Predefined sets: `flat_combined`, `voxel_combined`, `all_combined`.
- `sanitize=True` is required for features that depend on aromaticity such as `pi_stack`, `cation_pi`, and `ecfp_ligand`; otherwise they are ignored.
- `sybyl` is listed but not implemented and is ignored.

### Contact/SPLIF/Voxel APIs

- `ContactCircularFingerprint(cutoff=4.5, radius=2, size=8)`: returns contact-region circular fingerprints with shape `(2*size,)` for a two-fragment complex.
- `ContactCircularVoxelizer(cutoff=4.5, radius=2, size=8, box_width=16.0, voxel_width=1.0, flatten=False)`: localizes contact circular features onto a voxel grid.
- `SplifFingerprint(contact_bins=None, radius=2, size=8)`: returns SPLIF contact-bin fingerprints with default bins `(0,2.0)`, `(2.0,3.0)`, `(3.0,4.5)`.
- `SplifVoxelizer(...)`: voxelized SPLIF interactions.
- `ChargeVoxelizer`, `SaltBridgeVoxelizer`, `CationPiVoxelizer`, `PiStackVoxelizer`, `HydrogenBondVoxelizer`, and `HydrogenBondCounter`: interaction-specific features for prepared complexes.

## Material APIs

- `ElemNetFeaturizer()`: composition vector of length 86 from a `pymatgen` composition-like input.
- `ElementPropertyFingerprint(data_source='matminer')`: matminer elemental property statistics; returns a NumPy vector and converts NaNs to zero.
- `SineCoulombMatrix(max_atoms=100, flatten=True)`: periodic crystal sine Coulomb features from a `pymatgen.core.Structure`; `flatten=True` returns eigenvalue-style fixed vectors.
- `CGCNNFeaturizer(radius=8.0, max_neighbors=12, step=0.2)`: crystal graph features as `GraphData`; downloads atom initialization data if needed.
- `LCNNFeaturizer(structure, aos, pbc, ns=1, na=1, cutoff=6.00)`: lattice/surface graph features. Requires primitive-cell site properties and per-datapoint active/spectator site metadata.

## DFT APIs

- `deepchem.models.dft.dftxc.DFTXC`: Torch module for exchange-correlation computation.
- `deepchem.models.dft.dftxc.XCModel`: DeepChem TorchModel-style wrapper for DFT XC training/evaluation.
- `deepchem.models.dft.nnxc.NNLDA`, `NNPBE`, `HybridXC`: neural XC components.
- `deepchem.models.dft.scf.XCNNSCF`: SCF wrapper that combines an XC model with a DFT entry.
- DFT data objects such as `DFTEntry` and `DFTSystem` are data/entry surfaces; route dataset loading details to `../data-and-molnet/`.

DFT modules import `torch`; execution may require `dqc` and compatible tensor/device setup. Base DeepChem installs commonly do not include these extras.
