# Sonnet Module Patterns

## Custom module with lazy shape-dependent variables

Use `@snt.once` for variables whose shape depends on input tensors. Validate `x.shape[-1]` before creating weights; TensorFlow variables need fully known shape dimensions.

## Composition with submodules

Create child modules in `__init__` when their constructor arguments are known:

```python
class Classifier(snt.Module):
  def __init__(self, num_classes):
    super().__init__()
    self.net = snt.nets.MLP([128, num_classes])
  def __call__(self, x):
    return self.net(x)
```

Use `snt.Deferred` only when construction itself must wait for input-dependent information. Prefer normal submodule attributes otherwise because they are clearer and easier to checkpoint.

## Sequential chains

`Sequential` is concise for pure chains:

```python
model = snt.Sequential([
    snt.Linear(32), tf.nn.relu,
    snt.Linear(10),
])
```

Do not use it for branches, multiple arguments, auxiliary losses, or calls that require `is_training`; create a named `snt.Module` instead.

## BatchApply

`BatchApply` is useful when a 2-D module should apply over several leading dimensions:

```python
linear = snt.BatchApply(snt.Linear(7), num_dims=2)
y = linear(tf.ones([3, 5, 11]))  # [3, 5, 7]
```

## Build-before-use rule

Call the module or `snt.build` before serialization, optimizer creation checks, or shape-based assertions. This prevents false reports that a module has no variables.
