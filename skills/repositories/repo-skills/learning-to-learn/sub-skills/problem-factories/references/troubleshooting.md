# Troubleshooting

## Invalid problem names

`util.get_config(problem_name, path=None)` only accepts the README problem keys:

- `simple`
- `simple-multi`
- `quadratic`
- `mnist`
- `cifar`
- `cifar-multi`

Any other name raises a `ValueError`. If you are thinking in source-factory names, remember:

- `simple-multi` corresponds to `problems.simple_multi_optimizer`.
- `cifar` and `cifar-multi` both use `problems.cifar10`.

## MNIST/CIFAR data downloads and queue side effects

The data-backed factories can do real work when they are called:

- `mnist` loads the MNIST dataset.
- `cifar10` may create the target directory, download a tarball, extract it, and build queue runners.

If you only want to inspect a configuration, use `scripts/inspect_problem_config.py` instead of calling the factory directly.

If you do want to run the factory, make sure the `path` argument is writable and points to a dataset cache root, not to a saved-optimizer directory.

## Custom `make_loss` Python side effects

If your custom loss builder performs downloads, queue construction, or file I/O inside the callable passed to `meta_minimize`, repeated unrolls can repeat those side effects.

Fix:

- move the side effect to the outer factory,
- keep the returned `build()` callable graph-only,
- and return a scalar loss tensor from that callable.

## Variable names for `net_assignments`

`net_assignments` matches by exact TensorFlow variable name without the `:0` suffix.

Examples:

- `x_0`
- `x_1`
- `conv_net_2d/conv_2d_0/w`
- `mlp/linear_1/b`

If a name is wrong, missing, or uses the wrong scope prefix, the optimizer assignment step will fail when it builds the net subsets.

## Activation and mode errors

- `problems.mnist(..., activation=...)` only accepts `sigmoid` or `relu`.
- `problems.cifar10(..., mode=...)` only accepts `train` or `test`.
- `problems.ensemble(..., weights=...)` requires `len(weights) == len(problems)` when weights are provided.

## Saved-net path issues

When `path` is supplied to `util.get_config`, the helper expects saved `.l2l` files under that directory.

Typical file names are:

- `cw.l2l` for `simple`, `simple-multi`, `quadratic`, `mnist`, and `cifar`
- `conv.l2l` and `fc.l2l` for `cifar-multi`

If loading fails, check that the directory exists and contains the expected filenames.

## Quick recovery checklist

1. Confirm the public problem name, not the source-factory alias.
2. Check whether the problem is data-backed.
3. Verify the exact variable names.
4. Check `activation`, `mode`, and `weights` arguments.
5. Re-run the bundled inspection script for a safe summary.
