# OpenFF Toolkit Package Overview

## Purpose

OpenFF Toolkit is a Python package for molecule processing, topology construction, optional cheminformatics backend dispatch, and SMIRNOFF force-field loading/application. The core public import is `openff.toolkit`.

## Main Object Model

| Object or module | Role | Owning sub-skill |
| --- | --- | --- |
| `Molecule` | Single chemical graph plus conformers, charges, atom/bond metadata, IO, conversion, enumeration, and SMARTS matching. | `../sub-skills/molecules-and-io/SKILL.md` |
| `Topology` | Collection of one or more molecules plus hierarchy metadata, constraints, positions/box handoff, and conversion to OpenMM/PDB/MDTraj-style structures. | `../sub-skills/topology-and-systems/SKILL.md` |
| `ForceField` | SMIRNOFF `.offxml` loader/editor/applier that labels molecules and creates Interchange/OpenMM systems from a topology. | `../sub-skills/smirnoff-force-fields/SKILL.md` |
| Toolkit wrappers | RDKit, OpenEye, AmberTools, NAGL, and BuiltIn dispatch layer for file IO, conformers, charges, SMARTS, and conversions. | `../sub-skills/toolkit-backends/SKILL.md` |

## Installation Shape

Use conda-forge for normal environments:

```bash
mamba create -n openff-toolkit -c conda-forge openff-toolkit
```

The full `openff-toolkit` conda package installs recommended optional toolkits such as RDKit and AmberTools. The `openff-toolkit-base` package is narrower and expects users to supply optional backends separately.

## Workflow Dependencies

- Molecule file IO and SMILES handling normally need RDKit or OpenEye.
- `Molecule.assign_partial_charges()` depends on the requested charge method and available wrappers.
- `ForceField("openff-2.3.0.offxml")` requires installed force-field data or a direct path to an `.offxml` file.
- `ForceField.create_interchange()` needs the Interchange package and any charge/back-end dependencies required by the force field.
- `ForceField.create_openmm_system()` also requires OpenMM compatibility.
- Notebook visualization may require `nglview`, RDKit drawing support, or notebook-specific display packages.

## No Console CLI

This repository snapshot exposes no package console scripts through distribution metadata. Treat OpenFF Toolkit as a Python API package and use the bundled skill scripts for safe diagnostics.

## Minimal Smoke Pattern

```python
from openff.toolkit import ForceField, Molecule, Topology

mol = Molecule.from_smiles("CCO")
top = Topology.from_molecules([mol])
ff = ForceField("openff-2.3.0.offxml")
labels = ff.label_molecules(top)
print(mol.n_atoms, top.n_atoms, labels[0].keys())
```

If this fails, diagnose in this order: package import, backend availability, force-field discovery, molecule graph/stereochemistry, topology completeness, then Interchange/OpenMM dependencies.
