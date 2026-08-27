# Molecules and I/O Workflows

Use these recipes to prepare ProLIF inputs. After molecules are prepared, route fingerprint execution to `../../fingerprints/SKILL.md` and interaction choice to `../../interactions/SKILL.md`.

## Smoke-Test the Installed Package Data

Run the bundled helper with no arguments:

```bash
python scripts/inspect_inputs.py
```

Expected use: confirm ProLIF, RDKit, MDAnalysis, package data, `Molecule.from_mda`, and the built-in SDF/MOL2 examples can be imported and counted. The helper prints JSON and does not write files.

## Convert an MDAnalysis Selection

```python
import MDAnalysis as mda
import prolif as plf

u = mda.Universe(topology_path, trajectory_path)
ligand_ag = u.select_atoms("resname LIG")
protein_ag = u.select_atoms("protein and byres around 6.5 group ligand", ligand=ligand_ag)

ligand_mol = plf.Molecule.from_mda(ligand_ag)
protein_mol = plf.Molecule.from_mda(protein_ag)
```

Checklist:

- Verify each selection has atoms before conversion: `selection.n_atoms > 0`.
- Pass a `selection` string only when converting from a full `Universe`; if you already have an `AtomGroup`, pass it directly.
- Forward converter arguments such as `NoImplicit=False`, `force=True`, or newer MDAnalysis inferrer arguments only when they solve a known conversion problem.
- For multi-segment systems, decide whether residue identity should use chain IDs or segment indices and pass `use_segid=True` or `False` explicitly when reproducibility matters.

## Handle Multi-Segment `use_segid` Labels

`Molecule.from_mda(..., use_segid=None)` automatically uses segment indices as the residue `chain` field when an atom group has more segment indices than chain IDs. This prevents residues from different segments collapsing into the same `ResidueId` when chain IDs are missing or reused.

```python
water = u.select_atoms("resname TIP3 and byres around 6 protein")
water_mol = plf.Molecule.from_mda(water, use_segid=True, NoImplicit=False)
print([str(res.resid) for res in water_mol][:5])
```

Guidance:

- Use `use_segid=True` when segment identity distinguishes otherwise duplicate residue labels.
- Use `use_segid=False` when chain IDs are authoritative and segment indices are implementation details.
- Use the same `use_segid` decision for all ligand/protein/water molecules that will later be compared by residue ID.
- If a downstream fingerprint object already has a resolved `use_segid` setting, reuse it when rebuilding molecules for plotting or inspection.

## Convert an RDKit Molecule

```python
from rdkit import Chem
import prolif as plf

rdmol = Chem.MolFromMolFile("ligand.sdf", removeHs=False)
ligand_mol = plf.Molecule.from_rdkit(rdmol, resname="LIG", resnumber=1, chain="A")
```

Use `Molecule.from_rdkit` instead of `Molecule(rdmol)` when the RDKit molecule may lack `AtomPDBResidueInfo`. ProLIF only checks the first atom for existing monomer info, so use consistent residue metadata across atoms when supplying pre-annotated RDKit molecules.

## Prepare SDF Docking Poses

```python
import prolif as plf

poses = plf.sdf_supplier("docking_output.sdf", sanitize=True, resname="LIG", resnumber=1, chain="A")
print(len(poses), poses[0].n_residues)

for ligand_mol in poses:
    assert isinstance(ligand_mol, plf.Molecule)
```

Use SDF when possible for docking poses because it preserves bond orders better than PDBQT. If RDKit sanitization fails but the file is otherwise trusted, retry with `sanitize=False` and inspect the resulting chemistry before fingerprinting.

## Prepare MOL2 Docking Poses

```python
import prolif as plf

poses = plf.mol2_supplier("docking_output.mol2", cleanup_substructures=True, sanitize=True)
first_pose = poses[0]
```

MOL2 notes:

- The supplier skips comment lines and treats every `@<TRIPOS>MOLECULE` block as a pose.
- `len(poses)` counts molecule blocks.
- Indexing works, including negative indices; slicing is not implemented.
- Retry with `cleanup_substructures=False` or `sanitize=False` only as a targeted workaround for MOL2 chemistry that RDKit cannot standardize.

