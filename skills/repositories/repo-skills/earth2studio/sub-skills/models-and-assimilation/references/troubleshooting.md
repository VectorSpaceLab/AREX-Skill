# Model and assimilation troubleshooting

## A CUDA-only request is running on a CPU host

**Symptoms:** `torch.cuda.is_available()` is false; a GPU-only extra cannot
install a usable wheel; model construction or output conversion fails with a
CUDA/CuPy error.

**Recovery:** classify the request as blocked rather than silently changing the
scientific configuration. Inspect the selected class and extra first. For a
CPU smoke check, use the offline fixture or a model/diagnostic whose declared
implementation supports CPU, keep the device as `cpu`, and do not call a
CUDA-only loader. If the actual task requires the CUDA checkpoint, stop and
report the missing GPU, CUDA runtime, or compatible wheel. Installing a CUDA
package on CPU does not make the model CPU-capable.

For CUDA DA models, the output contract may require a same-device CuPy array.
`CorrDiffCosmoEra5SDA` explicitly rejects CUDA execution without CuPy; use the
`da-cosmo` extra on a compatible CUDA environment or run the model on CPU when
that class supports it.

## Optional dependency error at construction

**Symptoms:** an `OptionalDependencyError` identifies a group such as
`stormcast`, `corrdiff`, `cosmo`, `da-healda`, or `da-interp`.

**Recovery:** install only that declared group using the project environment,
for example:

```bash
uv sync --extra corrdiff
uv sync --extra da-healda
```

Re-run a lightweight import/coordinate probe before loading weights. If the
error names a compiled extension, verify its PyTorch/CUDA compatibility rather
than retrying the same install. Keep the original extra name in the report.

## Extras conflict or resolver failure

**Symptoms:** `uv` cannot resolve a combination of model extras, or a compiled
package has incompatible Torch constraints.

**Recovery:** create a separate environment for the selected model family.
Do not combine alternative AIFS extras (`aifs`, `aifs2`, `aifsens`, and
`aifs2ens`) in one environment. The project also declares conflicts involving
`ace2`, `atlas`, `fcn3`, `perturbation`, and `sfno`; respect the resolver's
reported conflict. For broad development coverage, use separate targeted
extras rather than the aggregate `all` group. Record the exact Python and Torch
versions used.

## ONNX Runtime cannot bind CUDA input

**Symptoms:** FengWu, FuXi, or Pangu reports a provider binding error or cannot
load `libonnxruntime_providers_cuda.so`.

**Recovery:** verify the ONNX Runtime GPU build, CUDA libraries, and Torch device
match the package's supported installation. A CPU host should not select these
GPU configurations merely because the Python class imports. Reinstall the
compatible ONNX Runtime build following the environment's package policy, then
probe `torch.cuda.is_available()` and provider availability before a checkpoint
load.

## Flash Attention, NATTEN, or torch-harmonics build failure

**Symptoms:** a long compile, missing `Python.h`/CMake, an undefined Torch CUDA
symbol, or a wheel unavailable for the current Python/CUDA version.

**Recovery:** use a supported wheel or a build image with the required compiler
and Python development headers. Match the extension to the installed Torch;
clear stale build caches only when the environment owner permits it. For a
CPU-only task, select a CPU-capable model instead of forcing a CUDA extension.
Do not claim success from an import that bypasses the guarded execution path.

## Coordinate handshake or shape mismatch

**Symptoms:** `ValueError`/handshake errors mention variable order, dimension
rank, spatial size, lead time, or a history window.

**Recovery:** print `model.input_coords()` and
`model.output_coords(model.input_coords())`; compare every key, size, allowed
value, and coordinate ordering. For an existing tensor, use the package's
coordinate mapping/handshake helpers rather than reshaping blindly. Check
whether the model needs a batch, time-history, or lead-time dimension. For
DLESyM, select valid atmosphere/ocean outputs separately. For StormScope,
construct the required history and conditioning stream before trying a coupled
call.

## Observation schema or metadata failure

**Symptoms:** `DataFrame missing required fields`, unknown variable/platform,
invalid sensor index, or a missing `request_time` error.

**Recovery:** obtain the exact `FrameSchema` from `model.input_coords()`. Add
only the fields the selected model requires, with the expected names and
physical units. Preserve DataFrame `.attrs` and set `request_time` when the
class requires it. For HealDA, pass at least one of conventional or satellite
frames and include all fields for that stream. For CorrDiff COSMO SDA, select
only identity-transform, unit-scale output channels and make the
`sda_std_obs` mapping exact. For time mismatch, widen the explicit
`time_tolerance` only when scientifically justified; an empty filtered batch
may be a valid no-observation case.

## Generator yielded the wrong thing

**Symptoms:** `send()` raises a type error, the first result is unexpectedly
`None`, or a generator appears to skip a forecast step.

**Recovery:** follow the concrete priming table in
[assimilation](assimilation.md). `InterpEquirectangular` and HealDA are primed
with `send(None)`; StormCastSDA and CorrDiff COSMO SDA are primed with
`next(generator)`. Send a single observation frame to Interp/StormCast/CorrDiff
SDA, but send a `(conv_df, sat_df)` pair to HealDA. Do not treat CorrDiff COSMO
SDA's independent analyses as a stateful forecast.

## Observations have no visible effect

**Symptoms:** analysis resembles the free run, or a test reports no increment.

**Recovery:** check time tolerance, variable names, finite values, geographic
coverage, and whether points fall inside the model domain. Some models snap
multiple observations to one cell and average them; sparse/out-of-domain points
may be discarded. Compare a prior and observation-guided result with identical
background input and a fixed seed before drawing a quality conclusion. For
DPS-based models, `sda_std_obs` and `sda_gamma` control guidance strength; do
not tune them without recording the units and baseline.

## Package access, NGC, or cache failure

**Symptoms:** timeout, unauthorized/not-found asset, or a model package appears
to load but a required file is absent.

**Recovery:** distinguish package construction from asset access. Verify the
root URI shape and exact checkpoint file expected by the class. For NGC, remove
stale credentials only under the environment owner's policy; public access can
be affected by an invalid NGC configuration. Increase
`EARTH2STUDIO_PACKAGE_TIMEOUT` only for a justified slow connection. Check the
configured cache has space and that a partial cache is not being mistaken for a
complete model. Never put API keys into scripts or skill files.
