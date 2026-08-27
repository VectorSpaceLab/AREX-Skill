# Training Workflows

## Tiny eager loop

```python
model = snt.nets.MLP([32, 1])
optimizer = snt.optimizers.Adam(1e-2)
for step in range(20):
  with tf.GradientTape() as tape:
    pred = model(x)
    loss = tf.reduce_mean(tf.square(pred - y))
  variables = model.trainable_variables
  gradients = tape.gradient(loss, variables)
  optimizer.apply(gradients, variables)
```

Run one forward pass before checking variables. In a `tf.function`, keep model and optimizer construction outside the decorated function.

## Metrics

Sonnet metric modules are stateful. Call them on batches, read their value, and reset or recreate them between logically separate evaluations.

## Synthetic data over downloads

When validating a Sonnet recipe, prefer deterministic tensor fixtures over dataset downloads. The repository's MNIST examples demonstrate the pattern but not a required dependency for Sonnet itself.

## Checkpointing training

After the first optimizer step, checkpoint both model and optimizer so slot variables are included:

```python
ckpt = tf.train.Checkpoint(model=model, optimizer=optimizer)
path = ckpt.save(prefix)
```

Use the serialization sub-skill for restoration and SavedModel export details.
