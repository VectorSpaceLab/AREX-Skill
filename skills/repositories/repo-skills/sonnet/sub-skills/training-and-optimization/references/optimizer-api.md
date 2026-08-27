# Sonnet Optimizer API Reference

Sonnet optimizers are object-oriented TensorFlow optimizers with a common `apply(updates, parameters)` method. `updates` are usually gradients from `tf.GradientTape`; `parameters` are the variables to update.

## Public optimizers

- `snt.optimizers.SGD(learning_rate)` and `snt.SGD` apply vanilla gradient descent. `learning_rate` may be a float scalar or TensorFlow variable/tensor.
- `snt.optimizers.Momentum(learning_rate, momentum=0.9, use_nesterov=False)` keeps velocity slots.
- `snt.optimizers.RMSProp(learning_rate, decay=0.9, momentum=0.0, epsilon=1e-8, centered=False)` keeps moving-average slots.
- `snt.optimizers.Adam(learning_rate, beta1=0.9, beta2=0.999, epsilon=1e-8)` keeps first/second moment slots.

## Apply contract

```python
with tf.GradientTape() as tape:
  loss = compute_loss(model(x), y)
variables = model.trainable_variables
gradients = tape.gradient(loss, variables)
optimizer.apply(gradients, variables)
```

Validation checks include equal gradient/parameter nesting, trainable floating parameters, non-`None` gradients where required, and compatible dense/sparse update shapes.

## State behavior

Optimizers lazily create slot variables on first `apply`. Use the same optimizer instance across steps. If you checkpoint a training loop, include both model and optimizer objects after at least one step.
