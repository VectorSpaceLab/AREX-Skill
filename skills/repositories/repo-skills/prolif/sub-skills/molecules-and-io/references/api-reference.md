# Molecules and I/O API Reference

This reference summarizes the ProLIF input-preparation API needed before fingerprinting. It intentionally excludes interaction setup, fingerprint execution, and plotting.

## Core Molecule Objects

| API | Use | Key Notes |
| --- | --- | --- |
| `prolif.Molecule(mol, use_segid=False, residues=None)` | Wrap an RDKit `Chem.Mol` that already has residue metadata and one conformer. | Sets each atom `mapindex`, splits the molecule into `Residue` objects unless `residues` is provided, and stores them in `mol.residues`. |
| `Molecule.from_mda(obj, selection=None, use_segid=None, **kwargs)` | Convert an MDAnalysis `Universe` or `AtomGroup` to a ProLIF molecule. | Applies `selection` if provided, rejects empty atom groups, forwards `**kwargs` to the MDAnalysis RDKit converter, and auto-selects segment indices when there are more segments than chains unless `use_segid` is explicit. |
| `Molecule.from_rdkit(mol, resname="UNL", resnumber=1, chain="", use_segid=False)` | Convert an RDKit molecule into a ProLIF molecule. | If the first atom lacks `AtomPDBResidueInfo`, ProLIF deep-copies the molecule and attaches residue metadata to every atom using the supplied defaults. |
| `split_molecule(mol, predicate)` | Split a ProLIF molecule into two ProLIF molecules by residue ID. | `predicate` receives each `ResidueId`; the first returned molecule contains residues for which the predicate is true. Existing residue objects are preserved. |

`Molecule` behaves like an RDKit `Chem.Mol` with extra residue access. Common properties include `mol.n_residues`, `mol.residues`, residue iteration with `for residue in mol`, `mol.centroid`, and `mol.xyz`.

## Residue Objects

| API | Use | Key Notes |
| --- | --- | --- |
| `ResidueId(name="UNK", number=0, chain=None)` | Stable residue identifier used as a dictionary-like key. | Empty names become `UNK`; missing numbers become `0`; empty chains become `None`; whitespace is stripped. |
| `ResidueId.from_string(resid_str)` | Parse labels such as `ALA10.A`, `GLU33`, `LYS.B`, `42`, `.D`, `TIP31.1`, or `8NU1.A`. | Use an explicit `ResidueId` object when unusual chain characters make string parsing ambiguous. |
| `ResidueId.from_atom(atom, use_segid=False)` | Build a residue ID from an RDKit atom's monomer metadata. | `use_segid=True` stores the atom segment number as the residue `chain` field instead of `GetChainId()`. |
| `Residue(mol, use_segid=False)` | RDKit-like molecule representing one residue. | `residue.resid` is a `ResidueId`; `str(residue)` returns the residue label. |
| `ResidueGroup(residues)` | Container for residues on a `Molecule`. | Supports lookup by index, `ResidueId`, or residue-label string. Exposes arrays `name`, `number`, and `chain`. |
| `ResidueGroup.select(mask)` | Select residues with a boolean mask. | Build masks from `rg.name`, `rg.number`, and `rg.chain`; combine with NumPy-style `&`, `|`, `^`, and `~`. |

Example residue selection:

```python
rg = protein_mol.residues
active_site = rg.select((rg.chain == "A") & (rg.number >= 30) & (rg.number <= 60))
acidic = rg.select((rg.name == "ASP") | (rg.name == "GLU"))
```

## Docking Pose Suppliers

| API | Use | Important Behavior |
| --- | --- | --- |
| `sdf_supplier(path, sanitize=True, **kwargs)` | Read an SDF file as a reusable sequence of ProLIF `Molecule` poses. | Uses RDKit `SDMolSupplier` with `removeHs=False`; accepts residue defaults through `**kwargs`; supports indexing, slicing, iteration, and `len()`. |
| `mol2_supplier(path, cleanup_substructures=True, sanitize=True, **kwargs)` | Read a MOL2 file as a reusable sequence of ProLIF `Molecule` poses. | Counts `@<TRIPOS>MOLECULE` records; supports indexing and iteration; slicing is not implemented; cleanup can standardize some MOL2 substructures. |
| `pdbqt_supplier(paths, template, converter_kwargs=None, **kwargs)` | Read one or more single-model PDBQT files as ProLIF `Molecule` poses. | Requires a template RDKit molecule with correct bond orders and charges; uses MDAnalysis plus template bond-order assignment; supports indexing, slicing, iteration, and `len()`. |

All suppliers yield `Molecule` objects suitable for `Fingerprint.run_from_iterable` after a protein/reference molecule is prepared. Fingerprint execution details belong in `../../fingerprints/SKILL.md`.

## Standardization and Templates

| API | Use | Key Notes |
| --- | --- | --- |
| `from prolif.io import MoleculeStandardizer` | Standardize residue names and fix bond orders on PDB/RDKit/ProLIF molecule inputs. | Accepts `Molecule`, RDKit `Chem.Mol`, or `.pdb` path inputs. A `Molecule` input is modified in place. |
| `MoleculeStandardizer(templates=None)` | Build a standardizer from optional CIF documents or RDKit molecule templates. | User templates take priority, and built-in standard amino acid templates are always appended as fallback. |
| `from prolif.io import cif_template_reader` | Read a CIF file into a `gemmi.cif.Document` template source. | Each CIF block can become a template engine keyed by residue name. |
| `RDKitMolTemplateEngine(name, mol)` | Template engine from an RDKit molecule. | Use when a residue template is easier to express as a prepared RDKit molecule. |
| `CIFTemplateEngine(name, block)` | Template engine from one CIF block. | Used internally for CIF-backed standardization. |

`MoleculeStandardizer` guesses a forcefield from residue names, maps common forcefield residue names to ProLIF standard residue names, warns when heavy atom counts differ from templates, and raises if a residue has no matching standard or custom template.

## Package Data

`prolif.datafiles` exposes installed package examples:

- `prolif.datafiles.TOP`: example topology PDB path.
- `prolif.datafiles.TRAJ`: example trajectory path.
- `prolif.datafiles.WATER_TOP`: water-bridge example topology path.
- `prolif.datafiles.WATER_TRAJ`: water-bridge example trajectory path.
- `prolif.datafiles.datapath`: package data directory containing Vina, MOL2, PDB, CIF, and implicit-H-bond examples.

Use these for smoke checks or examples, not as required user runtime data.

## Import Surface

Common imports:

```python
import prolif as plf
from prolif import Molecule, ResidueId, sdf_supplier, mol2_supplier, pdbqt_supplier, split_molecule
from prolif.io import MoleculeStandardizer, cif_template_reader
from rdkit import Chem
import MDAnalysis as mda
```

Top-level ProLIF exports include `Molecule`, `ResidueId`, `sdf_supplier`, `mol2_supplier`, `pdbqt_supplier`, `split_molecule`, and `datafiles`. `MoleculeStandardizer` and `cif_template_reader` are imported from `prolif.io`.
