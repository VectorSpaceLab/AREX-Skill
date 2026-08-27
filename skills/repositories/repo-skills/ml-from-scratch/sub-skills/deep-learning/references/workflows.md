# Deep-learning workflows

Use these workflows to assemble small, inspectable ML-From-Scratch neural networks. They assume an environment where `mlfromscratch` is importable and run on CPU.

## Fast validation workflow

Before debugging a user-specific model, validate the installed neural-network stack with a tiny deterministic smoke:

```bash
python scripts/run_mlp_smoke.py
python scripts/run_cnn_smoke.py
```

Both scripts avoid plotting and set headless behavior. Add `--help` to see tunable sample counts, epochs, and batch sizes.

## MLP multiclass classifier

Best for tabular features shaped `(n_samples, n_features)`.

Checklist:

1. Normalize or standardize numeric features if scale varies widely.
2. Convert integer labels to one-hot targets with a fixed class count.
3. Add a first `Dense` layer with `input_shape=(n_features,)`.
4. Use hidden `Activation('relu')` or `Activation('leaky_relu')` after each hidden dense layer.
5. End with `Dense(n_classes)` and `Activation('softmax')` when using `CrossEntropy`.
6. Use a short `n_epochs` first; only extend training after shape and loss are finite.

Skeleton:

```python
from mlfromscratch.deep_learning import NeuralNetwork
from mlfromscratch.deep_learning.layers import Dense, Dropout, Activation
from mlfromscratch.deep_learning.optimizers import Adam
from mlfromscratch.deep_learning.loss_functions import CrossEntropy
from mlfromscratch.utils import to_categorical

n_features = X_train.shape[1]
n_classes = 10
y_train_oh = to_categorical(y_train.astype('int'), n_col=n_classes)
y_val_oh = to_categorical(y_val.astype('int'), n_col=n_classes)

model = NeuralNetwork(
    optimizer=Adam(learning_rate=0.001),
    loss=CrossEntropy,
    validation_data=(X_val, y_val_oh),
)
model.add(Dense(64, input_shape=(n_features,)))
model.add(Activation('leaky_relu'))
model.add(Dropout(0.25))
model.add(Dense(n_classes))
model.add(Activation('softmax'))
train_err, val_err = model.fit(X_train, y_train_oh, n_epochs=1, batch_size=32)
```

## Tiny XOR or binary-as-two-class smoke

For binary classification with `CrossEntropy`, prefer a two-unit softmax head rather than a single scalar output because the package accuracy helper assumes class-axis `argmax`.

```python
X = np.array([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
y = to_categorical(np.array([0, 1, 1, 0]), n_col=2)
model.add(Dense(4, input_shape=(2,)))
model.add(Activation('relu'))
model.add(Dense(2))
model.add(Activation('softmax'))
```

A one-epoch smoke only proves imports, shapes, forward pass, backpropagation, and finite loss. It should not be treated as model quality evidence.

## CNN image classifier

The convolution implementation expects channels-first batches: `(n_samples, channels, height, width)`.

Checklist:

1. Reshape flat images to channels-first form.
2. First convolution gets `input_shape=(channels, height, width)`.
3. Use `Conv2D -> Activation -> optional Dropout/BatchNormalization` blocks.
4. Add `Flatten()` before any dense classifier head.
5. End with `Dense(n_classes)` and `Activation('softmax')` for `CrossEntropy`.
6. Keep filters and epochs very small for CPU checks.

Skeleton:

```python
X_train_img = X_train.reshape((-1, 1, 8, 8))
X_val_img = X_val.reshape((-1, 1, 8, 8))
y_train_oh = to_categorical(y_train.astype('int'), n_col=10)
y_val_oh = to_categorical(y_val.astype('int'), n_col=10)

model = NeuralNetwork(optimizer=Adam(learning_rate=0.001), loss=CrossEntropy,
                      validation_data=(X_val_img, y_val_oh))
model.add(Conv2D(n_filters=4, filter_shape=(3, 3), input_shape=(1, 8, 8), padding='same'))
model.add(Activation('relu'))
model.add(Flatten())
model.add(Dense(10))
model.add(Activation('softmax'))
train_err, val_err = model.fit(X_train_img, y_train_oh, n_epochs=1, batch_size=8)
```

Use pooling only after verifying dimensions. With `pool_shape=(2, 2)` and `stride=2`, height and width must produce integer pooled dimensions.

