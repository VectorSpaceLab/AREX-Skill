---
name: neural-network-building-blocks
description: "Use this sub-skill for MLAlgorithms NeuralNet construction,
  activations, losses, parameters, constraints, regularizers, optimizers,
  convolutional/recurrent layers, and DQN wiring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Neural Network Building Blocks

Use this sub-skill when a task asks for the custom MLAlgorithms neural-network stack: how to build a `NeuralNet`, choose layers or optimizers, debug training phases and shapes, or adapt the repo's MLP/CNN/RNN/LSTM/DQN examples into shorter checks. The implementation is educational and CPU-only, with no external training service or model hub dependency.

## Route elsewhere

- Tabular supervised estimators, SVM kernels, ensembles, KNN, Naive Bayes, and factorization machines belong in `../classical-estimators/SKILL.md`.
- KMeans, Gaussian mixtures, PCA, t-SNE, RBM, and demo dataset loaders belong in `../unsupervised-and-reduction/SKILL.md`.
- Cross-cutting install, provenance, and route selection remain in the root skill.

## Start here

1. Confirm the package imports the neural stack you need:

   ```python
   from mla.neuralnet import NeuralNet
   from mla.neuralnet.layers import Dense, Activation, Dropout
   from mla.neuralnet.optimizers import Adam
   ```

2. Choose the architecture family:
   - Simple dense model: `Dense` + `Activation`.
   - CNN: `Convolution`, `MaxPooling`, `Flatten`, `Dense`.
   - Sequence model: `RNN` or `LSTM`, optionally followed by `TimeDistributedDense` or `TimeStepSlicer`.
   - Reinforcement learning wrapper: `mla.rl.dqn.DQN` with a user-provided neural model factory.
3. Use explicit one-hot labels for `categorical_crossentropy`, and remember that `NeuralNet` uses a separate `optimizer.setup(self)` step when `fit` starts.
4. Run `scripts/run_neural_smoke.py --workflow all` for a short no-display check.

## Primary workflows

### Build a dense network

`NeuralNet` takes a list of layers plus an optimizer and a loss name. The container sets up layers, performs forward/backward passes, and delegates parameter updates to the optimizer.

```python
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Dense, Activation
from mla.neuralnet.optimizers import Adam

model = NeuralNet(
    layers=[Dense(16), Activation("relu"), Dense(1)],
    optimizer=Adam(),
    loss="mse",
    batch_size=32,
    max_epochs=5,
    metric="mse",
)
```

### Convolutional workflow

Use `Convolution`, `MaxPooling`, `Flatten`, and `Dense` for the repo's MNIST-style example. The ConvNet expects image tensors shaped like `(n_samples, n_channels, height, width)`.

### Recurrent workflow

Use `RNN` or `LSTM` for sequence problems. The classes accept `return_sequences=True` by default, which is helpful for per-time-step outputs. `TimeDistributedDense` applies a dense layer to each time step.

### DQN wiring

`DQN` is a lightweight training loop that asks the user to supply a model factory. It is designed around legacy Gym-style `reset()`/`step()` interactions and should be treated as an integration recipe rather than a production RL stack.

## Bundled references and helpers

- Read `references/api-reference.md` for exact constructor signatures and output/shape contracts.
- Read `references/workflows.md` for dense/CNN/RNN/DQN recipes and validation advice.
- Read `references/neural-workflows.md` for longer CNN and sequence reference workflows.
- Read `references/rl-dqn.md` before touching CartPole or other Gym environments.
- Read `references/troubleshooting.md` when training stalls, shapes break, or Gym/NumPy compatibility drifts.
- Run `scripts/run_neural_smoke.py --workflow mlp` or `--workflow all` for a small installed-package check.
