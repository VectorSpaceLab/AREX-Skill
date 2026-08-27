---
name: interfaces-md
description: "Run trained SchNetPack models through ASE calculators, ensemble
  uncertainty, molecular dynamics configs, TorchScript deployment, and LAMMPS
  interface guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SchNetPack Interfaces and Molecular Dynamics

Use this sub-skill when the task starts from an already trained SchNetPack model and asks to run, relax, deploy, or simulate atomistic systems.

## Route Here For

- ASE calculators with `SpkCalculator`, `AtomsConverter`, `AseInterface`, `SpkEnsembleCalculator`, `AbsoluteUncertainty`, or `RelativeUncertainty`.
- Single-point energy/force/stress prediction, ASE optimization, normal modes, short ASE MD, or batchwise relaxation planning.
- `spkmd` command construction, Hydra MD config files, checkpoint/restart handling, thermostat/barostat/integrator choices, RPMD, and CPU fallback.
- TorchScript deployment for the SchNetPack LAMMPS pair style with `scripts/deploy_for_lammps.py`.
- LAMMPS interface advice, including `pair_style schnetpack`, `pair_coeff` atom-type mapping, cutoff metadata, and build-risk warnings.

## Route Elsewhere

- Model architecture, output modules, response-force/stress training, and model checkpoints: `../models-atomistic/SKILL.md`.
- Training runs, Hydra training configs, callbacks, and checkpoint selection: `../training-configs/SKILL.md`.
- Dataset creation, ASE databases, property units, and unit conversion before training: `../data-pipelines/SKILL.md`.
- External LAMMPS compilation, source-tree patching, or cluster build-system changes: provide guidance only unless the user explicitly authorizes environment mutation.

## Fast Decision Guide

- For a Python workflow using ASE `Atoms`: start with [ASE interface](references/ase-interface.md).
- For production-style MD from CLI/config: start with [MD CLI](references/md-cli.md).
- For LAMMPS deployment: read [LAMMPS deployment](references/lammps.md), then use `scripts/deploy_for_lammps.py` only after checking model compatibility.
- For failures or unsafe requests: use [troubleshooting](references/troubleshooting.md).

## Safety Defaults

- Prefer `device="cpu"` for examples and dry runs unless the user confirms CUDA availability.
- Keep MD examples bounded; do not launch long MD, GPU workloads, dataset downloads, native tests, or LAMMPS builds by default.
- Treat SchNetPack's upstream LAMMPS patch helper as reference-only because it mutates an external LAMMPS source tree and build files.
