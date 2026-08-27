# Deep-learning API reference

This reference summarizes the installed ML-From-Scratch neural-network API. Use import paths directly; no source checkout is required at runtime.

## Core imports

```python
from mlfromscratch.deep_learning import NeuralNetwork
from mlfromscratch.deep_learning.layers import (
    Dense, Activation, Dropout, Flatten, Conv2D, MaxPooling2D,
    AveragePooling2D, BatchNormalization, RNN, Reshape, UpSampling2D,
    ZeroPadding2D, ConstantPadding2D,
)
from mlfromscratch.deep_learning.optimizers import (
    Adam, StochasticGradientDescent, RMSprop, Adagrad, Adadelta,
    NesterovAcceleratedGradient,
)
from mlfromscratch.deep_learning.loss_functions import CrossEntropy, SquareLoss
from mlfromscratch.utils import to_categorical, train_test_split, normalize
```

`SGD` and `NAG` are common shorthand names in explanations, but the package exports the classes as `StochasticGradientDescent` and `NesterovAcceleratedGradient`.

## Model contract

| Object | Signature | Notes |
| --- | --- | --- |
| `NeuralNetwork` | `NeuralNetwork(optimizer, loss, validation_data=None)` | Pass an optimizer instance and a loss class, not a loss instance. Example: `NeuralNetwork(optimizer=Adam(), loss=CrossEntropy)`. |
| `.add(layer)` | `model.add(layer)` | Sets non-first layer input shapes from the previous layer's `output_shape()` and initializes trainable layers. |
| `.fit` | `model.fit(X, y, n_epochs, batch_size)` | Returns `(training_errors, validation_errors)`. Progressbar output is normal unless replaced in a smoke script. |
| `.train_on_batch` | `model.train_on_batch(X_batch, y_batch)` | One gradient update; useful for custom loops such as GAN training. |
| `.test_on_batch` | `model.test_on_batch(X_batch, y_batch)` | Returns `(loss, accuracy)` using the configured loss. |
| `.predict` | `model.predict(X)` | Runs inference with `training=False`; dropout uses pass-through scaling instead of a random mask. |
| `.summary` | `model.summary(name='Model Summary')` | Prints layer table, parameters, and output shapes. Requires at least one layer. |
| `.set_trainable` | `model.set_trainable(trainable)` | Freezes or unfreezes layer updates; used by combined generator/discriminator workflows. |

## Shape conventions

Layer `input_shape` excludes the batch dimension. Runtime arrays include the batch dimension.

| Workflow | Runtime `X` shape | First layer `input_shape` | Typical output `y` shape |
| --- | --- | --- | --- |
| Dense MLP | `(n_samples, n_features)` | `(n_features,)` | For `CrossEntropy`: `(n_samples, n_classes)` one-hot. |
| CNN image classifier | `(n_samples, channels, height, width)` | `(channels, height, width)` | `(n_samples, n_classes)` one-hot after `Flatten()` and dense classifier head. |
| RNN sequence model | `(n_samples, timesteps, input_dim)` | `(timesteps, input_dim)` | Usually `(n_samples, timesteps, input_dim)` or matching sequence output. |
| Autoencoder | `(n_samples, n_features)` or image tensor | Encoder input shape; decoder input is latent shape | Target is usually the same as input for reconstruction. |
| GAN generator | `(n_samples, latent_dim)` | `(latent_dim,)` | Generator output shape must match discriminator input shape. |

## Layer catalog

| Layer | Signature | Output shape rule | Common use |
| --- | --- | --- | --- |
| `Dense` | `Dense(n_units, input_shape=None)` | `(n_units,)` | MLP blocks and classifier heads. First dense layer needs `input_shape=(n_features,)`. |
| `Activation` | `Activation(name)` | Same as input | Add after dense/conv/RNN outputs. Names are lowercase strings listed below. |
| `Dropout` | `Dropout(p=0.2)` | Same as input | Regularization after activations. During inference it scales by `1-p`. |
| `Conv2D` | `Conv2D(n_filters, filter_shape, input_shape=None, padding='same', stride=1)` | `(n_filters, out_height, out_width)` | Channels-first image tensors. First conv needs `input_shape=(channels, height, width)`. |
| `MaxPooling2D` | `MaxPooling2D(pool_shape=(2, 2), stride=1, padding=0)` | `(channels, pooled_height, pooled_width)` | Downsampling after conv/activation blocks. Pool dimensions must divide cleanly. |
| `AveragePooling2D` | `AveragePooling2D(pool_shape=(2, 2), stride=1, padding=0)` | `(channels, pooled_height, pooled_width)` | Average downsampling with the same constraints as max pooling. |
| `BatchNormalization` | `BatchNormalization(momentum=0.99)` | Same as input | Normalizes dense or convolutional activations; initialized after input shape is known. |
| `Flatten` | `Flatten(input_shape=None)` | `(prod(input_shape),)` | Bridge image/tensor outputs to dense classifier heads. |
| `RNN` | `RNN(n_units, activation='tanh', bptt_trunc=5, input_shape=None)` | Same as input shape | Vanilla recurrent block for sequence-to-sequence toy tasks. |
| `Reshape` | `Reshape(shape, input_shape=None)` | `shape` | Generator/decoder reshaping, excluding batch dimension. |
| `UpSampling2D` | `UpSampling2D(size=(2, 2), input_shape=None)` | `(channels, size[0] * height, size[1] * width)` | DCGAN-style generator upsampling. |
| `ZeroPadding2D` | `ZeroPadding2D(padding)` | Pads height/width | Convolutional alignment for channels-first tensors. |
| `ConstantPadding2D` | `ConstantPadding2D(padding, padding_value=0)` | Pads height/width | Nonzero padding variant. |

