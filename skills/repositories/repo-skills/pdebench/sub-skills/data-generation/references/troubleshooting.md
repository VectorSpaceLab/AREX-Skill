# Data-generation troubleshooting and boundaries

## Missing optional dependencies

- **Clawpack:** the source-evidence module
  `pdebench.data_gen.src.sim_radial_dam_break` imports `clawpack.pyclaw` and
  `clawpack.riemann`. A missing import blocks radial dam-break execution. Do
  not install it or switch solvers implicitly; stop at config rendering or use
  a different family whose requirements are present.
- **phiflow/`phi`:** the incompressible Navier–Stokes source-evidence modules
  import `phi.field`, `phi.flow`, and `phi.math` through
  `pdebench.data_gen.src.data_io`. Missing phiflow blocks the route even if
  NumPy and JAX are available. `backend`, `device`, and `jit` values must match
  the installed phiflow/JAX backend.
- **JAX:** all NLE scripts import JAX and `jax.numpy`. The inspected baseline is
  CPU JAX 0.4.38; CUDA wheels, CUDA runtime, and GPU visibility are separate
  prerequisites. A CPU pass is not evidence of GPU behavior.
- **Other imports:** classical wrappers also import Hydra, OmegaConf, h5py,
  dotenv, SciPy, and project modules before entering `main`. Read the traceback
  and classify the missing package before changing the environment.

Do not turn an optional dependency failure into a claim that the model or
physics is incorrect. Record `missing optional dependency` and keep the route
blocked until the user approves environment preparation.

## Hydra working directory and config resolution

Hydra may change the process working directory to its run directory. The
classical configs use `${hydra:runtime.cwd}` or environment-based run roots;
the source-evidence NLE programs set `hydra.run.dir: .` and use
`hydra.utils.get_original_cwd()`. Consequently, for package-safe classical
commands:

1. invoke the installed module rather than a script path;
2. render with `--cfg job --resolve` before execution;
3. use an explicit `save`, `WORKING_DIR`, or `ARTEFACT_DIR`; and
4. verify the resolved path rather than trusting log-directory names.

The NLE and incompressible-NS runners are not currently self-contained
installed-package entry points. If Hydra cannot find a config group in a
separately approved adapter, check whether it expects the `args` or `multi`
config group; a plain file value is not interchangeable with group selection.
Use the bounded package-safe fixtures in the workflow reference instead of
repairing native import layout at runtime.

Safe package examples are:

```bash
python -m pdebench.data_gen.gen_diff_react --cfg job --resolve mode=debug
python -m pdebench.data_gen.gen_diff_sorp --cfg job --resolve mode=debug
```

Do not use an absolute private checkout path in a saved config or runtime
instruction. Keep output roots user-selected and explicit.

## Invalid overrides

Hydra distinguishes among:

- `key=value`: override an existing key;
- `+key=value`: add a key or select a config group according to the app's
  config structure; and
- `++key=value`: override or add a key, useful after selecting a group when the
  selected config already defines the nested field.

The source-evidence NLE programs select config groups with `+multi=...` or
`+args=...`, then access values as `cfg.multi.*` or `cfg.args.*`. A common
adapter failure is to write `nx=32` instead of `++multi.nx=32`, or to use
`args` for a multi-solution program. Render the selected configuration and
copy its exact nesting; do not copy a native config path into the runtime skill.

Other common causes:

- YAML values such as `1.e0` or booleans are quoted incorrectly in a shell;
  quote overrides when punctuation is involved.
- `save` is concatenated with filenames by source code; retain a trailing `/`
  where the config examples do.
- `numbers` is not divisible by `jax.device_count()` for a pmap/vmap route.
  On a single CPU device, one is the safest first value.
- CFD `dim`/`nx`/`ny`/`nz` combinations do not match the selected initializer.
- Merge `type` is case-sensitive (`ReacDiff` is not `reacdiff`) and `bd` has a
  narrower accepted set than some solver boundary modes.

## Memory and time blowups