## RNN sequence-to-sequence toy model

The `RNN` layer consumes 3D tensors `(n_samples, timesteps, input_dim)` and returns the same timestep/input-dimensional output shape. It is best suited for small one-hot sequence problems.

Checklist:

1. Encode each timestep as one-hot vectors, e.g. `X.shape == (batch, timesteps, vocab_size)`.
2. Targets should match the sequence output shape when using `CrossEntropy`.
3. First layer: `RNN(n_units, activation='tanh', bptt_trunc=5, input_shape=(timesteps, vocab_size))`.
4. Add `Activation('softmax')` after `RNN` for per-timestep categorical probabilities.
5. Use small `n_epochs` until loss is finite; long sequence demos can be slow.

Skeleton:

```python
model = NeuralNetwork(optimizer=Adam(), loss=CrossEntropy)
model.add(RNN(10, activation='tanh', bptt_trunc=5, input_shape=(timesteps, vocab_size)))
model.add(Activation('softmax'))
train_err, _ = model.fit(X_train, y_train, n_epochs=1, batch_size=32)
y_pred = model.predict(X_test).argmax(axis=2)
```

For reporting sequence accuracy, compute it outside `CrossEntropy.acc` with an explicit axis and mask if needed.

## Autoencoder-style reconstruction

Use `SquareLoss` when the target is the input itself. A compact fully connected autoencoder combines an encoder and decoder by extending layer lists.

Pattern:

```python
optimizer = Adam(learning_rate=0.0002, b1=0.5)
encoder = NeuralNetwork(optimizer=optimizer, loss=SquareLoss)
encoder.add(Dense(128, input_shape=(input_dim,)))
encoder.add(Activation('leaky_relu'))
encoder.add(Dense(latent_dim))

decoder = NeuralNetwork(optimizer=optimizer, loss=SquareLoss)
decoder.add(Dense(128, input_shape=(latent_dim,)))
decoder.add(Activation('leaky_relu'))
decoder.add(Dense(input_dim))
decoder.add(Activation('tanh'))

autoencoder = NeuralNetwork(optimizer=optimizer, loss=SquareLoss)
autoencoder.layers.extend(encoder.layers)
autoencoder.layers.extend(decoder.layers)
loss, _ = autoencoder.train_on_batch(batch, batch)
```

Keep reconstruction experiments bounded: use synthetic data or already-local small arrays, tiny batches, and no image saving unless explicitly requested.

## GAN and DCGAN model-builder pattern

GAN-style workflows use multiple `NeuralNetwork` objects and the `set_trainable` flag:

1. Build a discriminator ending with two softmax units for valid/fake one-hot labels.
2. Build a generator that maps latent vectors to discriminator-compatible sample shape.
3. Combine by appending generator layers followed by discriminator layers to a new `NeuralNetwork`.
4. Train discriminator with `discriminator.set_trainable(True)` on real and generated batches.
5. Train generator through the combined model after `discriminator.set_trainable(False)`.

For DCGAN-style builders, use `Dense -> Reshape -> UpSampling2D -> Conv2D -> Activation` in the generator and channels-first `Conv2D` blocks in the discriminator. Verify each intermediate `output_shape()` with `.summary()` before training.

Avoid unbounded generative runs by default. Large image datasets, hundreds of thousands of epochs, and periodic image writes are outside a smoke check and should require explicit user intent.

## DQN model-builder handoff

When a DQN workflow asks for a model builder, this sub-skill can provide only the neural network callback pattern:

```python
def model(n_inputs, n_outputs):
    net = NeuralNetwork(optimizer=Adam(), loss=SquareLoss)
    net.add(Dense(64, input_shape=(n_inputs,)))
    net.add(Activation('relu'))
    net.add(Dense(n_outputs))
    return net
```

Send environment reset/step API issues, replay training, epsilon schedule, rendering, and Gym version compatibility to `reinforcement-learning`.

## Bounded debugging loop

Use this loop when constructing a new model:

1. Print or inspect the intended runtime `X.shape` and target `y.shape`.
2. Map runtime shape to first layer `input_shape` by removing only the batch dimension.
3. Add layers incrementally and call `model.summary()` after assembly.
4. Run one `train_on_batch` or one epoch with the smallest representative batch.
5. Assert finite loss, prediction shape, and probability class dimension before tuning accuracy.
6. Only then increase epochs, hidden units, filters, or dataset size.
