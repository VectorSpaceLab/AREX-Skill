# Deep-learning troubleshooting

Use this guide for common ML-From-Scratch neural-network failures. Start with shapes and label encoding before changing optimizers or model size.

## Quick diagnostic questions

1. What is the runtime `X.shape` including the batch dimension?
2. What is the first layer's `input_shape`, excluding the batch dimension?
3. What are `y.shape` and the network output shape?
4. Is `CrossEntropy` receiving one-hot targets and a softmax output with matching class units?
5. Did the model validate with one tiny batch or one epoch before increasing size?

## Failure matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Error while adding the first `Dense` layer, often involving `None`, subscriptable types, or `input_shape[0]`. | Missing `input_shape` on the first shape-bearing layer. | Add `Dense(n_units, input_shape=(n_features,))` for tabular data. Do not rely on automatic shape inference for the first layer. |
| Dot-product shape mismatch in a dense layer. | Included the batch dimension in `input_shape`, or passed data with a different feature count than the first dense layer expects. | If `X.shape == (batch, features)`, use `input_shape=(features,)`, not `(batch, features)`. |
| `CrossEntropy` raises broadcasting errors, accuracy is nonsensical, or loss is not finite. | Integer labels were passed directly, or target class dimension does not match predictions. | Convert labels with `to_categorical(labels.astype('int'), n_col=n_classes)`. End model with `Dense(n_classes)` and `Activation('softmax')`. |
| Binary classification with a single output behaves unexpectedly. | The package's classification accuracy helper uses `argmax` on class axis. | For `CrossEntropy`, model binary labels as two classes: one-hot targets of shape `(n_samples, 2)`, `Dense(2)`, `Activation('softmax')`. Use `SquareLoss` only for scalar regression-style targets. |
| Output probabilities have shape `(n_samples, k)` but labels are `(n_samples, m)`. | Output units do not match class count. | Set the final dense units to the exact class count used in `to_categorical(..., n_col=class_count)`. |
| First layer is `Activation`, `Dropout`, `BatchNormalization`, or `Flatten` and later layers fail. | The first layer did not establish a concrete input shape for trainable layers. | Start with a shape-bearing layer such as `Dense(..., input_shape=...)`, `Conv2D(..., input_shape=...)`, `RNN(..., input_shape=...)`, `Flatten(input_shape=...)`, or `Reshape(..., input_shape=...)`. |
| CNN fails with unpacking or shape mismatch around convolution. | Image data is channels-last or missing the channel dimension. | Use channels-first arrays: `(n_samples, channels, height, width)`. For 8x8 grayscale images, reshape to `(-1, 1, 8, 8)` and set `input_shape=(1, 8, 8)`. |
| `Flatten` to `Dense` has wrong parameter count or dense dot-product failure. | `Flatten()` was omitted, or a previous conv/pooling output shape is not what the dense head expects. | Insert `Flatten()` before `Dense` after image-like tensors. Call `model.summary()` and verify `Flatten` output equals the dense input feature count. |
| Pooling asserts that output height or width is not an integer. | `pool_shape`, `stride`, and current image dimensions are incompatible. | Use dimensions where `(height - pool_h) / stride + 1` and `(width - pool_w) / stride + 1` are integers, or adjust stride/pool size. |
| Activation name key error. | Activation string has wrong case or spelling. | Use exact lowercase names: `relu`, `sigmoid`, `selu`, `elu`, `softmax`, `leaky_relu`, `tanh`, `softplus`. |
| Training is much slower than expected. | Full examples use many epochs, large hidden layers/filters, plotting, or large datasets. | Reduce to one epoch, small samples, small hidden units/filters, and no plotting. Validate with bundled smoke scripts before scaling. |
| Logs contain progressbar control output. | `NeuralNetwork.fit` wraps epochs with a progressbar by default. | This is normal. For scripts or tests that need quiet logs, set `model.progressbar = lambda iterable: iterable` before calling `.fit`. |
| Plotting blocks, crashes on display, or hangs in headless environments. | Matplotlib selected an interactive backend or code calls `plt.show()`. | Set `MPLBACKEND=Agg` before importing plotting libraries. For smokes, do not call `show()` and avoid writing images unless requested. |
| Validation loss shape differs from training loss or validation fails. | `validation_data` uses raw labels or unreshaped arrays while training data was encoded/reshaped. | Apply the same one-hot encoding and shape transformations to validation data before passing `validation_data=(X_val, y_val)`. |
| GAN combined training updates the discriminator while training the generator. | The discriminator was not frozen in the combined model step. | Call `discriminator.set_trainable(False)` before generator-through-combined updates, then restore `True` for discriminator batches. |
| `NesterovAcceleratedGradient` fails when used as a drop-in layer optimizer. | Its `update` method expects a gradient function, while the network layers pass gradient arrays. | Prefer `Adam`, `StochasticGradientDescent`, `RMSprop`, `Adagrad`, or `Adadelta` for ordinary `NeuralNetwork` layers unless adapting the optimizer contract. |

## Synthetic case: missing first dense input shape

Problem pattern:

```python
model = NeuralNetwork(optimizer=Adam(), loss=CrossEntropy)
model.add(Dense(4))          # Missing input_shape on first trainable layer
model.add(Activation('relu'))
```

Diagnosis:

- `NeuralNetwork.add` only auto-fills a layer's input shape when there is a previous layer.
- A first `Dense` layer initializes weights from `self.input_shape[0]`; without a shape it cannot initialize.

Repair:

```python
model.add(Dense(4, input_shape=(X.shape[1],)))
```

For image tensors, use `Conv2D(..., input_shape=(channels, height, width))`. For sequence tensors, use `RNN(..., input_shape=(timesteps, input_dim))`.

## Synthetic case: integer labels to one-hot multiclass

Problem pattern:

```python
y_train = np.array([0, 2, 1, 2])
model.add(Dense(3))
model.add(Activation('softmax'))
model.fit(X_train, y_train, n_epochs=1, batch_size=2)  # wrong target shape
```

Repair:

```python
n_classes = 3
y_train = to_categorical(y_train.astype('int'), n_col=n_classes)
model.add(Dense(n_classes))
model.add(Activation('softmax'))
```

Confirm after repair:

```python
probs = model.predict(X_train)
assert probs.shape == y_train.shape
assert np.all(np.isfinite(probs))
```

## Headless and quiet smoke pattern

```python
import os
os.environ.setdefault('MPLBACKEND', 'Agg')
model.progressbar = lambda iterable: iterable
```

Set the backend before any plotting import. The bundled smoke scripts use this pattern and perform no network access, no credential access, and no destructive writes.
