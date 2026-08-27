# Cross-cutting troubleshooting

## Install and import

- **No setup metadata / editable install failure:** this source tree does not
  declare a distribution. Use an isolated environment and make a separately
  supplied checkout importable only for the current command. Do not infer that
  a successful `import second` means the model path is usable.
- **Generated protobuf descriptor errors:** old `*_pb2.py` files can fail with
  “Descriptors cannot be created directly” under modern protobuf. Use a
  compatible protobuf 3.20-era runtime for historical inspection or regenerate
  the descriptors in a controlled migration; do not hide the error by setting a
  global compatibility variable in a published workflow.
- **`collections.Iterable` failure:** old `torchplus` imports a Python API that
  moved to `collections.abc`. This is an environment/source-age signal. Record
  the compatibility shim or use a maintained fork; do not silently patch a
  shared user environment.
- **Missing Fire/tensorboardX/scikit-image/NuScenes devkit:** install only the
  optional package needed by the selected route. The layout and NumPy geometry
  helpers do not need the detector stack.

## Backend and model failures

- **Missing `VoxelGeneratorV2`, `non_max_suppression`, or sparse symbols:** run
  the training sub-skill's `check_legacy_backend.py --require-detector`. Modern
  spconv 2.x is not a drop-in replacement for this source. Stop, obtain a
  proven legacy environment, or migrate to a maintained detector.
- **CUDA is available but the detector fails:** a Torch tensor smoke checks only
  the framework/driver path. It does not check Numba kernels, spconv ABI,
  sparse module behavior, or checkpoint compatibility. Preserve the first
  traceback and keep the detector gate blocked.
- **GPU out-of-memory:** first check `CUDA_VISIBLE_DEVICES` and other jobs,
  then lower the config's per-GPU batch/voxel limits only after preserving the
  original config. Do not use an occupied device as evidence of backend failure.
- **Apex/fp16 errors:** the source's `enable_mixed_precision` targets a
  historical Apex integration, not automatically modern `torch.amp`. Disable
  it while diagnosing and verify the exact sparse backend before rebuilding.

## Data and configuration

- **Missing info/database files:** run the bundled layout validator, confirm
  split/version/class names, then generate artifacts only in a backed-up or
  disposable dataset root. Check the expected filenames and relative-path
  policy before training.
- **Empty or mismatched stems:** image, calibration, lidar, and label stems must
  agree for the selected split. A present directory is not proof that the
  writer can read it; inspect at least one file of each required type.
- **NuScenes velocity mismatch:** a `Velo` dataset class and nine-dimensional
  anchors/custom values must be paired with velocity-aware generated info and
  config. A base class and velocity fields must not be mixed.
- **Wrong class order/feature width:** keep config class order identical to
  model head order, dataset registry class, anchor settings, and evaluator
  mapping. Point feature width must agree with the dataset and model config.
- **Multi-GPU schedule drift:** batch size and worker count are per GPU in the
  historical source. If scaling a single-GPU schedule, divide `steps` and
  `steps_per_eval` once and record the effective update count.

## CLI/API and viewer failures

- **Fire rejects an option:** inspect the exact callable signature and current
  help output. The historical docs mention `--pickle_result`, but the current
  evaluation signature does not necessarily accept it.
- **Viewer says load/build/inference failed:** load the dataset first; the
  backend expects backend-host filesystem paths, an info pickle, and a matching
  dataset class. Build the network only after the legacy backend gate passes;
  otherwise the error is a compatibility block, not a browser bug.
- **CORS/URL errors:** keep frontend and backend origins explicit, use a URL
  with scheme and correct port, and check browser network logs. The historical
  backend has no authentication and should remain loopback/local unless the
  user supplies a secure deployment boundary.
- **Qt viewer import/display failures:** the desktop viewer is deprecated and
  requires a separate Qt/OpenGL/display stack. Do not install GUI packages as
  a prerequisite for data/geometry tasks; use the web route or a maintained
  visualization tool.

## Stop conditions

Stop rather than guessing when a required backend, dataset, checkpoint,
credential, or large external artifact is unavailable; when a source/config
schema is ambiguous; or when a compatibility workaround would modify user code
or data irreversibly. Report the symptom, first failing command, exact missing
surface, and the next safe option.