The principal cost multipliers are batch count, number of saved times, cell
count, spatial dimension, and JAX compilation. Diffusive CFL limits shrink
with the square of cell width; Burgers and reaction-diffusion source code
compute diffusion-based limits. Compressible CFD computes advective and
viscous limits and stores multiple fields. Three-dimensional arrays multiply
memory by `nx * ny * nz` before compilation overhead.

Use this order when reducing a trial:

1. set `numbers=1`/`nbatch=1`;
2. use a 1D or very small grid (`nx=16` or `32`, and singleton `ny`/`nz` where
   the family permits it);
3. use a very short `fin_time`/`T_end` and only two or three saved frames;
4. set `if_show=0`, disable images/GIF/profiling, and use CPU; and
5. estimate output bytes before starting.

Do not claim a timeout made a simulation safe. Stop before swap/OOM, preserve
logs, and report the resolved dimensions and time controls. A tiny fixture that
finishes is not evidence that a production grid will fit.

## Output collisions and partial files

Classical writers append HDF5 datasets under seed names and NLE scripts write
parameterized `.npy` names. Reusing a path can cause:

- HDF5 `name already exists` errors;
- mixed configs under one seed file;
- merge globs to pick old and new parameter sets together; or
- a failed JAX process to leave coordinates without a complete solution.

Use a fresh directory per config/seed/backend. Before a run, list the target
and require it to be empty or explicitly approved. After interruption, treat
all files as partial until shape, finite values, and coordinate lengths are
checked. Do not delete or merge partial output automatically.

The classical wrappers also open shared HDF5 files from multiprocessing workers.
A lock/retry in the source is not a guarantee against collisions from two
separate launcher processes; never launch two wrappers against one output file.

## Backend, device, and reproducibility

The recorded verification baseline uses CPU JAX. The current review shell did
not have JAX installed, so this is not a live-environment verification claim.
`CUDA_VISIBLE_DEVICES` in the source-evidence NLE shell recipes is an example
of the authors' multi-GPU setup, not a device selection requirement. Do not
copy GPU IDs blindly. Check:

```bash
python - <<'PY'
import jax
print(jax.__version__)
print(jax.devices())
print("local devices:", jax.local_device_count())
PY
```

For a CPU route, omit `CUDA_VISIBLE_DEVICES` and use one sample. If a script
uses `pmap`, set `numbers` divisible by the visible device count. JIT compilation
can make the first call much slower and can reserve substantial memory. Keep
`init_key`/`seed`, package versions, and backend in the reproducibility record.

The classical NS config defaults to `device: GPU`, `backend: jax`, and `jit:
true`; those values should be changed only after confirming the phiflow backend
supports the requested device. `save_h5=false` and disabled visualization are
useful for inspection, but do not turn a missing solver dependency into a
successful run.

## Merge failures

`Data_Merge.py` discovers files with broad glob patterns and infers parameters
from filename token positions. Before calling it:

- use one homogeneous `savedir`;
- confirm the `type`, `dim`, `bd`, `nbatch`, and generated filename family;
- make a copy or immutable snapshot of raw `.npy` files; and
- inspect the source version for known defects.

The current source evidence includes apparent defects such as calling `.sort()`
on `Path.glob(...)` results and misspelling `create_dataset` as `create_dataet`
in several HDF5 writes. If those errors occur, report the merge as blocked
rather than silently patching the runtime skill or claiming an HDF5 was
produced. A merge fix requires a separate approved change and a focused fixture.

## Upload and credential boundary

The classical wrappers and NS helper can call a Dataverse uploader when
`upload=true`; the NLE merge itself is local. Upload uses environment-provided
URL, token, and persistent dataset ID and invokes a network command. It is
never part of help checks, tiny fixtures, schema verification, or default
production. Keep `upload=false`, redact tokens from logs, and route any request
to upload through explicit credential/network approval. Dataset retrieval and
visualization are separate routes.

## What to report when blocked

Return the family, script, config group/file, resolved overrides, Python/JAX/
Hydra versions, device list, output target, and the first actionable traceback.
Classify the result as one of:

- parser/config inspection passed;
- tiny in-memory fixture passed;
- optional dependency missing;
- backend/device unsupported;
- resource bound exceeded;
- output collision or partial output; or
- merge/upload explicitly blocked.

Do not collapse these categories into a generic "generation failed" message.
