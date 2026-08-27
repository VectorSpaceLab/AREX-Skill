---
name: sonnet
description: "Use DeepMind Sonnet for TensorFlow 2 modules, layers, training
  loops, functional transforms, serialization, and distribution workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sonnet Repo Skill

Use this repo skill when a task involves DeepMind Sonnet (`dm-sonnet`, imported
as `sonnet` or `snt`) for TensorFlow 2 neural-network research code: custom
modules, built-in layers and nets, manual training loops, RNNs, functional
transforms, checkpoints, SavedModel export, mixed precision, or TensorFlow
distribution helpers.

Sonnet is intentionally small and unopinionated. It provides composable
`Module` objects, built-in module families, and optimizers, but it does **not**
provide a full training framework, dataset pipeline, experiment runner, or
serving stack.

## Quick install and import check

```bash
python -m pip install tensorflow dm-sonnet
```

```python
import tensorflow as tf
import sonnet as snt
print("TensorFlow", tf.__version__)
print("Sonnet", snt.__version__)
print(snt.nets.MLP([16, 4])(tf.ones([2, 8])).shape)
```

Run [scripts/check_sonnet_install.py](scripts/check_sonnet_install.py) when you
need a no-download smoke check for importability, device visibility, lazy
variables, a tiny optimizer step, and basic RNN construction.

## Route by task

| If the task asks about... | Read this sub-skill | Why |
| --- | --- | --- |
| Custom `snt.Module` classes, `@snt.once`, lazy variables, names, `Sequential`, `Deferred`, `BatchApply`, or `snt.build` | [sub-skills/module-authoring/SKILL.md](sub-skills/module-authoring/SKILL.md) | Owns Sonnet's core module programming model and composition contracts. |
| Built-in layers, normalization, initializers, metrics, regularizers, `snt.nets.MLP`, ResNet, Cifar10ConvNet, or VQ-VAE modules | [sub-skills/layers-and-nets/SKILL.md](sub-skills/layers-and-nets/SKILL.md) | Owns constructor signatures, shape rules, state behavior, and layer/net smoke checks. |
| `tf.GradientTape` training loops, `snt.optimizers.*`, `optimizer.apply`, tiny local training checks, or metric accumulation | [sub-skills/training-and-optimization/SKILL.md](sub-skills/training-and-optimization/SKILL.md) | Owns object-oriented Sonnet optimization and safe training-loop recipes. |
| `RNNCore`, `LSTM`, `GRU`, `DeepRNN`, `dynamic_unroll`, `static_unroll`, trainable state, or ConvLSTM | [sub-skills/sequence-and-rnn/SKILL.md](sub-skills/sequence-and-rnn/SKILL.md) | Owns sequence shape/state conventions and recurrent troubleshooting. |
| `snt.functional.variables`, `transform`, `transform_with_state`, `grad`, `value_and_grad`, `jit`, `device_put/get`, or functional optimizers | [sub-skills/functional-transforms/SKILL.md](sub-skills/functional-transforms/SKILL.md) | Owns Sonnet's TensorFlow-based Haiku/JAX-like functional API. |
| TensorFlow checkpoints, SavedModel export/load, Keras/pickle caveats, XLA, mixed precision, `snt.distribute.Replicator`, TPU, or cross-replica BatchNorm | [sub-skills/serialization-and-distribution/SKILL.md](sub-skills/serialization-and-distribution/SKILL.md) | Owns persistence, export, distribution, and backend limitations. |

## Root references

- [references/package-overview.md](references/package-overview.md) summarizes
  Sonnet's public package mental model, dependencies, public imports, and common
  workflow boundaries.
- [references/troubleshooting.md](references/troubleshooting.md) covers
  cross-cutting install/import, TensorFlow backend, and public-API routing
  failures before you enter a sub-skill-specific troubleshooting file.
- [references/repo-provenance.md](references/repo-provenance.md) records the
  source snapshot used to build this skill.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  is structured routing metadata consumed by the managed repo-skill importer.

## Operating checklist

1. Import public symbols from `sonnet` (`import sonnet as snt`), not private
   implementation modules.
2. Build modules once with representative inputs before inspecting variables,
   exporting, or passing parameters to optimizers.
3. Assert small shapes at module boundaries: final feature dimension for
   `Linear`, channel dimension for convolution/normalization, and time-major
   sequence layout for RNN unroll helpers.
4. Use `tf.GradientTape` plus `optimizer.apply(gradients, variables)` for
   object-oriented Sonnet training loops, or use `snt.functional` only when the
   task explicitly wants stateless-style `init`/`apply` workflows.
5. Treat CUDA, TPU, XLA, and distributed execution as environment-specific. Do
   not claim accelerator verification unless the current TensorFlow runtime has
   been probed and the sub-skill's backend guidance is satisfied.

## When not to use this skill

- The user is asking for general TensorFlow or Keras usage with no Sonnet API,
  module, optimizer, or distribution helper involved.
- The user wants to edit or maintain the Sonnet repository itself rather than
  use Sonnet as a package; route to a repository-maintenance workflow instead.
- The user needs a full experiment framework, trainer, data pipeline, model
  zoo, or serving platform that Sonnet does not provide.
