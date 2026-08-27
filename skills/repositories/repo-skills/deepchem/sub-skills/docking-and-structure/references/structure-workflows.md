# Structure Workflow Selection

DeepChem separates structural work into pocket discovery, pose generation/docking, complex featurization, material featurization, and DFT-style modeling. Pick the smallest workflow that answers the user request before installing optional dependencies or running expensive binaries.

## Pocket Finding

Use pocket finding when the user needs candidate binding regions on a protein, a docking box, or a quick geometric screen without generating ligand poses.

Typical plan:

1. Confirm the protein file is a readable PDB-like structure with 3D coordinates.
2. Create `deepchem.dock.ConvexHullPocketFinder(scoring_model=None, pad=5.0)`.
3. Call `find_pockets(protein_file)` for merged `CoordinateBox` pocket candidates, or `find_all_pockets(protein_file)` for unmerged hull-face boxes.
4. Optionally featurize returned pockets with `deepchem.feat.BindingPocketFeaturizer().featurize(protein_file, pockets)` when `mdtraj` is installed.

Use `deepchem.dock.extract_active_site(protein_file, ligand_file, cutoff=4.0)` when a known ligand defines the active site. This returns a `CoordinateBox` and pocket coordinates around protein atoms contacting the ligand.

## Docking Pose Generation

Use docking when the user needs docked ligand poses, Vina/GNINA scores, or output PDBQT poses. Require a stricter dependency gate than pocket finding.

Typical Vina plan:

1. Verify `vina` Python package import works; the optional `vina` command is useful for environment sanity but DeepChem's Vina generator imports `from vina import Vina`.
2. Use protein `.pdb` plus ligand `.sdf` when DeepChem should convert to PDBQT, or preprepared `.pdbqt` files when the user only needs scores and can tolerate no RDKit complex objects being returned.
3. Choose either explicit `centroid` and `box_dims`, whole-protein docking, or pockets via `VinaPoseGenerator(pocket_finder=ConvexHullPocketFinder(...))` plus `num_pockets`.
4. Run with small `exhaustiveness` and `num_modes` for smoke tests; increase only after input preparation succeeds.
5. If wrapping in `Docker`, set `use_pose_generator_scores=True` to use Vina scores, or provide both `featurizer` and `scoring_model` together.

Typical GNINA plan:

1. Confirm Linux and external GNINA executable availability; DeepChem may download GNINA into its data directory if missing.
2. Use protein `.pdb` and ligand `.sdf`; GNINA generator rejects other formats.
3. Ensure CUDA expectations are clear. GNINA can run without fast GPU scoring depending on build, but production CNN scoring is CUDA-sensitive.
4. Treat GNINA scores as a matrix containing binding affinity, CNN pose score, and CNN affinity for each mode.

## Complex Featurization

Use complex featurizers when the user needs ML features from already prepared structures, not new docked poses.

- `AtomicConvFeaturizer`: produces atomic coordinates, neighbor lists, and atomic-number arrays for two fragments plus the combined complex. Requires accurate atom count limits and usually RDKit-readable ligand/protein files.
- `NeighborListComplexAtomicCoordinates`: returns complex coordinates and neighbor lists using a distance cutoff; `mdtraj` is required for neighbor-list computation.
- `RdkitGridFeaturizer`: builds flat or voxelized protein-ligand features with feature types such as `ecfp`, `splif`, `salt_bridge`, `charge`, `hbond`, `pi_stack`, and `cation_pi`. Sanitization affects aromatic features; `sybyl` is ignored because it is not implemented.
- `ContactCircularFingerprint` and `ContactCircularVoxelizer`: focus on ECFP fragments around inter-fragment contacts.
- `SplifFingerprint` and `SplifVoxelizer`: encode close atom-pair SPLIF interactions in contact bins.
- Voxelizers (`ChargeVoxelizer`, `SaltBridgeVoxelizer`, `CationPiVoxelizer`, `PiStackVoxelizer`, `HydrogenBondVoxelizer`, `HydrogenBondCounter`) are useful when the downstream model expects spatial channels or interaction counts.

Complex featurizers generally expect tuples of structure file names such as `(ligand_file, protein_file)` or `(mol_pdb_file, protein_pdb_file)`. Check the exact class before assuming protein-first ordering; docking APIs use `(protein_file, ligand_file)`.

## Material and Crystal Featurization

Use material featurizers for inorganic crystals, compositions, surfaces, and periodic structures.

- Composition-only: `ElemNetFeaturizer` and `ElementPropertyFingerprint` operate on composition-like inputs. They require `pymatgen`; `ElementPropertyFingerprint` also requires `matminer`.
- Periodic structures: `SineCoulombMatrix`, `CGCNNFeaturizer`, and `LCNNFeaturizer` operate on `pymatgen.core.Structure` objects. `SineCoulombMatrix` requires `matminer`; `CGCNNFeaturizer` downloads atom initialization data; `LCNNFeaturizer` additionally requires graph/surface metadata such as site properties.
- Model handoff: material structure features often pair with material models such as CGCNN-style models; route model training details to `../model-training/`.

## DFT and Quantum Surfaces

Use DFT surfaces only when the user explicitly asks about DeepChem DFT data entries, neural XC functionals, SCF wrappers, or `dqc` integration. These are not base-install workflows.

Typical gate:

1. Confirm `torch` import before importing `deepchem.models.dft` modules that subclass Torch modules.
2. Confirm `dqc` and any quantum chemistry extras for dataset entries or SCF execution.
3. Keep DFT data loading and dataset preparation separate from model execution; route general data questions to `../data-and-molnet/`.
4. Treat GPU acceleration as optional but environment-specific; focus first on importability and small CPU smoke checks.

## Minimal User Questions

Ask for the following before running structure work:

- Is the goal pocket discovery, docking pose generation, fixed complex features, material features, or DFT?
- What are the available input formats: protein `.pdb`, receptor `.pdbqt`, ligand `.sdf`, ligand `.pdbqt`, `pymatgen` structure, composition, or DFT YAML/entry objects?
- Are optional dependencies and binaries already installed, or should the task stop at an installation/check plan?
- For docking, is there an explicit binding-site center/box, a known ligand, or should DeepChem detect pockets?