## Prepare PDBQT Docking Poses

PDBQT lacks bond orders and charges and may omit many hydrogens. ProLIF therefore requires a template molecule that exactly matches the ligand chemistry.

```python
from pathlib import Path
from rdkit import Chem
import prolif as plf

template = Chem.MolFromSmiles("...")
pdbqt_files = sorted(Path("vina_split_outputs").glob("*.pdbqt"))
poses = plf.pdbqt_supplier(pdbqt_files, template, resname="LIG", resnumber=1, chain="G")

print(len(poses), poses[0].GetNumAtoms())
```

Checklist:

- Prefer Meeko or another chemistry-aware route to produce SDF if available.
- Do not rely on generic OpenBabel PDBQT-to-SDF conversion to infer bond orders/charges correctly.
- Split multi-model PDBQT files into one model per file before MDAnalysis parsing.
- Provide a template from SMILES, SDF, MOL2, or another RDKit-readable source with correct bond orders and formal charges.
- The PDBQT supplier removes all hydrogens before assigning bond orders from the template, then restores hydrogens present in the PDBQT coordinates.

## Prepare PDB Structures With Explicit Hydrogens

Recommended path for many prepared PDB protein structures:

```python
import MDAnalysis as mda
import prolif as plf

u = mda.Universe("prepared_protein.pdb")
protein_mol = plf.Molecule.from_mda(u)
```

If residue names are non-standard or bond orders are uncertain, use `MoleculeStandardizer`:

```python
from rdkit import Chem
from prolif.io import MoleculeStandardizer, cif_template_reader

lig_template = cif_template_reader("LIG.cif")
standardizer = MoleculeStandardizer(templates=[lig_template])
system_mol = standardizer("prepared_system.pdb")
ligand_mol, protein_mol = plf.split_molecule(system_mol, lambda resid: resid.name == "LIG")
```

PDB preparation reminders:

- Explicit hydrogens are important for hydrogen-bond-sensitive workflows unless the later interaction setup intentionally uses implicit-hydrogen modes.
- For PDB files, either all bonds should be explicit or none should be explicit; partial bond records can block MDAnalysis bond guessing.
- For ligand-only PDB input, use an external template or SMILES with RDKit to assign correct bond orders before `Molecule.from_rdkit`.

## Standardize Non-Standard Residues

```python
from rdkit import Chem
from prolif.io import MoleculeStandardizer, cif_template_reader

custom_templates = [
    cif_template_reader("TPO.cif"),
    ("BEN", Chem.MolFromSmiles("NC(=N)c1ccccc1")),
]
standardizer = MoleculeStandardizer(templates=custom_templates)
protein_mol = standardizer("prepared_with_nonstandard_residues.pdb")
```

Template guidance:

- CIF templates come from ligand/component definitions and are read with `cif_template_reader`.
- RDKit molecule templates are `(residue_name, Chem.Mol)` tuples.
- User templates take priority over built-in standard amino acid templates.
- SMILES templates for residue fragments may need to represent the residue after peptide-bond splitting, not a standalone capped molecule.

## Split a Complex Into Ligand, Water, and Protein

```python
import prolif as plf

system_mol = plf.Molecule.from_mda(u)
water_mol, non_water_mol = plf.split_molecule(system_mol, lambda resid: resid.name in {"HOH", "WAT", "TIP3"})
ligand_mol, protein_mol = plf.split_molecule(non_water_mol, lambda resid: resid.name == "LIG")
```

`split_molecule` works at residue granularity. The returned molecules preserve the original residue objects, including information produced by `MoleculeStandardizer`.

## Inspect Before Fingerprinting

Before passing objects to the fingerprint sub-skill, collect:

- Number of ligand poses and residues.
- Protein molecule residue count and representative residue labels.
- Whether residue IDs use chain IDs or segment indices.
- Whether hydrogens are present where expected.
- Whether parsing required non-default `sanitize`, `cleanup_substructures`, converter, or template choices.

Then continue with `../../fingerprints/SKILL.md` for `Fingerprint.run`, `run_from_iterable`, `generate`, exports, and parallel execution.
