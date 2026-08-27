---
name: force-fields-modeling
description: "Choose and troubleshoot OpenMM force fields, model-building
  workflows, parameterized input formats, and ForceField XML authoring. Use when
  working with ForceField.createSystem, Modeller, bundled force-field XML files,
  residue template failures, solvation/hydrogenation/membranes,
  AMBER/CHARMM/GROMACS/Tinker inputs, or ffxml validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT, GPL, LGPL
---

# Force Fields and Modeling

Use this sub-skill when a task is about preparing a molecular model or parameterizing it before a simulation in OpenMM.

## Route Here For

- Selecting bundled OpenMM `ForceField` XML files, compatible water/ion files, implicit solvent files, or polarizable force fields.
- Calling `ForceField.createSystem()` with correct `nonbondedMethod`, cutoff, constraints, `rigidWater`, `hydrogenMass`, residue template, and external-bond options.
- Editing structures with `Modeller`: add missing hydrogens, solvent, ions, membranes, extra particles, or remove incompatible water.
- Diagnosing `No template found for residue` and related residue-template, terminal variant, water-model, bond, or extra-particle mismatches.
- Loading parameterized inputs from AMBER, CHARMM, GROMACS, or Tinker instead of using `ForceField` XML directly.
- Authoring or validating practical OpenMM force-field XML (`ffxml`) files and residue template generators.

## Start With These References

- `references/forcefield-api-and-data.md` for `ForceField`, bundled XML families, `createSystem()` options, and AMBER/CHARMM/GROMACS/Tinker input routes.
- `references/model-building-recipes.md` for `Modeller` workflows: hydrogens, solvent, ions, water conversion, membranes, and extra particles.
- `references/forcefield-xml-authoring.md` for ffxml structure, residue templates, patches, standard force tags, custom force wiring, and template generators.
- `references/troubleshooting.md` for template mismatch diagnosis, water/ion compatibility, periodic-box and include-path problems.

## Practical Workflow

1. Identify whether the inputs are coordinates plus topology needing a `ForceField`, or already-parameterized files such as AMBER `prmtop`, CHARMM `psf`, GROMACS `top`, or Tinker `xyz/key/prm`.
2. Choose force-field XML files as a compatible set: main biopolymer file plus the matching water/ion or implicit-solvent file when needed.
3. Use `Modeller` before `createSystem()` when the topology lacks hydrogens, solvent, membranes, or force-field-required extra particles.
4. Run `forcefield.getUnmatchedResidues(topology)` or `forcefield.getMatchingTemplates(topology)` before debugging a full simulation when template matching is uncertain.
5. Build the `System` with `createSystem()` using nonbonded settings that match the topology: periodic boxes generally pair with `PME`/cutoffs; implicit solvent supports only non-periodic or limited cutoff choices.
6. Keep production dynamics, integrator choice, reporter setup, and platform precision decisions in sibling sub-skills unless they directly affect model parameterization.

## Bundled Script

Use `scripts/forcefield_modeling_check.py` as a lightweight smoke check for an OpenMM installation and a minimal force-field/model-building path. It builds a tiny in-memory water topology, verifies template matching, creates a `System`, and prints a JSON summary without requiring source checkout files.

```bash
python scripts/forcefield_modeling_check.py
```

## Boundaries

- For running or restarting complete simulations, use `simulation-workflows`.
- For custom mathematical force expressions or custom integrator algorithms beyond ffxml wiring, use `custom-forces-integrators`.
- For CUDA/OpenCL/HIP/CPU platform selection, precision, and performance tuning, use `platforms-performance`.
- For modifying OpenMM internals, plugins, C++ extension development, or tests, use `development-extensions`.
