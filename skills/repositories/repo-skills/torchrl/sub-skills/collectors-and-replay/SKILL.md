---
name: collectors-and-replay
description: "Collect rollouts, select collector topologies, configure replay
  buffers, and debug TorchRL data movement."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TorchRL collectors and replay

Use this sub-skill when a task involves TorchRL rollout collection, evaluation rollouts, replay-buffer composition, sequence or slice sampling, prioritized replay, generation-safe record updates, memmap storage, checkpointing, HER, or optional service-backed replay.

## Route here for

- `Collector`, `AsyncCollector`, `MultiCollector`, `Evaluator`, `frames_per_batch`, `total_frames`, `trajs_per_batch`, `sync`, `backend`, `backend_options`, `num_collectors`, `update_policy_weights_`, and weight-update schemes.
- Direct, local process, Ray, RPC, distributed, and Submitit collector topology selection.
- `ReplayBuffer`, `TensorDictReplayBuffer`, `TensorDictPrioritizedReplayBuffer`, `LazyTensorStorage`, `LazyMemmapStorage`, `SliceSampler`, `Sequence`, `PrioritizedSampler`, `TensorDictRoundRobinWriter`, `update_tensordict_priority`, and `update_if_present`.
- Collector-to-replay integration, explicit `device` / `storing_device` / `policy_device` / `env_device` decisions, and debugging TensorDict movement across collection and storage.

## Route out instead

- Environment construction, specs, transforms, Gym/Gymnasium wrappers, and `step_mdp` layout questions: use `envs-and-transforms`.
- Actor, critic, recurrent policy, distribution, and TensorDictModule construction: use `modules-and-policies`.
- Loss modules, trainers, target updates, and algorithm optimization loops: use `objectives-and-training`.
- Generic TorchRL service registry, LLM collectors, VLA schemas, rendering, or serving backends: use `llm-vla-and-services`.

## Operating references

1. Read [collector-workflows.md](references/collector-workflows.md) for collector topology, sync/async choices, explicit devices, Evaluator, and collector-to-replay patterns.
2. Read [replay-buffer-workflows.md](references/replay-buffer-workflows.md) for buffer composition, storages, samplers, writers, transforms, sequence units, priorities, HER, memmap, checkpointing, and service-backed replay.
3. Read [api-reference.md](references/api-reference.md) for verified signatures and import paths.
4. Read [troubleshooting.md](references/troubleshooting.md) when collection, storage, sampling, priority updates, process workers, memmap cleanup, or optional Ray services fail.

## Bundled smoke helpers

- [scripts/smoke_collector.py](scripts/smoke_collector.py): CPU-only direct collector, explicit devices, direct collector-to-replay integration, and synchronous Evaluator smoke.
- [scripts/smoke_replay_buffer.py](scripts/smoke_replay_buffer.py): CPU-only TensorDict replay, LazyTensor/LazyMemmap storage, prioritized replay, `Sequence` sample unit masks, checkpoint round trip, and generation-safe updates.

Run these helpers from any working directory after TorchRL and TensorDict are importable. They do not download assets, launch distributed services, or train models.

## Evidence basis

This runtime guidance was distilled from relative TorchRL evidence covering `torchrl/collectors/`, `torchrl/data/replay_buffers/`, collector and replay reference pages, collector/evaluator/replay tutorials, selected collector and replay examples, selected `test/collectors/` and `test/rb/` behavior, and installed API probes. Optional Ray, RPC, Submitit, CUDA, simulator, and service-backed behaviors are documented as optional or reference-only unless a future task verifies those backends explicitly.
