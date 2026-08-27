# Sonnet Package Overview

Read this when you need the high-level operating model for DeepMind Sonnet
before choosing a focused sub-skill.

## What Sonnet provides

Sonnet is a TensorFlow 2 library for composable neural-network modules. Its core
concept is `snt.Module`: a Python object that owns TensorFlow variables, other
modules, and methods that apply computation. Sonnet modules are intentionally
unopinionated about the rest of a research program.

Use Sonnet for custom module classes with lazy variable creation, built-in
modules such as `Linear`/convolutions/normalization/RNN cores, optimizer objects
that apply TensorFlow gradients, functional transform APIs, and TensorFlow-native
checkpoint/SavedModel/distribution integration.

Do not expect Sonnet to provide a Keras-style `compile`/`fit` training loop,
dataset download/preprocessing, experiment management, automatic distributed
gradient averaging, or model serving infrastructure.

## Public imports

```python
import tensorflow as tf
import sonnet as snt
mlp = snt.nets.MLP([64, 10])
logits = mlp(tf.ones([8, 32]))
```

| Namespace | Contains |
| --- | --- |
| `snt.Module`, `snt.Optimizer` | Base classes and contracts. |
| `snt.Linear`, `snt.Conv2D`, `snt.BatchNorm`, ... | Frequently used built-in modules. |
| `snt.initializers`, `snt.regularizers`, `snt.pad` | Helpers for parameters and padding. |
| `snt.nets` | `MLP`, `ResNet`, `Cifar10ConvNet`, VQ-VAE quantizers. |
| `snt.optimizers` | `SGD`, `Momentum`, `RMSProp`, `Adam`. |
| `snt.functional` | Functional transform, gradient, device, optimizer helpers. |
| `snt.distribute` | Distribution strategies and cross-replica BatchNorm. |

Avoid importing from implementation modules. Public code should not depend on
private module locations even if a traceback shows them.

## Lazy variable lifecycle

Most Sonnet modules create variables on first call because shapes often depend
on input shape. Construct the module, call it once with representative tensors
or use `snt.build`, then inspect `variables`, `trainable_variables`, and
`submodules`. In Sonnet 2, requesting variables before a module is built often
raises a helpful `ValueError`; after a forward pass, an empty variable set is a
bug for modules that should own weights.

## Backend expectations

CPU is enough for most API inspection, module construction, shape validation,
optimizers, functional transforms, checkpoint roundtrips, and synthetic smoke
tests. CUDA, TPU, and multi-device behavior are TensorFlow runtime concerns: a
GPU-visible host is not proof that TensorFlow can use CUDA, and CPU smoke tests
are not proof of TPU behavior.

## Safe validation helpers

The generated skill bundles no-download helpers:

- `scripts/check_sonnet_install.py`
- `sub-skills/module-authoring/scripts/module_contract_smoke.py`
- `sub-skills/layers-and-nets/scripts/layers_and_nets_smoke.py`
- `sub-skills/training-and-optimization/scripts/sonnet_tiny_training_smoke.py`
- `sub-skills/sequence-and-rnn/scripts/rnn_unroll_smoke.py`
- `sub-skills/functional-transforms/scripts/sonnet_functional_transform_smoke.py`
- `sub-skills/serialization-and-distribution/scripts/serialization_smoke.py`

Run each helper with `--help` first and keep temporary artifacts outside
important project directories.
