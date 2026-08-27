# Module Authoring API Reference

## Public contracts

- `snt.Module(name=None)`: base class. Subclasses own TensorFlow variables and submodules. Call `super().__init__(name=name)` before assigning Sonnet submodules.
- `@snt.once`: decorator for side-effect-only methods that should run at most once per module instance. It is commonly used to lazily create variables after seeing an input shape. The decorated method must return `None`.
- `module.variables`, `module.trainable_variables`, `module.submodules`: recursive views populated after first build/call.
- `snt.Sequential(layers)`: calls a list/tuple of callables in order. It is best for single-input/single-output chains.
- `snt.Deferred(lambda: module)`: delays construction of a module until needed, useful when input shape is not available at `__init__` time.
- `snt.BatchApply(module_or_callable, num_dims=2)`: merges leading batch dimensions, applies a callable, then restores leading dimensions.
- `snt.build(module_or_callable, example_input, *args, **kwargs)`: executes a representative call so variables are created and shape errors surface early.

## Lazy variable pattern

```python
class Affine(snt.Module):
  def __init__(self, output_size, name=None):
    super().__init__(name=name)
    self.output_size = output_size

  @snt.once
  def _initialize(self, x):
    in_size = x.shape[-1]
    if in_size is None:
      raise ValueError("last dimension must be known")
    self.w = tf.Variable(tf.random.normal([in_size, self.output_size]), name="w")
    self.b = tf.Variable(tf.zeros([self.output_size]), name="b")

  def __call__(self, x):
    self._initialize(x)
    return tf.matmul(x, self.w) + self.b
```

## Variable inspection

In Sonnet 2, requesting `variables` or `trainable_variables` before a module is built often raises a helpful `ValueError` instead of returning an empty list. After a representative call, check:

```python
module(tf.ones([2, 4]))
assert module.trainable_variables
assert any(v.name.endswith("w:0") for v in module.variables)
```
