# Data-backed and custom problems

## Factory shape

The repository expects a **zero-argument loss builder**:

1. The outer problem factory prepares any nontrivial Python state.
2. The factory returns a `build()` function.
3. `build()` creates or reuses TensorFlow objects and returns a scalar loss tensor.

Keep Python side effects outside the inner `build()` function.

## Safe pattern for custom problems

Use this structure when authoring a new problem:

```python
def custom_problem(...):
    # Python side effects: load data, create queues, validate paths, etc.

    def build():
        x = tf.get_variable("x", shape=[], initializer=tf.ones_initializer())
        return tf.square(x)

    return build
```

### Checklist

- Return a callable that builds a scalar loss.
- Create any queues, datasets, downloads, or file checks before returning the builder.
- Choose stable variable names if you want `util.get_config` or later `net_assignments` to work.
- If you compose multiple losses, scope them explicitly so names stay predictable.
- If your problem needs a cache directory, document whether the `path` argument is a data cache or an optimizer checkpoint root.

## Built-in patterns

### `simple`, `simple_multi_optimizer`, and `quadratic`

These are pure graph factories.

- `simple()` creates one trainable scalar variable `x` and returns `x^2`.
- `simple_multi_optimizer()` creates `x_0`, `x_1`, ... and returns the sum of their squares.
- `quadratic()` creates trainable `x` plus fixed `w` and `y` variables.

They are the easiest templates for custom scalar problems.

### `ensemble`

`problems.ensemble(problems, weights=None)` is a composition helper.

- Each subproblem is a dict with `name` and `options`.
- The helper calls each subproblem factory and sums the resulting losses.
- Each component is wrapped in a `problem_i` variable scope.
- If `weights` is provided, `len(weights)` must equal `len(problems)`.

Use this when you want a synthetic multi-task optimizee without changing the inner factories.

### `mnist`

`problems.mnist(...)` loads MNIST data during factory setup.

- `activation` must be `sigmoid` or `relu`.
- `mode` must be `train` or `test`.
- `util.get_config` uses `mode="train"` when `path is None`, otherwise `mode="test"`.
- The inner builder samples minibatches and returns cross-entropy loss.

Keep MNIST loading outside the returned builder if you write a custom variant.

### `cifar10`

`problems.cifar10(...)` is the data-backed example with the most side effects.

- `_maybe_download_cifar10(path)` creates the directory if needed.
- If the tarball is missing, the factory downloads and extracts it.
- The factory creates a `RandomShuffleQueue` and registers queue runners before returning the loss builder.
- `mode` must be `train` or `test`.
- `util.get_config` uses `mode="train"` when `path is None`, otherwise `mode="test"`.

If you write a CIFAR-style custom problem, keep all download and queue setup outside the inner loss builder.

## Why this matters for `meta_minimize`

The optimizer only wants a callable that builds the loss graph.

If you put Python side effects inside the callable that is passed to `meta_minimize`, repeated unrolls can recreate queues, reload data, or trigger file-system work at the wrong time.

## Practical tips

- Use a dedicated `path` for dataset cache roots when a factory needs one.
- Use exact variable names if later code will target subsets of variables.
- Prefer small scalar or batched quadratic templates when you only need to test the optimizer wiring.
- Use the bundled inspection script to see the config shape without touching MNIST/CIFAR downloads.
