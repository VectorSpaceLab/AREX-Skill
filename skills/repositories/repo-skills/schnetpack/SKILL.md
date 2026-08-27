---
name: schnetpack
description: "Use SchNetPack for atomistic machine-learning datasets, Hydra
  training/prediction configs, neural network potential components, ASE/MD
  interfaces, and LAMMPS deployment guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SchNetPack Repo Skill

Use this skill when a task involves SchNetPack, atomistic neural networks, neural network potentials, molecular or materials datasets, SchNet/PaiNN-style models, ASE calculators, molecular dynamics, or SchNetPack command-line tools.

## Fast Routing

- Use `sub-skills/data-pipelines/SKILL.md` for ASE DB datasets, unit metadata, property names, atomrefs, split files, `AtomsDataModule`, built-in datasets, and legacy dataset conversion.
- Use `sub-skills/training-configs/SKILL.md` for `spktrain`, `spkpredict`, Hydra config groups, experiment templates, trainer/logger/callback overrides, checkpoint behavior, and prediction commands.
- Use `sub-skills/models-atomistic/SKILL.md` for Python model construction, `NeuralNetworkPotential`, SchNet, PaiNN, output modules, force/stress response wiring, property keys, postprocessors, and transforms.
- Use `sub-skills/interfaces-md/SKILL.md` for trained-model runtime use through ASE calculators, ensemble uncertainty, `spkmd`, MD configs, TorchScript deployment, and LAMMPS pair-style guidance.

## Read These Root References

- `references/api-overview.md` gives a compact map of SchNetPack modules, public object families, and verified signatures.
- `references/cli-and-configuration.md` summarizes installed command names, Hydra config families, safe help checks, and routing from CLI tasks to sub-skills.
- `references/troubleshooting.md` covers cross-cutting install/import, PyTorch/backend, CLI, Hydra, data, model, and MD failure surfaces.
- `references/repo-provenance.md` records the source snapshot and relative evidence paths used to generate this skill.
- `references/repo-routing-metadata.json` is structured metadata used by `repo-skills-router` during import.

## Safe First Checks

Run these in the user's intended Python environment before deep debugging:

```bash
python scripts/schnetpack_import_check.py --json
python scripts/schnetpack_cli_check.py --commands spktrain spkpredict spkmd spkconvert spkdeploy
```

Use these scripts for import/signature/CLI availability checks only. They do not train models, download datasets, run MD, or build LAMMPS.

## Install and Core Package Facts

Install in a normal Python environment with:

```bash
pip install schnetpack
python -c "import schnetpack as spk; print(spk.__version__)"
```

- Distribution/import module: `schnetpack`.
- Generated against SchNetPack version `2.2.0`.
- Python requirement from package metadata: `>=3.12`.
- Primary dependencies include PyTorch, PyTorch Lightning, Hydra/OmegaConf, ASE, NumPy, SciPy, h5py, matscipy, tensorboard, and related utilities.
- Installed command names include `spktrain`, `spkpredict`, `spkconvert`, `spkdeploy`, and `spkmd`.

## Workflow Map

| User asks for | Start with | Then check |
| --- | --- | --- |
| Create or repair an ASE DB, units, atomrefs, property lists, split files | `data-pipelines` | `training-configs` if the data feeds `spktrain` |
| Train QM9, MD17, rMD17, custom data, loggers, callbacks, checkpoints | `training-configs` | `data-pipelines` for schema errors; `models-atomistic` for output/task changes |
| Build/customize SchNet, PaiNN, force, stress, dipole, polarizability, postprocessors | `models-atomistic` | `training-configs` for Hydra command assembly |
| Use a trained model in ASE, relaxation, MD, ensemble uncertainty, LAMMPS | `interfaces-md` | `models-atomistic` if outputs or stress/force support are missing |
| Diagnose import, CLI, backend, or broad environment failures | `references/troubleshooting.md` | Nearest sub-skill troubleshooting file for workflow-specific errors |

## Safety Boundaries

- Do not launch long training, dataset downloads, GPU jobs, production MD, LAMMPS patching, or LAMMPS builds as routine validation.
- Prefer help/import/signature checks and tiny user-provided fixtures before real compute.
- Use CPU examples unless the user explicitly asks for CUDA and the environment verifies CUDA support.
- Keep native examples and tests as verification evidence, not runtime dependencies for this skill.
- When adapting user commands, make run/data/output directories explicit so Hydra's working-directory changes are predictable.

## Common Decision Points

- If an ASE DB lacks `_distance_unit` or `_property_unit_dict`, route to `data-pipelines` before training or prediction.
- If a command uses `model/representation=painn`, that selects a config group; if it uses `model.representation.n_interactions=5`, that edits a field. Route syntax confusion to `training-configs`.
- If force or stress predictions fail, verify `Forces`, `required_derivatives`, property keys, and output/task wiring in `models-atomistic` before blaming ASE or MD.
- If `spkmd` fails on CPU-only hosts, check whether the MD config defaulted to `device=cuda` and add `device=cpu` when appropriate.
- If LAMMPS deployment is requested, use the bundled deployment helper and read the LAMMPS reference before proposing build or patch steps.
