# Repository Overview

## Purpose

This reference maps the repository's public runtime surface so future agents can route tasks without reopening the source tree.

## Architecture

| Module / script | Runtime role | Skill owner |
| --- | --- | --- |
| `meta` | Defines `MetaOptimizer`, variable interception, unrolled meta-loss construction, optimizer-state reset/update ops, and `.l2l` save/load entry point. | `meta-optimizer-api` |
| `networks` | Defines optimizer network modules and serialization helpers: factory, save, LSTM networks, SGD, and Adam. | `optimizer-networks` |
| `preprocess` | Defines Sonnet preprocessing modules used before LSTM optimizer networks. | `optimizer-networks` |
| `problems` | Defines optimizee loss factories for scalar, quadratic, ensemble, MNIST, and CIFAR tasks. | `problem-factories` |
| `util` | Maps README problem names to problem factories, network configs, saved-network paths, and variable-to-network assignments. | `problem-factories`, `training-evaluation` |
| Training script | Creates a problem, builds `MetaOptimizer.meta_minimize`, runs epoch/evaluation loops, and optionally saves the best optimizer. | `training-evaluation` |
| Evaluation script | Evaluates either the L2L optimizer or TensorFlow Adam on a selected problem. | `training-evaluation` |

## Main object flow

1. A problem factory returns a zero-argument `make_loss` function.
2. `MetaOptimizer.meta_loss` discovers trainable optimizee variables by calling `make_loss` once under a custom TensorFlow variable getter.
3. `networks.factory` builds one or more optimizer networks from the config.
4. A TensorFlow `while_loop` repeatedly rebuilds the loss with replacement variables, computes gradients, and asks the optimizer network(s) for parameter deltas.
5. The returned namedtuple exposes `reset`, `update`, `fx`, and final optimizee tensors; `meta_minimize` additionally exposes a TensorFlow Adam `step` op for meta-training.
6. `MetaOptimizer.save` persists the optimizer-network variables as `.l2l` pickle files.

## Safe smoke scope

Use these for quick checks:

- Problem: `simple` or `quadratic`.
- Optimizer network: `CoordinateWiseDeepLSTM` with small or empty `layers`, or stateless `Sgd`/`Adam`.
- Epochs/steps: one epoch, two optimizee steps, one-step unroll.

Avoid by default:

- `convergence_test`-style long training.
- CIFAR data workflows, because they may download and unpack a dataset.
- MNIST/CIFAR workflows if the runtime cannot tolerate dataset cache writes.
- Second derivatives on data-backed networks unless the graph is known to support them.

## Key terminology

- **Optimizee**: the problem model or variables being optimized, for example scalar `x` in `simple`.
- **Meta-optimizer**: the learned optimizer that emits parameter deltas from gradients.
- **Unroll**: repeated optimizee update steps inside the meta-loss graph.
- **Optimizer network id**: a key such as `cw`, `adam`, `conv`, or `fc` that maps optimizee variables to a network config and saved `.l2l` file.
- **Problem name**: README/CLI-facing name such as `simple-multi`; some source function names use underscores instead.
