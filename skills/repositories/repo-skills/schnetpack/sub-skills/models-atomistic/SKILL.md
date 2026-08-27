---
name: models-atomistic
description: "Build, inspect, customize, and troubleshoot SchNetPack atomistic
  neural network components in Python and Hydra configs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SchNetPack Models and Atomistic Components

Use this sub-skill when the task is about composing SchNetPack atomistic model objects, output modules, representation networks, response properties, radial/cutoff layers, postprocessors, or model/task key alignment.

## Read First

- `references/api-reference.md` for constructor signatures, object contracts, and Python assembly patterns.
- `references/model-components.md` for choosing representations, input modules, output modules, response layers, and Hydra snippets.
- `references/property-keys-and-units.md` for tensor keys, target names, units, dtype, offsets, and postprocessor behavior.
- `references/troubleshooting.md` for common atomistic model failures and fixes.

## Core Mental Model

SchNetPack atomistic models pass a mutable dictionary of tensors through `input_modules`, one `representation`, `output_modules`, and optional `postprocessors`. `NeuralNetworkPotential` collects `required_derivatives` and `model_outputs` from child modules, initializes requested gradients on input tensors, runs modules sequentially, applies postprocessors only when enabled, and returns only the collected output keys.

## Route Boundaries

- Use this sub-skill for `NeuralNetworkPotential`, `AtomisticTask`, `ModelOutput`, `SchNet`, `PaiNN`, `SO3net`, `FieldSchNet`, `GaussianRBF`, `BesselRBF`, `CosineCutoff`, `Atomwise`, `Forces`, `Response`, `DipoleMoment`, `Polarizability`, Coulomb/ZBL priors, `StaticExternalFields`, `PairwiseDistances`, key mapping, and postprocessing.
- Route dataset creation, `ASEAtomsData`, `AtomsDataModule`, splitting, and dataset unit declarations to `../data-pipelines/SKILL.md`.
- Route CLI/Hydra run assembly, experiment directory layout, trainers, loggers, checkpoint callbacks, and `spktrain` overrides to `../training-configs/SKILL.md`.
- Route ASE calculators, `AtomsConverter`, `SpkCalculator`, MD, deployment, and LAMMPS integration to `../interfaces-md/SKILL.md`.

## Safe Working Pattern

1. Pick one property-key vocabulary and reuse it in model outputs, task targets, losses, metrics, data properties, and postprocessors.
2. Ensure neighbor-list transforms are present before `PairwiseDistances`; representation modules require `_Rij`, `_idx_i`, and `_idx_j`.
3. Add derivative modules such as `Forces` or `Response` as output modules, not task outputs alone.
4. Match every predicted output in `model.output_modules` with a `task.outputs` `ModelOutput` when it participates in supervised training.
5. Keep postprocessors for inference-scale outputs; `AtomisticTask.predict_without_postprocessing()` disables them while computing losses.

## Avoid

- Do not run long training, downloads, GPU molecular dynamics, or native repository tests from this sub-skill.
- Do not reference local checkout paths or machine-specific environment details in generated configs.
- Do not put data-loading, CLI workflow, or calculator deployment details here beyond routing links.
