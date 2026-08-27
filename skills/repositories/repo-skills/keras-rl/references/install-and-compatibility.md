# Install and compatibility

Read this before running keras-rl code in a new environment. keras-rl is a legacy standalone Keras package; most failures come from mixing it with modern Keras/TensorFlow, optional Gym/simulator dependencies, or callback/logging extras.

## Package identity

- Distribution: `keras-rl`.
- Import package: `rl`.
- Public version captured for this skill: `0.4.2`.
- Core install requirement from package metadata: `keras>=2.0.7`.
- Optional package extra: `keras-rl[gym]` installs Gym for example-style environment use.

## Recommended compatibility workflow

1. Create an isolated Python environment rather than installing into a shared project environment.
2. Install a legacy Keras 2.x-compatible backend stack.
3. Install `keras-rl`, plus only the optional dependencies needed by the task.
4. Run a compile-only smoke helper before long training.
5. Add heavy extras such as Atari or MuJoCo only when the user explicitly needs those workflows.

A typical package-level check is:

```python
import rl
from rl.agents import DQNAgent, DDPGAgent, CEMAgent, SARSAAgent, NAFAgent
from rl.memory import SequentialMemory, EpisodeParameterMemory
from rl.policy import EpsGreedyQPolicy, BoltzmannQPolicy
```

For a stronger check, use `sub-skills/core-extension-and-logging/scripts/check_keras_rl_env.py` from this skill tree.

## Backend notes

| Surface | Guidance |
| --- | --- |
| Standalone Keras 2.x | Required family for this legacy code. Prefer old-compatible APIs such as `Adam(lr=...)` when examples use them. |
| Theano backend | Often the safest CPU compile-smoke route for old keras-rl APIs that inspect Keras symbolic tensors. If native-op errors mention BLAS symbols such as `dgemm_`, install/link a BLAS runtime such as OpenBLAS and rerun the smoke. |
| TensorFlow backend | TensorFlow 1.x-era imports can work, but some stacks fail when agent constructors call legacy symbolic-output checks such as `len(model.output)`. Prove with a compile smoke before training. |
| Modern Keras 3 / pure `tf.keras` | Treat as incompatible until proven. Expect renamed optimizer arguments, changed tensor attributes, and missing legacy backend behavior. |
| CUDA/GPU | keras-rl itself has no selected CUDA-specific package code. GPU support belongs to the chosen Keras backend and is optional for these skill workflows. |

## Optional dependencies by task

| Need | Dependency | Notes |
| --- | --- | --- |
| Gym examples/environments | `keras-rl[gym]` or a compatible `gym` install | Legacy examples expect old Gym reset/step signatures. New Gymnasium-style APIs may need an adapter. |
| Saving/loading weights | `h5py` | Keras HDF5 weight save/load needs h5py compatible with the Keras version. |
| Plotting training logs | `matplotlib` | Use noninteractive backends when saving figures in headless sessions. |
| `WandbLogger` or importing `rl.callbacks` in this version | `wandb` | This repo imports `wandb` at callback module import time, so missing W&B can break imports even if you do not call `WandbLogger`. |
| Atari DQN | Pillow, Atari-capable Gym extras, ROM/data setup | Heavy optional path; no full runner is bundled. Use the discrete-control Atari reference for processor concepts. |
| MuJoCo DDPG | MuJoCo system packages/license plus compatible Gym bindings | Heavy optional path; treated as reference-only unless the user has prepared it. |

## Smoke-check order

- For discrete agents, run the discrete smoke helper with an installed legacy-compatible backend before training.
- For continuous agents, run the continuous smoke helper before wiring a real environment.
- For callbacks/logs, run the environment checker or the log visualizer helper with a tiny JSON fixture.

Do not treat a successful import as proof that agent construction, `compile`, `fit`, or `test` will work. This package has several compatibility points that only appear after a Keras model is built and passed into an agent.
