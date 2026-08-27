---
name: openff-toolkit
description: "Use OpenFF Toolkit for molecule processing, SMIRNOFF force fields,
  topology/system preparation, and optional chemistry backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFF Toolkit

Use this repo skill when a task involves the Open Force Field Toolkit (`openff.toolkit`), especially `Molecule`, `Topology`, SMIRNOFF `.offxml` force fields, toolkit wrappers, parameter assignment, molecule/topology conversion, conformers, charges, PDB handling, OpenMM/Interchange handoff, or force-field troubleshooting.

## Read First

- `references/package-overview.md` summarizes package purpose, install shape, important concepts, and cross-skill workflow order.
- `references/troubleshooting.md` covers cross-cutting install/import, optional dependency, backend, force-field discovery, and workflow routing failures.
- `references/repo-provenance.md` records the source snapshot and evidence paths used to create this skill; read it before deciding whether the skill is stale.
- `scripts/check_openff_toolkit.py --json` checks importability, version, available force fields, core classes, and backend wrapper status in the current Python environment.

## Route by Task

| Task signal | Use this entry point | Why |
| --- | --- | --- |
| Build a molecule from SMILES, mapped SMILES, SDF/MOL/SMI/PDB, RDKit/OpenEye objects, conformers, partial charges, stereochemistry, tautomers, SMARTS, visualization, or molecule graph checks | `sub-skills/molecules-and-io/SKILL.md` | Focuses on single-molecule API usage and safe IO/validation recipes. |
| Assemble systems from molecules, load PDB files, handle proteins/HETATM records, manage hierarchy metadata, convert to/from OpenMM/MDTraj, write PDB, add constraints, or prepare topologies for parameterization | `sub-skills/topology-and-systems/SKILL.md` | Owns multi-molecule `Topology` workflows and PDB/biopolymer assumptions. |
| Load or edit `.offxml`, discover installed OpenFF force fields, inspect/modify SMIRNOFF handlers, label assigned parameters, serialize force fields, create Interchange/OpenMM systems, or troubleshoot SMIRNOFF errors | `sub-skills/smirnoff-force-fields/SKILL.md` | Owns `ForceField` and SMIRNOFF parameter workflows. |
| Choose RDKit/OpenEye/AmberTools/NAGL/BuiltIn wrappers, inspect `GLOBAL_TOOLKIT_REGISTRY`, control registry precedence, diagnose missing optional dependencies, unsupported formats, or charge method failures | `sub-skills/toolkit-backends/SKILL.md` | Owns optional backend and registry behavior. |

## Common Workflow Order

1. Check the environment with `scripts/check_openff_toolkit.py --json` if importability, force-field discovery, or optional backend availability is uncertain.
2. Create or validate `Molecule` objects with `sub-skills/molecules-and-io/SKILL.md`.
3. Build the `Topology` or load a PDB/system with `sub-skills/topology-and-systems/SKILL.md`.
4. Load/apply/edit a SMIRNOFF force field with `sub-skills/smirnoff-force-fields/SKILL.md`.
5. Return to `sub-skills/toolkit-backends/SKILL.md` when the failure is caused by an unavailable wrapper, unsupported file format, charge method, or registry ordering.

## Installation and Import Baseline

Prefer package-manager installation for normal users because OpenFF Toolkit depends on compiled chemistry/simulation packages:

```bash
mamba create -n openff-toolkit -c conda-forge openff-toolkit
```

Minimal import check:

```python
from openff.toolkit import ForceField, Molecule, Topology
from openff.toolkit.utils.toolkits import GLOBAL_TOOLKIT_REGISTRY

molecule = Molecule.from_smiles("CCO")
topology = Topology.from_molecules([molecule])
force_field = ForceField("openff-2.3.0.offxml")
print(molecule.n_atoms, topology.n_molecules, force_field.registered_parameter_handlers)
print(GLOBAL_TOOLKIT_REGISTRY.registered_toolkit_versions)
```

If `ForceField("openff-2.3.0.offxml")` fails, inspect available force fields and package installation before changing molecule/topology code.

## Safe Defaults

- Use Python versions supported by the installed release; this repository snapshot declares Python `>=3.12`.
- Prefer conda-forge packages for RDKit, AmberTools, OpenMM, Interchange, OpenFF force fields, and OpenFF units.
- Keep toolkit selection explicit for reproducibility: pass `toolkit_registry=` or a wrapper when behavior must match RDKit, OpenEye, AmberTools, or BuiltIn paths.
- Treat PDB files as topology/system inputs, not reliable molecule graph sources unless hydrogens, elements, bonds, and unique molecules are known.
- Treat `.offxml` files as SMIRNOFF force-field sources; preserve originals when troubleshooting version, handler, or parameter errors.

## What Not To Do

- Do not assume OpenEye, AmberTools, or NAGL are available just because `openff.toolkit` imports.
- Do not use a bare PDB file as the only source of small-molecule bond orders; prepare `unique_molecules` when loading PDB systems.
- Do not mutate `GLOBAL_TOOLKIT_REGISTRY` globally unless the task explicitly needs process-wide behavior; prefer temporary context managers or explicit arguments.
- Do not route force-field parameter problems to molecule IO only; use the SMIRNOFF sub-skill once molecules/topologies are valid.
