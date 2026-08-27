---
name: training-engine
description: "Assemble TorchDrug models and tasks into core.Engine training,
  evaluation, prediction, checkpoint, config serialization, logging,
  CPU/GPU/distributed settings, and safe smoke tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training Engine

Use this sub-skill when a user needs to turn an already chosen TorchDrug dataset, model, and task into an executable training or inference loop with `torchdrug.core.Engine`.

## When To Use

- Build a `core.Engine(task, train_set, valid_set, test_set, optimizer, ...)` training harness.
- Explain `train()`, `evaluate()`, direct `task.predict()`, checkpoint save/load, and JSON config round-trips.
- Choose CPU, single-GPU, distributed GPU, `batch_size`, `num_worker`, `gradient_interval`, logger, optimizer, or scheduler settings.
- Debug Engine, `Task`, `Configurable`, registry, optimizer, checkpoint, device, or logger failures.
- Add a no-dataset smoke check for `core.Configurable` serialization.

## Route Elsewhere

- Molecular property, pretraining, generation, retrosynthesis, and molecule dataset recipes belong in the `molecular-workflows` sub-skill.
- Knowledge graph completion datasets, negative sampling, filtered ranking, and KGE models belong in the `knowledge-graphs` sub-skill.
- Protein contact, structure, and sequence workflows belong in the `protein-workflows` sub-skill.
- Custom layer/model internals, representation model outputs, and extension patterns belong in the `layers-and-extensions` sub-skill.
- Graph, molecule, packed batch, or data container manipulation belongs in the data-focused sub-skills.

## References

- [Engine workflows](references/engine-workflows.md) covers Engine construction, training/evaluation/prediction, CPU/GPU/distributed choices, logging, scheduler, checkpoint, and config patterns.
- [Task contract](references/task-contract.md) covers the `Task` lifecycle, `predict`, `target`, `forward`, `evaluate`, `preprocess`, and custom integration points.
- [Troubleshooting](references/troubleshooting.md) covers split shapes, missing optimizer params, device and `gpus` errors, W&B setup, registry/config failures, and checkpoint mismatch recovery.

## Bundled Smoke Test

Run `scripts/smoke_config_roundtrip.py` from any environment that can import TorchDrug to verify that registered configurable models round-trip without datasets, network access, or training.
