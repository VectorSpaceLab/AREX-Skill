---
name: distributed-training
description: "Use FedML for centralized training, cross-cloud training, LLM
  training recipes, data/model loading, and FedMLRunner-based training
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent_skill: "fedml"
license: Apache 2.0
---

# FedML Distributed Training

Use this sub-skill for non-FL training workflows: centralized single-process training, cross-cloud client/server training, launch-driven training jobs, LLM training scripts, `fedml.init`, `fedml.data.load`, `fedml.model.create`, and `FedMLRunner`.

## Do not use this for

- Federated simulation/cross-silo algorithm design: use `../federated-learning/SKILL.md`.
- Package building or platform launch mechanics: combine with `../launch-and-packaging/SKILL.md`.
- Model-serving endpoints: use `../model-serving/SKILL.md`.

## Training route selection

1. **Centralized/local training** — use this when a user wants a normal Python training entry point under FedML.
2. **Cross-cloud training** — use this with `launch-and-packaging` when client/server code is packaged for the platform.
3. **LLM training** — use this for `python/examples/train/llm_train` patterns; expect optional extras, GPUs, and model/data access.
4. **Remote training job** — inspect training code here, then launch with `launch-and-packaging`.

## Core API pattern

The canonical local training shape is:

```python
import fedml

args = fedml.load_arguments(training_type="simulation", comm_backend="sp")
args = fedml.init(args)
device = fedml.device.get_device(args)
dataset, output_dim = fedml.data.load(args)
model = fedml.model.create(args, output_dim)
runner = fedml.FedMLRunner(args, device, dataset, model)
runner.run()
```

Adapt the `training_type`, backend, dataset, model, trainer, and aggregator to the selected example.

## Evidence anchors

- `python/examples/centralized/` — centralized training examples.
- `python/examples/cross_cloud/` — cross-cloud client/server package patterns.
- `python/examples/train/llm_train/` — LLM scripts, job YAML, bootstrap, DDP and DeepSpeed variants.
- `python/fedml/runner.py` — `FedMLRunner` orchestration.
- `python/fedml/data/` and `python/fedml/model/` — data/model factory surfaces.

## Backend and safety checks

- Read `../../references/backend-matrix.md` before selecting CUDA, DDP, DeepSpeed, or dataset-heavy examples.
- Use CPU/small-data checks first when the user asks for a quick smoke test.
- LLM training is not a quick validation route; it may require large downloads, optional extras, GPUs, and remote launch configuration.
- Multiprocessing-heavy entry points should be guarded with `if __name__ == "__main__":`.
- Dataset loaders may download data. Clarify network/cache constraints before running examples.

## Common combinations

- Need to package a training job: read this sub-skill for code shape, then `../launch-and-packaging/SKILL.md` for YAML/package/launch.
- Need centralized training only: stay here and avoid remote platform commands.
- Need federated learning: switch to `../federated-learning/SKILL.md` unless the task is only about a shared model/data loader.

## Exit criteria

A distributed-training task is complete when the training mode, backend, data/model path, launch-vs-local decision, and any GPU/network requirements are explicit, and the user has either runnable commands/code or a documented blocker.
