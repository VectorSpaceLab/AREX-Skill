# TensorFlow Integration

TFLearn can train a pure TensorFlow graph when the graph provides placeholders, a loss tensor, an optimizer, and optional metrics. This is the right route for custom models, GAN losses, wide/deep multi-optimizer setups, validation monitors, or recipes that do not fit a simple `DNN(regression(...))` wrapper.

## Minimal Custom Graph Pattern

Use this pattern when adapting any pure TensorFlow graph:

```python
import numpy as np
import tensorflow.compat.v1 as tf
import tflearn

tf.disable_v2_behavior()
np.random.seed(7)
tf.set_random_seed(7)

with tf.Graph().as_default():
    X = tf.placeholder(tf.float32, [None, 2], name="X")
    Y = tf.placeholder(tf.float32, [None, 2], name="Y")

    W1 = tf.Variable(tf.random_normal([2, 4], stddev=0.1), name="W1")
    b1 = tf.Variable(tf.zeros([4]), name="b1")
    W2 = tf.Variable(tf.random_normal([4, 2], stddev=0.1), name="W2")
    b2 = tf.Variable(tf.zeros([2]), name="b2")

    hidden = tf.nn.tanh(tf.matmul(X, W1) + b1)
    logits = tf.matmul(hidden, W2) + b2
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=Y))
    metric = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(logits, 1), tf.argmax(Y, 1)), tf.float32), name="acc")

    trainop = tflearn.TrainOp(
        loss=loss,
        optimizer=tf.train.GradientDescentOptimizer(learning_rate=0.1),
        metric=metric,
        batch_size=4,
    )
    trainer = tflearn.Trainer(train_ops=trainop, tensorboard_verbose=0)
    trainer.fit({X: train_x, Y: train_y}, n_epoch=2, show_metric=True, snapshot_epoch=False)
```

The bundled [`../scripts/custom_trainer_smoke.py`](../scripts/custom_trainer_smoke.py) turns this pattern into a safe no-network command with tiny synthetic arrays.

## `TrainOp` and `Trainer` Contracts

- `tflearn.TrainOp` expects a TensorFlow loss tensor and a `tf.train.Optimizer` instance. Unlike `tflearn.regression`, it does not accept optimizer names such as `'adam'` directly.
- `metric` should be a tensor, usually a scalar or batch-reduced scalar. Set it to `None` if the task has no meaningful metric.
- `trainable_vars` restricts updates to a subset of variables. Use it for GAN generator/discriminator isolation, recommender wide/deep heads, and partial fine-tuning.
- `validation_monitors` can hold tensors evaluated during validation snapshots and summarized for TensorBoard. Keep monitors cheap and deterministic in smokes.
- `Trainer.fit` accepts a single feed dict or a list of feed dicts for multiple train ops. For multiple optimizers, align each feed dict with the corresponding `TrainOp`.
- Use `snapshot_epoch=False` for smoke tests unless checkpoint behavior is the workflow under test.
- Use `tensorboard_verbose=0` for fast validation. Higher levels summarize gradients, weights, activations, and sparsity and can slow small tests.

## Connecting TFLearn Layers to TensorFlow Ops

TFLearn layers return TensorFlow tensors. You can mix them with raw TensorFlow ops as long as graph collections are consistent.

- To wrap an existing TensorFlow placeholder as a TFLearn input, call `tflearn.input_data(shape=..., placeholder=existing_placeholder, name='input_name')`.
- To make TFLearn trainers discover targets, pass an explicit target placeholder to `tflearn.regression(..., placeholder=target_placeholder, name='target_name')` or create a `TrainOp` manually.
- To summarize custom activations, add them to `tf.GraphKeys.ACTIVATIONS` and choose a `tensorboard_verbose` level that includes activations.
- To include custom regularization in training loss, add regularizers to `tf.GraphKeys.REGULARIZATION_LOSSES` or use `tflearn.add_weights_regularizer` / `tflearn.variable(..., regularizer='L2')`.

## Multiple Optimizers and Scoped Variables

Advanced examples often build several losses over the same graph.

### GAN-style isolation

- Put generator variables under a `Generator` variable scope and discriminator variables under `Discriminator`.
- Retrieve variables with `tflearn.get_layer_variables_by_scope('Generator')` and `tflearn.get_layer_variables_by_scope('Discriminator')`.
- Use `tflearn.regression(..., placeholder=None, loss=custom_loss, trainable_vars=vars, op_name='GEN')` when the loss already closes over all required tensors and no target placeholder is needed.
- For discriminator targets that concatenate fake and real branches, use `tflearn.multi_target_data([...], shape=[None, n_classes])` and feed each named target separately.

### Wide/deep recommender isolation

- Keep the continuous input named, for example, `wide_X`.
- Give each categorical feature a separate integer placeholder such as `workclass_in`, then embed and squeeze it before concatenating with continuous features.
- Create separate regression/train ops for wide and deep heads if they use different optimizers or learning rates.
- Restrict `trainable_vars` by variable name prefixes when only one branch should update.
- Feed `DNN.fit` dictionaries keyed by input and target names so the many placeholders do not depend on creation order.

### Custom validation monitors

Validation monitors are useful for confusion matrix entries, AUC-like counters, or domain-specific totals. Keep them tensors inside the graph and pass them to either `tflearn.regression(..., validation_monitors=[...])` or `tflearn.TrainOp(..., validation_monitors=[...])`. For smoke tests, prefer simple reductions over large tensors.

## Session Reuse for Generator-Only Prediction

Several generative recipes train a full model and then create a second model for generation or decoding. Reuse the training session so the second model sees learned weights:

```python
training_model = tflearn.DNN(training_network)
training_model.fit(X_train, Y_train, n_epoch=1, snapshot_epoch=False)

generator_model = tflearn.DNN(generator_tensor, session=training_model.session)
samples = generator_model.predict(generator_inputs)
```

This pattern is used for autoencoder/VAE decoders and can also be useful for inspecting intermediate tensors. Ensure the generator tensor was built in the same graph and variable scopes as the trained weights.

## TensorFlow 2.x Caveat

These recipes are TensorFlow 1.x style. TensorFlow 2.x removes or relocates several internals used by TFLearn and its estimator examples, especially `tensorflow.contrib`. If `import tflearn` fails under a modern TensorFlow version, switch to a TF1-compatible environment instead of patching recipe code during a smoke test. See [Troubleshooting](troubleshooting.md) for exact signals.
