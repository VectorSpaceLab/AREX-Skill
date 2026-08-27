# Foolbox Troubleshooting

## Installation and imports

- **`ModuleNotFoundError: foolbox`**: install with `python -m pip install
  foolbox` in the same interpreter that will run the experiment; verify with
  `python -c "import foolbox; print(foolbox.__version__)"`.
- **Pillow missing from `samples()`**: `samples()` reads bundled image files
  through Pillow. Install `pillow` or provide your own already-batched tensors.
- **Matplotlib missing from `plot.images()`**: install `matplotlib`; set a
  headless backend such as `MPLBACKEND=Agg` in CI.
- **TensorBoard import failure**: only attacks that request a TensorBoard log
  directory need `tensorboardX`. Keep `tensorboard=False` for a dependency-free
  run, or install `tensorboardX` explicitly.

## Model and data errors

- **`expected data_format to be 'channels_first' or 'channels_last'`**:
  correct the wrapper argument; do not use `NCHW`/`NHWC` strings.
- **`data_format could not be inferred`**: pass `data_format` to `samples()` or
  configure it on the model wrapper. A bare custom `Model` has no channel hint.
- **Preprocessing errors about `axis` or dimensions**: channel vectors must be
  1-D and `axis` must be negative. Use `axis=-3` for `(N,C,H,W)` or omit axis
  for scalar mean/std.
- **Bounds assertion during an attack**: every input value must be between
  `model.bounds.lower` and `model.bounds.upper`. Normalize inputs or call
  `transform_bounds()` before retrying.
- **Shape mismatch in criteria**: model logits must have one row per input and
  labels/targets must have shape `(N,)`. Check `fmodel(inputs).shape` before
  constructing a criterion.
- **Training-mode warning from PyTorchModel**: call `model.eval()` unless
  training-time stochastic behavior is intentional.

## Attack errors

- **`unsupported criterion`**: some gradient attacks only support untargeted
  `Misclassification`; choose a supported attack or use a targeted-capable
  attack with `TargetedMisclassification`.
- **`FixedEpsilonAttack subclasses do not yet support None in epsilons`**:
  provide numeric epsilon(s), or choose a minimization attack that supports
  `None`.
- **`unknown distance, please pass distance`**: flexible minimization attacks
  such as `InversionAttack` or `DatasetAttack` need `distance=fb.distances.l2`
  (or another supported distance) when a budget is requested.
- **Unexpected keyword argument**: inspect the concrete attack constructor or
  `run()` contract; Foolbox rejects unknown attack kwargs rather than silently
  ignoring them.
- **No adversarial starting point in BoundaryAttack**: supply a known
  adversarial `starting_points` tensor or choose an initialization attack that
  can find one. Network/model accuracy and labels must be checked first.
- **SpatialAttack rejects inputs**: it expects 4-D image batches and has a
  special call without an epsilon budget. It searches rotations/translations,
  not an Lp ball.
- **Random attack results vary**: seed the underlying framework where possible,
  report repeats, and use `attack.repeat(n)` or repeated sampling rather than
  treating one stochastic run as a guarantee.

## Optional frameworks and external state

Foolbox does not install PyTorch, TensorFlow, or JAX. Install the framework
before importing its wrapper; select a wheel compatible with the requested CPU,
CUDA, ROCm, or accelerator runtime. A successful base import does not verify a
framework gradient path. Pretrained examples and `zoo.get_model()` may download
large weights or clone remote code; stop and obtain approval before networked or
untrusted operations.
