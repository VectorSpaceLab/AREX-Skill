# Problem catalog

This repo uses two naming layers:

- README-facing names: `simple`, `simple-multi`, `quadratic`, `mnist`, `cifar`, `cifar-multi`.
- Source factories: `problems.simple`, `problems.simple_multi_optimizer`, `problems.quadratic`, `problems.ensemble`, `problems.mnist`, and `problems.cifar10`.

`util.get_config(problem_name, path=None)` accepts the README-style keys, not the source factory names.

## Built-in factories

| Factory | What it builds | Side effects / notes |
| --- | --- | --- |
| `simple()` | A scalar quadratic loss `x^2` for one trainable variable named `x`. | Pure graph construction. No data access. |
| `simple_multi_optimizer(num_dims=2)` | A sum of independent scalar quadratics over `x_0 ... x_{n-1}`. | Pure graph construction. The default `num_dims` is 2. |
| `quadratic(batch_size=128, num_dims=10, stddev=0.01, dtype=tf.float32)` | A batched quadratic loss `||Wx - y||` with trainable `x` and fixed `w`, `y`. | Pure graph construction. Uses non-trainable `w` and `y` variables. |
| `ensemble(problems, weights=None)` | A weighted sum of subproblem losses. | `weights` must be the same length as `problems` when provided. Each component is wrapped in `problem_i` scope. |
| `mnist(layers, activation="sigmoid", batch_size=128, mode="train")` | A multilayer perceptron for MNIST classification. | Loads MNIST data during factory setup. `activation` only accepts `sigmoid` or `relu`. |
| `cifar10(path, conv_channels=None, linear_layers=None, batch_norm=True, batch_size=128, num_threads=4, min_queue_examples=1000, mode="train")` | A convolutional CIFAR-10 classifier. | May download/extract CIFAR-10, build queues, and register queue runners during factory setup. `mode` only accepts `train` or `test`. |

## Shared default optimizer net

`util.get_config` uses a shared default optimizer net for MNIST/CIFAR problems and as the base template for saved-net paths:

```python
{
  "net": "CoordinateWiseDeepLSTM",
  "net_options": {
    "layers": (20, 20),
    "preprocess_name": "LogAndSign",
    "preprocess_options": {"k": 5},
    "scale": 0.01,
  },
  "net_path": None if path is None else os.path.join(path, "<name>.l2l"),
}
```

## `util.get_config` mappings

### `simple`

- Problem factory: `problems.simple()`
- Net config:

```python
{
  "cw": {
    "net": "CoordinateWiseDeepLSTM",
    "net_options": {"layers": (), "initializer": "zeros"},
    "net_path": None if path is None else os.path.join(path, "cw.l2l"),
  }
}
```

- Net assignments: `None`
- Path effect: only sets `cw.l2l` when a path is supplied.

### `simple-multi`

- Problem factory: `problems.simple_multi_optimizer()`
- Net config:

```python
{
  "cw": {
    "net": "CoordinateWiseDeepLSTM",
    "net_options": {"layers": (), "initializer": "zeros"},
    "net_path": None if path is None else os.path.join(path, "cw.l2l"),
  },
  "adam": {
    "net": "Adam",
    "net_options": {"learning_rate": 0.1},
  },
}
```

- Net assignments: `[("cw", ["x_0"]), ("adam", ["x_1"])]`
- Path effect: only `cw` gets a saved-net path.

### `quadratic`

- Problem factory: `problems.quadratic(batch_size=128, num_dims=10)`
- Net config:

```python
{
  "cw": {
    "net": "CoordinateWiseDeepLSTM",
    "net_options": {"layers": (20, 20)},
    "net_path": None if path is None else os.path.join(path, "cw.l2l"),
  }
}
```

- Net assignments: `None`
- Path effect: only sets `cw.l2l` when a path is supplied.

### `mnist`

- Problem factory: `problems.mnist(layers=(20,), mode="train" if path is None else "test")`
- Net config: `get_default_net_config("cw", path)`
- Net assignments: `None`
- Path effect: a non-`None` path switches the data mode to `test` and sets `cw.l2l`.

### `cifar`

- Problem factory: `problems.cifar10("cifar10", conv_channels=(16, 16, 16), linear_layers=(32,), mode="train" if path is None else "test")`
- Net config: `get_default_net_config("cw", path)`
- Net assignments: `None`
- Path effect: a non-`None` path switches the data mode to `test` and sets `cw.l2l`.

### `cifar-multi`

- Problem factory: `problems.cifar10("cifar10", conv_channels=(16, 16, 16), linear_layers=(32,), mode="train" if path is None else "test")`
- Net config:

```python
{
  "conv": get_default_net_config("conv", path),
  "fc": get_default_net_config("fc", path),
}
```

- Net assignments:

```python
conv_vars = [
  "conv_net_2d/conv_2d_0/w",
  "conv_net_2d/conv_2d_1/w",
  "conv_net_2d/conv_2d_2/w",
]
fc_vars = [
  "conv_net_2d/conv_2d_0/b",
  "conv_net_2d/conv_2d_1/b",
  "conv_net_2d/conv_2d_2/b",
  "conv_net_2d/batch_norm_0/beta",
  "conv_net_2d/batch_norm_1/beta",
  "conv_net_2d/batch_norm_2/beta",
  "mlp/linear_0/w",
  "mlp/linear_1/w",
  "mlp/linear_0/b",
  "mlp/linear_1/b",
  "mlp/batch_norm/beta",
]
[("conv", conv_vars), ("fc", fc_vars)]
```

- Path effect: a non-`None` path switches the data mode to `test` and sets both `conv.l2l` and `fc.l2l`.

## Notes on naming

- `simple-multi` in the README corresponds to the source factory `simple_multi_optimizer`.
- `cifar` and `cifar-multi` in `util.get_config` both use the source factory `problems.cifar10`.
- `ensemble` is a factory helper but not a `util.get_config` key.
