---
name: system-preparation
description: "Prepare, minimize, equilibrate, serialize, and safely continue
  coronavirus molecular systems with OpenMM."
metadata:
  disco-role: operating
disable-model-invocation: true
license: CC BY 4.0
---

# System preparation

Use this route when a task needs an OpenMM molecular system prepared from a validated PDB, including solvation, ion placement, minimization, a short equilibration, XML/PDB serialization, or continuation at a longer timestep. The bundled scripts provide bounded, explicit-argument baselines that can be run from any working directory.

## Route by intent

- **Prepare an apo or straightforward protein system:** read [workflows.md](references/workflows.md), validate the input first with the sibling [structure-curation route](../structure-curation/SKILL.md), then use `scripts/simulate_openmm_system.py`.
- **Prepare a protein–ligand system:** read [ligand-complex.md](references/ligand-complex.md) before choosing OpenFF/SystemGenerator/ParmEd. Route residue naming, bond edits, and coordinate repair to [structure-curation](../structure-curation/SKILL.md).
- **Continue a serialized system:** confirm that the PDB, `system.xml`, and `state.xml` belong to the same preparation, then use `scripts/continue_openmm.py` and the continuation contract in [workflows.md](references/workflows.md).
- **Diagnose installation or platform behavior:** run `scripts/check_openmm_env.py --cpu-smoke`; treat CUDA as an optional probe, not as evidence of required capability.

## Operating sequence

1. Establish source-structure identity, chain selection, protonation/capping status, force-field assumptions, and output directory. Do not silently change a structure to make a simulation start.
2. Validate topology/positions using the sibling route. For a complex, confirm ligand chemistry and parameters before calling `createSystem`.
3. Start with the smallest deterministic CPU run. Use explicit `--steps` and `--iterations`; never inherit historical multi-nanosecond defaults into a test run.
4. Inspect atom counts, periodic box vectors, potential energy, and serialized files. Keep the input and output directories distinct unless an intentional, reviewed overwrite is requested.
5. Record parameters and provenance in the project note route. These helpers reproduce preparation mechanics; they do not establish production-quality sampling, biological efficacy, or paper-level validation.

## Safety gates

- CPU OpenMM is the required baseline. CUDA can be requested only after a platform probe and may fail because of driver/toolkit/PTX incompatibility; see [troubleshooting.md](references/troubleshooting.md).
- A missing optional ligand package is a reason to stop and report a prerequisite, not to substitute an unparameterized ligand.
- Keep the default run short. The helper refuses excessive work unless `--allow-long-run` is supplied, and even then a research plan should define an independent budget.
- Do not run Folding@home client workflows, network downloads, or long production trajectories through this route.

## Handoff

For coordinate/chain/ligand edits, hand off to `../structure-curation/SKILL.md`. For target rationale and publication evidence, hand off to `../project-context/SKILL.md`. After a successful run, hand off artifact names, exact parameters, package/platform information, warnings, and unresolved scientific limitations rather than only saying “equilibrated.”
