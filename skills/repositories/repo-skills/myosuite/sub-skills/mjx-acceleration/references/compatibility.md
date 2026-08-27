# MJX compatibility and backend policy

## Dependency tiers

The base distribution and the optional acceleration tiers are intentionally
separate:

| Route | Install declaration | What it enables | What it does not prove |
|---|---|---|---|
| Base CPU | ordinary MyoSuite dependencies | MuJoCo, Gymnasium environments, reset/step, model-backed CPU simulation | JAX, MJX, CUDA, or GPU throughput |
| Optional MJX | `MyoSuite[mjx]` | JAX, `jaxlib`, MuJoCo MJX, MuJoCo Playground/Brax support, JAX helpers, and the MJX environment factory | CUDA execution or a speedup on the current machine |
| Optional CUDA | `MyoSuite[mjx-cuda]` | The MJX tier plus the JAX CUDA extra | A working driver, visible GPU, compatible wheel, or a speedup until probed |

The inspected project metadata declares Python `>=3.10,<3.14`, MuJoCo
`>=3.6,<3.7`, JAX/JAXLIB `>=0.4.20` for the MJX tier, and a CUDA JAX extra
for `mjx-cuda`. Resolve the exact lockfile/package versions for the target
environment rather than copying versions from an unrelated installation.
The optional extras are marked non-Windows in the project metadata; treat a
Windows installation as a compatibility check, not an assumed supported route.

Use an explicit package-manager command only after permission is granted:

```bash
python -m pip install "MyoSuite[mjx]"
# For a CUDA-capable target, choose this instead:
python -m pip install "MyoSuite[mjx-cuda]"
```

These commands install packages but do not create assets or run training. Do
not combine them with an unbounded upgrade, a benchmark, or a data download.

## Device decision tree

1. Run `python scripts/mjx_probe.py` with no required flags.
2. If `jax` or `mujoco.mjx` cannot import, report `optional-unverified` and
   choose whether to install the `mjx` extra.
3. If imports work, inspect the reported `jax.devices()` and platform.
4. If the requested target is CPU, use `--platform cpu` for deterministic
   semantic checks; this proves only CPU JAX execution.
5. If the requested target is CUDA, use `--require-cuda` and an environment
   lifecycle probe. A list containing only CPU devices is a hard backend block.
6. If CUDA is expected but absent, compare the JAX/JAXLIB wheel, driver/runtime,
   and device visibility. Do not silently reroute to CPU and call it a speedup.

A successful `import jax` is not a successful CUDA check. A host GPU visible to
system tools is not a successful JAX CUDA check. The required observation is a
JAX device with a GPU/CUDA platform, followed by a model operation on that
platform.

Useful non-mutating diagnostics are:

```bash
python scripts/mjx_probe.py --json
python scripts/mjx_probe.py --platform cpu --require-mjx --json
python scripts/mjx_probe.py --require-cuda --env-name MjxElbowPoseRandom-v0 --steps 1 --json
```

The script does not install, initialize submodules, download assets, render a
window, or time a workload.

## MJX implementation limits

The environment factory defaults to a JAX implementation and builds an MJX
model from a MuJoCo model specification. The base class uses a control period
of `0.02`, simulation period of `0.002`, action normalization by default, and a
large vectorization capacity in its default configuration. These are config
values, not promises that every model can run at every batch size. Override
small values for a smoke test and increase them only for an actual experiment.

For the JAX implementation, the inspected preprocessing disables contacts for
cylinder geoms and clears nonzero margins for mesh/heightfield geoms before
compilation. This is an implementation accommodation, not semantic equivalence
to every CPU MuJoCo contact model. If contact-rich behavior matters, compare
outputs and document the implementation choice; do not infer exact parity from
matching shapes.

The optional `impl="warp"` route is distinct from JAX. It still requires the
optional acceleration stack and must be probed separately. This sub-skill does
not make a benchmark claim for Warp or MJX.

## Environment and asset requirements

MJX environment construction still needs the packaged MuJoCo XML/model assets.
An import-only probe can succeed while a model-backed lifecycle fails because
assets are missing or incomplete. Keep asset setup separate from the probe and
use the package's supported installation/setup procedure with explicit user
approval. Never embed checkout paths, asset initialization commands, or mutable
setup in the runtime skill.

## Evidence status policy

Use these labels in reports:

- `verified-cpu-jax`: JAX/MJX imported and the requested operation ran on a
  reported CPU JAX device.
- `verified-cuda-mjx`: MJX environment operation ran while JAX reported a GPU/
  CUDA device; include the exact device/platform observation.
- `optional-unverified`: the extra was not installed, a dependency failed to
  import, or only source inspection was possible.
- `backend-blocked`: the requested CUDA route cannot run on the current host.
- `semantic-mismatch`: both paths ran but output or contact behavior differs
  beyond the documented tolerance.

Never convert `optional-unverified` or `backend-blocked` to a CPU success.
