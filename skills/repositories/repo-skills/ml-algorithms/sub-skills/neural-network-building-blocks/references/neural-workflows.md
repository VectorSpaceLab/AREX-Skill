# Longer neural workflow notes

## Purpose

Read this for the repository's longer CNN and recurrent patterns. These are reference workflows, not default verification commands, because they can be slow and may need package data or compatibility pins.

## CNN MNIST pattern

The package includes a loader that returns MNIST arrays shaped for convolution:

```python
from mla.datasets import load_mnist
from mla.utils import one_hot

X_train, X_test, y_train, y_test = load_mnist()
X_train = X_train / 255.0
X_test = X_test / 255.0
y_train = one_hot(y_train.flatten())
y_test = one_hot(y_test.flatten())
```

A ConvNet stack follows this pattern:

```python
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Convolution, Activation, MaxPooling, Dropout, Flatten, Dense
from mla.neuralnet.optimizers import Adadelta

model = NeuralNet(
    layers=[
        Convolution(n_filters=32, filter_shape=(3, 3), padding=(1, 1), stride=(1, 1)),
        Activation("relu"),
        Convolution(n_filters=32, filter_shape=(3, 3), padding=(1, 1), stride=(1, 1)),
        Activation("relu"),
        MaxPooling(pool_shape=(2, 2), stride=(2, 2)),
        Dropout(0.5),
        Flatten(),
        Dense(128),
        Activation("relu"),
        Dropout(0.5),
        Dense(10),
        Activation("softmax"),
    ],
    loss="categorical_crossentropy",
    optimizer=Adadelta(),
    metric="accuracy",
    batch_size=128,
    max_epochs=3,
)
```

The original workflow comments indicate a long per-epoch runtime. Prefer synthetic tensor smoke tests unless the user explicitly requests a full MNIST run.

## Binary addition with recurrent layers

The sequence addition pattern builds 3D binary tensors `(samples, bits, 2)` and target tensors `(samples, bits, 1)`, then trains an `LSTM` or `RNN` with `TimeDistributedDense(1)` and `Activation("sigmoid")`.

Key constraints:

- Round sample counts so train/test sizes are multiples of `batch_size`.
- Use `return_sequences=True` because there is a target at each timestep.
- Keep `dim`, `n_samples`, and `max_epochs` small for checks.

## Text generation with recurrent layers

The Nietzsche text workflow uses `load_nietzsche()` to create one-hot sequences and trains an `LSTM(128, return_sequences=False)` followed by `Dense(vocab_size)` and `Activation("softmax")`.

Compatibility caveats:

- `load_nietzsche()` in version `0.0.1` uses deprecated `np.bool`; NumPy below `1.24` avoids that failure, or patch the loader to use `bool`/`np.bool_`.
- The training loop in the original workflow repeatedly fits and samples generated text. Treat this as a manual educational run, not a smoke check.
- Sampling uses temperature-scaled multinomial draws; seed randomness if reproducibility matters.

## When to use these longer workflows

Use them only when the user specifically asks for CNN/RNN/LSTM examples or educational reproduction. For normal environment validation, run the bundled short neural smoke instead.
