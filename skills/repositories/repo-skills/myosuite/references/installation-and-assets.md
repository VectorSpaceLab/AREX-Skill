# Installation and model assets

## Base installation

MyoSuite 2.12.x declares Python `>=3.10,<3.14` and base dependencies including
Gymnasium `<1.3`, MuJoCo `>=3.6,<3.7`, NumPy, h5py, imageio/ffmpeg, Click,
Pillow, termcolor, flatten-dict, pink-noise-rl, packaging, and GitPython.
Install the distribution into an isolated environment:

```bash
python -m pip install -U myosuite
python -c "import myosuite, mujoco; print(myosuite.__version__, mujoco.__version__)"
```

For source installation, use the project's documented editable install and make
sure the model asset dependencies are present before creating an environment.
The package's console commands are `myoapi_init` and `myoapi_clean`; they manage
optional SimHive assets and should be treated as explicit operator actions, not
automatic skill steps.

## Optional variants

- `MyoSuite[mjx]` adds JAX/MJX/Brax/Flax/Optax and related helper dependencies
  for the optional accelerated route.
- `MyoSuite[mjx-cuda]` selects the CUDA JAX variant on supported non-Windows
  systems. Verify the actual JAX device and a minimal operation; package
  importability alone is not CUDA evidence.
- `MyoSuite[tutorials]` adds plotting, Mink, OSQP, Stable-Baselines3, and other
  tutorial/training dependencies. Install only when a selected tutorial or RL
  integration needs them.
- `MyoSuite[examples]` provides Mink examples. It is not required for the base
  environment route.
- `MyoSuite[docs]` is documentation-build tooling, not runtime support.

Keep optional variants in a compatible isolated environment. Do not install all
extras as a substitute for selecting a workflow.

## Model assets and source checkouts

MyoSuite's model-backed task XML files can include files from its model asset
repositories. A source checkout with uninitialized or incomplete asset
submodules may import successfully yet fail at `gym.make` with a MuJoCo
`Error opening file` XML exception. A release package with complete package data
or a correctly initialized source distribution is required for environment
creation.

Diagnose in this order:

1. Verify the distribution/import versions and that `myosuite` registration ran.
2. Verify the exact task ID with the registry, then attempt a tiny `gym.make`,
   `reset`, and `close` using `render none`.
3. If an XML include is missing, repair the explicitly documented asset setup or
   use a complete release package; do not change the task ID or silently fetch
   data from an unknown location.
4. Re-run the bundled environment smoke helper and record the package/backend
   result separately from the asset result.

Never put a local checkout path, environment prefix, or activation command into
scripts or public skill instructions.
