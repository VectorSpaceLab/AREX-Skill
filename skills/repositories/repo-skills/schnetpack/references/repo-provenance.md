# Repository Provenance

Schema: `disco.repo-provenance.v1`

Generated skill id: `schnetpack`

## Source Snapshot

- VCS: Git
- Commit: `de850ebf5dc00f6327c12824e20afb7879f5b596`
- Branch: `master`
- Exact tag: none recorded
- Package version: `2.2.0`
- Remote URL: https://github.com/atomistic-machine-learning/schnetpack
- Dirty state: the checkout contained newly generated `skills/` output during final provenance capture. No pre-existing source-code modifications were used as extraction evidence.

## Primary Evidence Paths

- `pyproject.toml`
- `README.md`
- `src/schnetpack/`
- `src/schnetpack/configs/`
- `src/scripts/`
- `docs/getstarted.rst`
- `docs/userguide/`
- `docs/api/`
- `examples/README.md`
- `examples/tutorials/`
- `examples/howtos/`
- `interfaces/lammps/`
- `tests/`

## Extraction Scope Summary

Included evidence covered package metadata, public APIs, installed CLI scripts, Hydra config groups, data modules, model/task components, ASE/MD interfaces, LAMMPS guidance, public docs, examples/notebooks as workflow evidence, and representative tests/fixtures as behavior evidence.

Excluded or de-prioritized evidence included VCS/CI files, generated/cached/build outputs, static docs assets, large trained-model artifacts, review/test artifacts, long training, dataset downloads, GPU MD, and LAMMPS compilation/build workflows.

## Installed Package Inspection Summary

A private inspection environment verified:

- `schnetpack` distribution and import module version `2.2.0`.
- Imports for `schnetpack`, `schnetpack.data`, `schnetpack.representation`, `schnetpack.atomistic`, `schnetpack.interfaces`, and `schnetpack.md`.
- Clean package dependency check.
- Safe help output for `spktrain`, `spkpredict`, `spkconvert`, `spkdeploy`, and `spkmd`.
- Public signatures for key data, model, representation, output, and interface classes used in this skill.

CPU PyTorch was sufficient for inspection. CUDA/GPU execution was not required to generate this runtime skill.
