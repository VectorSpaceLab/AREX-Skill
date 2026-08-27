# Neural network API reference

## Purpose

Read this when a task needs exact import paths, constructor defaults, shapes, losses, optimizers, layer behavior, or DQN wiring for MLAlgorithms' custom neural-network stack. Facts are based on package source and live signature inspection for distribution `mla` version `0.0.1`.

## Core container

```python
from mla.neuralnet import NeuralNet
```

`NeuralNet(layers, optimizer, loss, max_epochs=10, batch_size=64, metric='mse', shuffle=False, verbose=True)` manages layer setup, forward propagation, backpropagation, metrics, and optimizer updates.

Important behavior:

- `layers` is an ordered list of layer objects. Each layer must implement `setup`, `forward_pass`, `backward_pass`, and `shape`.
- `optimizer` must implement `setup(network)` and update all parametric layers.
- `loss` is a name resolved by `mla.neuralnet.loss.get_loss`. Supported names include `mse`, `logloss`, `mae`, `hinge`, `binary_crossentropy`, and `categorical_crossentropy`.
- `metric` is resolved through `mla.metrics.metrics.get_metric`.
- If `loss == 'categorical_crossentropy'`, the implementation uses a custom gradient `-(actual - predicted)`; otherwise it uses autograd's elementwise gradient.
- `fit(X, y)` sets up layers on the first call. If `y` is one-dimensional, it is reshaped to `(n_samples, 1)`.
- `predict(X)` initializes layers if needed, then batches through `fprop`.
- `error(X=None, y=None)` temporarily disables training phase for `Dropout` and other `PhaseMixin` layers.
- `reset()` clears layer initialization state.

## Basic layers

```python
from mla.neuralnet.layers import Dense, Activation, Dropout, TimeDistributedDense, TimeStepSlicer
```

| Layer | Signature | Input/output notes |
| --- | --- | --- |
| `Dense` | `Dense(output_dim, parameters=None)` | Fully connected layer. Input is 2D `(batch, input_dim)`, output is `(batch, output_dim)`. |
| `Activation` | `Activation(name)` | Applies an activation function and autograd elementwise derivative. |
| `Dropout` | `Dropout(p=0.1)` | During training, masks inputs with probability `p`; during testing, scales by `1-p`. |
| `TimeDistributedDense` | `TimeDistributedDense(output_dim)` | Applies a dense layer to every timestep in a 3D `(batch, timesteps, features)` tensor. |
| `TimeStepSlicer` | `TimeStepSlicer(step=-1)` | Selects a timestep from a 3D tensor; backward pass repeats a gradient across a fixed length used by the implementation. |

Activation names are functions in `mla.neuralnet.activations`: `sigmoid`, `softmax`, `linear`, `softplus`, `softsign`, `tanh`, `relu`, `leakyrelu`, and `gelu`. Unknown names raise `ValueError("Invalid activation function.")`.

## Convolution and normalization layers

```python
from mla.neuralnet.layers import Convolution, MaxPooling, Flatten, BatchNormalization
```

| Layer | Signature | Input/output notes |
| --- | --- | --- |
| `Convolution` | `Convolution(n_filters=8, filter_shape=(3, 3), padding=(0, 0), stride=(1, 1), parameters=None)` | Expects image tensors `(batch, channels, height, width)`. Uses im2col helpers. |
| `MaxPooling` | `MaxPooling(pool_shape=(2, 2), stride=(1, 1), padding=(0, 0))` | Pools 4D image tensors. Shape calculations assert integral output size. |
| `Flatten` | `Flatten()` | Flattens all non-batch dimensions into a 2D matrix. |
| `BatchNormalization` | `BatchNormalization(momentum=0.9, eps=1e-5, parameters=None)` | Supports 2D dense and 4D convolution tensors; keeps running mean/variance for test phase. |

## Recurrent layers

```python
from mla.neuralnet.layers.recurrent import RNN, LSTM
```

| Layer | Signature | Input/output notes |
| --- | --- | --- |
| `RNN` | `RNN(hidden_dim, activation='tanh', inner_init='orthogonal', parameters=None, return_sequences=True)` | Expects `(batch, timesteps, features)`. Returns full sequences by default. |
| `LSTM` | `LSTM(hidden_dim, activation='tanh', inner_init='orthogonal', parameters=None, return_sequences=True)` | Expects `(batch, timesteps, features)`. Maintains hidden/output state across calls. |

Use `return_sequences=False` when the next layer expects only the final timestep representation.

## Parameters, constraints, and regularizers

```python
from mla.neuralnet.parameters import Parameters
from mla.neuralnet.constraints import MaxNorm, NonNeg, SmallNorm, UnitNorm
from mla.neuralnet.regularizers import L1, L2, ElasticNet
```

- `Parameters(init='glorot_uniform', scale=0.5, bias=1.0, regularizers=None, constraints=None)` stores layer weights, gradients, initializers, regularizers, and constraints.
- Initializer names include `normal`, `uniform`, `zero`, `one`, `orthogonal`, `glorot_normal`, `glorot_uniform`, `he_normal`, and `he_uniform`.
- Constraints clip or normalize weights after parameter updates.
- Regularizers are callables that add gradient penalties to named parameter gradients, for example `Parameters(regularizers={'W': L2(0.05)})`.

## Optimizers

```python
from mla.neuralnet.optimizers import SGD, Adagrad, Adadelta, RMSprop, Adam, Adamax
```

| Optimizer | Signature |
| --- | --- |
| `SGD` | `SGD(learning_rate=0.01, momentum=0.9, decay=0.0, nesterov=False)` |
| `Adagrad` | `Adagrad(learning_rate=0.01, epsilon=1e-8)` |
| `Adadelta` | `Adadelta(learning_rate=1.0, rho=0.95, epsilon=1e-8)` |
| `RMSprop` | `RMSprop(learning_rate=0.001, rho=0.9, epsilon=1e-8)` |
| `Adam` | `Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-8)` |
| `Adamax` | `Adamax(learning_rate=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-8)` |

Optimizers allocate internal accumulators in `setup(network)`, which is called from `NeuralNet._setup_layers` before training.

## DQN wrapper

```python
from mla.rl.dqn import DQN
```

`DQN(n_episodes=500, gamma=0.99, batch_size=32, epsilon=1.0, decay=0.005, min_epsilon=0.1, memory_limit=500)` exposes:

- `init_environment(name='CartPole-v0', monitor=False)` to create a Gym environment and replay memory.
- `init_model(model)` where `model` is a factory taking `(n_actions, batch_size)` and returning an object with `fit(X, y)` and `predict(X)`.
- `train(render=False)` for the long training loop.
- `play(episodes)` for rendering trained behavior.

The source uses legacy Gym return signatures and rendering behavior. Read `rl-dqn.md` before running training or play loops.
