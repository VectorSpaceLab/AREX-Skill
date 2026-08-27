---
name: serialization-and-distribution
description: "Serialize/export Sonnet modules and reason about TensorFlow
  distribution, mixed precision, and backend limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serialization and Distribution

Use this sub-skill for TensorFlow checkpoints, SavedModel export/load, pickle or Keras interoperability caveats, XLA, mixed precision, and `snt.distribute` helpers.

## Start here

- [references/serialization.md](references/serialization.md): checkpoint, SavedModel, Keras/pickle, XLA, and mixed precision recipes.
- [references/distribution-and-backends.md](references/distribution-and-backends.md): `Replicator`, `TpuReplicator`, `CrossReplicaBatchNorm`, and backend limits.
- [references/troubleshooting.md](references/troubleshooting.md): restored object identity, SavedModel signatures, cross-replica context, and accelerator-runtime failures.
- [scripts/serialization_smoke.py](scripts/serialization_smoke.py): CPU checkpoint and SavedModel smoke.

## Boundaries

- Module construction and lazy variables: [../module-authoring/SKILL.md](../module-authoring/SKILL.md).
- Training-loop checkpoint timing: [../training-and-optimization/SKILL.md](../training-and-optimization/SKILL.md).
- Functional transforms and device helpers: [../functional-transforms/SKILL.md](../functional-transforms/SKILL.md).

## Backend policy

CPU verifies checkpoints, SavedModel export/load, pickle caveats, and mixed precision policy mechanics. CUDA, TPU, XLA performance, and distributed replicas require a matching TensorFlow runtime. Do not claim accelerator verification from a CPU-only run.
