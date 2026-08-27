# Functional Transform Workflows

## Stateless MLP

```python
fn = snt.functional
with fn.variables():
  net = snt.nets.MLP([16, 1])

def forward(x):
  return net(x)

tx = fn.transform(forward)
params = tx.init(tf.ones([2, 4]))
y = tx.apply(params, tf.ones([2, 4]))
```

Create Sonnet modules inside a `with fn.variables():` context and use them from the transformed function so Sonnet can capture TensorVariable-backed parameters. Reuse returned `params` rather than reinitializing every step.

## With state

Use `transform_with_state` for modules such as BatchNorm that own non-trainable state. Thread both `params` and `state` through every call and store updated state from `apply`.

## Gradient step

```python
def loss_fn(params, x, y):
  pred = tx.apply(params, x)
  return tf.reduce_mean(tf.square(pred - y))
loss, grads = fn.value_and_grad(loss_fn)(params, x, y)
```

Use a functional optimizer when the task wants immutable parameter/state trees. For ordinary eager training of modules, prefer the training sub-skill.

## Device helpers

Device helpers operate on nested TensorFlow structures. They do not prove GPU/TPU availability; check TensorFlow physical devices first.
