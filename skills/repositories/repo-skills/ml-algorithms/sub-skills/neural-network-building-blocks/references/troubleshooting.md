# Neural network troubleshooting

## Purpose

Use this reference when MLAlgorithms neural models fail to import, set up layers, train, or interoperate with datasets and Gym.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mla'` | Package not installed in the active environment. | Install `mla` and run the root import smoke. |
| `ModuleNotFoundError: No module named 'autograd'` | Required autodiff dependency missing. | Install package requirements. |
| Gym unmaintained warning | The installed legacy Gym package imports but warns about maintenance. | This is expected for Gym `0.25.x`; do not claim Gymnasium compatibility without adapting DQN. |
| `AttributeError: module 'numpy' has no attribute 'bool'` | Dataset loader uses deprecated `np.bool`. | Use NumPy `<1.24` or patch loader code to `bool`/`np.bool_`. |

## Shape and layer setup failures

- Dense layers expect 2D arrays `(batch, features)`. Flatten images before dense-only models.
- Convolution and pooling layers expect 4D arrays `(batch, channels, height, width)`.
- RNN and LSTM layers expect 3D arrays `(batch, timesteps, features)`.
- `categorical_crossentropy` expects one-hot targets and usually a final `Activation("softmax")`.
- Regression losses such as `mse` work with one-column outputs; flatten predictions only when computing external metrics.
- Batch-dependent recurrent and neural workflows often need sample counts divisible by `batch_size` because the model initializes layer shapes using the configured batch size.

## Training and optimizer issues

- Loss does not improve: lower `learning_rate`, scale inputs, reduce architecture size, or increase `max_epochs` cautiously.
- Optimizer errors before training: make sure `NeuralNet.fit` has initialized layers and called `optimizer.setup(network)`; do not call optimizer updates manually on an uninitialized network.
- Dropout behaves unexpectedly: `NeuralNet.fit` sets `is_training=True`; `predict` and `error` should run with training disabled. Avoid calling layer `forward_pass` directly unless you manage phase state.
- Repeated `fit` calls continue from existing weights unless you call `model.reset()` or create a new model.

## CNN, RNN, and data-loader issues

- ConvNet MNIST runs are slow; use small synthetic tensors for checks.
- `load_mnist()` requires package data files to be installed. If data files are missing, reinstall the package with package data included.
- `load_nietzsche()` needs a NumPy-compatible dtype path; see the `np.bool` note above.
- RNN/LSTM state is retained in layer attributes; recreate layers or reset state for independent sequences when needed.

## DQN and Gym issues

- Newer Gym/Gymnasium returns `(obs, info)` from `reset()` and five values from `step()`. The current DQN loop expects legacy four-value `step` output.
- `play()` and `render=True` may require a display and can block headless runs.
- `monitor=True` can write monitor/video outputs; do not enable it in smoke tests.
- Training can take hundreds to thousands of episodes. For verification, use `dqn-init` smoke rather than `train`.

## Safe next checks

1. Run `scripts/run_neural_smoke.py --workflow mlp`.
2. If dense training works, run `--workflow all` for RBM and DQN wiring checks.
3. For shape failures, print `X.shape`, `y.shape`, selected layer list, `batch_size`, and final activation/loss pairing.
4. For Gym failures, inspect the active Gym reset/step API before editing DQN code.