## Activation catalog

Use exactly these strings in `Activation(name)` and `RNN(..., activation=name)` where applicable:

| Name | Class | Notes |
| --- | --- | --- |
| `'relu'` | `ReLU` | Default hidden activation for simple MLP/CNN examples. |
| `'leaky_relu'` | `LeakyReLU(alpha=0.2)` | Used in deeper MLP/GAN examples. |
| `'sigmoid'` | `Sigmoid` | Binary-style nonlinear output or hidden activation. |
| `'softmax'` | `Softmax` | Multiclass probability output; pair with `CrossEntropy`. |
| `'tanh'` | `TanH` | RNN default and generator output in examples scaled to `[-1, 1]`. |
| `'softplus'` | `SoftPlus` | Smooth ReLU-like option. |
| `'elu'` | `ELU(alpha=0.1)` | Exponential linear unit. |
| `'selu'` | `SELU` | Self-normalizing activation constants built in. |

## Losses and target encoding

| Loss | Signature | Use with | Target expectations |
| --- | --- | --- | --- |
| `CrossEntropy` | `CrossEntropy()` | Classification, softmax outputs, discriminator heads | One-hot array. For labels `[0, 1, 2]`, call `to_categorical(labels.astype('int'), n_col=n_classes)`. |
| `SquareLoss` | `SquareLoss()` | Regression, reconstruction, Q-value outputs | Numeric target array with the same shape as predictions. |

`CrossEntropy.acc` computes accuracy by `argmax` on class axis. If labels are integer-coded or output units do not match classes, accuracy and gradients will be wrong or fail.

## Optimizer catalog

| Optimizer | Signature | Notes |
| --- | --- | --- |
| `Adam` | `Adam(learning_rate=0.001, b1=0.9, b2=0.999)` | Recommended default for most small neural-network workflows. |
| `StochasticGradientDescent` | `StochasticGradientDescent(learning_rate=0.01, momentum=0)` | The package's SGD implementation. Use a short alias locally only if you define it yourself. |
| `RMSprop` | `RMSprop(learning_rate=0.01, rho=0.9)` | Adaptive gradient method. |
| `Adagrad` | `Adagrad(learning_rate=0.01)` | Adaptive method that accumulates squared gradients. |
| `Adadelta` | `Adadelta(rho=0.95, eps=1e-6)` | Adaptive method without an explicit learning-rate parameter. |
| `NesterovAcceleratedGradient` | `NesterovAcceleratedGradient(learning_rate=0.001, momentum=0.4)` | Present in the package, but its `update` method expects a gradient function while network layers pass gradient arrays. Prefer the other optimizers for ordinary `NeuralNetwork` layers unless you adapt the update contract deliberately. |

## Minimal classifier skeleton

```python
import numpy as np
from mlfromscratch.deep_learning import NeuralNetwork
from mlfromscratch.deep_learning.layers import Dense, Activation
from mlfromscratch.deep_learning.optimizers import Adam
from mlfromscratch.deep_learning.loss_functions import CrossEntropy
from mlfromscratch.utils import to_categorical

X = np.asarray([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
y = to_categorical(np.asarray([0, 1, 1, 0]), n_col=2)

model = NeuralNetwork(optimizer=Adam(learning_rate=0.01), loss=CrossEntropy)
model.add(Dense(4, input_shape=(2,)))
model.add(Activation('relu'))
model.add(Dense(2))
model.add(Activation('softmax'))
train_loss, _ = model.fit(X, y, n_epochs=1, batch_size=2)
probs = model.predict(X)
```
