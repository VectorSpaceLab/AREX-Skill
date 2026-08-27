# Ensemble troubleshooting

Use the smallest possible model/data fixture to isolate a problem. First print
or inspect `model.input_coords()`, `model.output_coords(...)`, the perturbation
input `coords`, and the IO coordinate arrays. Most failures are coordinate or
resource mismatches rather than ensemble arithmetic.

## Configuration and batch failures

### `ZeroDivisionError`, no batches, or a surprising batch count

`run.ensemble` treats `None` as `nensemble` and clamps a supplied batch size to
`nensemble`, but it expects a positive integer. Reject `batch_size <= 0` before
the run. A batch size larger than `nensemble` is harmless after clamping, but
usually indicates a configuration typo. Check it offline:

```bash
python scripts/check_ensemble_config.py \
  --nensemble 128 --batch-size 4 --backend zarr --state-elements 1048576
```

The helper reports an estimate for repeated initial-state memory at the chosen
batch size. It is a planning estimate, not a model activation or total GPU
memory measurement.

### CUDA out-of-memory during the first batch

The workflow repeats `x0` to the current batch and the prognostic iterator
holds model activations/state. Lower `batch_size` first; it changes concurrency
without changing member count. Then reduce `output_coords` only if output
transfer/storage is the bottleneck, and select a device explicitly. For HENS
or bred-vector perturbations, include warmup/model-forward work in the memory
budget and try `batch_size=1`.

Do not solve an out-of-memory error by silently reducing `nensemble`; that
changes the statistical experiment. If CPU execution is only a smoke test,
run one or two members on CPU, then restore the intended GPU and member count.

### All members are identical

This is expected with `Zero()` unless the model itself has a stochastic hook.
For `Gaussian`, check that amplitude is nonzero, the perturbation is actually
passed to `ensemble`, and the model input was not overwritten after the call.
For a custom wrapper, compare `candidate - x` at lead time zero and verify that
its selected-variable mask is nonempty. A deterministic model may make later
fields similar if perturbations are numerically too small; inspect initial
spread in input units before diagnosing the model.

## Coordinate and perturbation failures

### `KeyError`/`ValueError` for `lat`, `lon`, or aspect ratio

`Brown`, `SphericalGaussian`, and `CorrelatedSphericalGaussian` require the
latitude and longitude dimensions in the final two positions. The spherical
methods generate on an equirectangular grid with latitude/longitude sizes
`N:2N` or `N+1:2N`. Use `map_coords` to place the model grid first, or choose a
perturbation without this grid restriction. Do not pad or transpose the tensor
without updating `coords`.

### `RuntimeError` or unexpected values from a perturbation amplitude

`noise_amplitude` is not automatically normalized. A Tensor amplitude must be
broadcastable to `x`; a common per-variable layout has shape compatible with
`[variable, 1, 1]` after the variable axis is located. Confirm dtype and device
by moving the amplitude to `x.device` inside custom code. Confirm physical vs
normalized units with the model's preprocessing contract. Never use one scalar
amplitude for mixed-unit variables without an intentional reason.

### `LaggedEnsemble` says the number of lags does not match members

The built-in lagged method compares `len(coords["ensemble"])` with
`len(lags)` on every perturbation call. Because `run.ensemble` calls it per
batch, set `batch_size=nensemble=len(lags)` or use a batch-aware custom
perturbation. It also requires axes `ensemble`, `time`, `lead_time` at
positions 0, 1, and 2. Ensure the data source can fetch every `time + lag`.
Negative lags are for past initial conditions; positive lags are not normal
forecast perturbations.

### Bred-vector or HENS method rejects dimensions or gives unstable spread

`BredVector` performs extra model calls and warns when multiple input lead
 times are supplied. Check its callable model and seeding perturbation before
checking the outer workflow. `HemisphericCentredBredVector` requires a single
time coordinate at its call, 5 or 6 tensor dimensions, a latitude/longitude
grid, and source data for warmup times. Its centered output is generated in
pairs; odd batch sizes use an internal residual between calls. Reinitialize
stateful perturbations between unrelated runs and validate nonnegative fields
that the method clips.

## Temporal interpolation and data fetch

### Initial-data interpolation fails or output cadence is wrong

If the prognostic object exposes `interp_method`, `run.ensemble` passes the
model input coordinates and that method to `fetch_data`; otherwise it uses
nearest behavior. An interpolation wrapper still needs a configured base model
and all required variables/features. Inspect the wrapper's `input_coords()` and
`output_coords()` rather than assuming a six-hour cadence. `nsteps + 1` is
counted in the wrapper's output lead-time units.

If source and model grids differ, verify the source contains all requested
variables and that the interpolation target is the model input coordinate
system. Do not pre-interpolate the tensor and then ask the workflow to
interpolate it again unless the model contract explicitly requires that.

## IO incompatibilities

### Async Zarr rejects a member batch as a nonparallel coordinate

This is the important large-ensemble incompatibility. Built-in
`run.ensemble` initializes the full `ensemble` coordinate but writes a subset
of members for each batch. With `AsyncZarrBackend`, configure complete
`parallel_coords` containing at least `ensemble` and `lead_time` (and the full
`time` set when it is indexed by the workflow). If `ensemble` is omitted, the
backend requires each write to contain the complete ensemble coordinate and
rejects a partial batch. If `lead_time` is omitted, it rejects the one-step
rollout slices.

Run the safe checker before launching a model:

```bash
python scripts/check_ensemble_config.py \
  --nensemble 2048 --batch-size 8 --backend async-zarr \
  --parallel-coords ensemble,time,lead_time
```

For non-blocking Async Zarr, call `io.close()` after the workflow and surface
any delayed write exception. Do not reuse an existing store when the backend
is configured for a new schema. A shard size on a parallel dimension must be a
positive multiple of chunk size 1; sharding also buffers host memory.

### Store grows too slowly or creates too many objects

Use member/time/lead-time chunks appropriate to the access pattern and measure
rather than assuming a universal optimum. Async Zarr can hide write latency,
but non-blocking writes still need a final `close()`. Sharding reduces object
count at the cost of host memory and rewrite work for partial shards. In a
multi-process job, a shard must belong entirely to one process; otherwise a
later write can silently replace another process's data. If the output is
small, a regular Zarr or in-memory backend is simpler.

### Output shape or missing member errors

The workflow writes `nsteps + 1` lead-time slices and prefixes the output with
`ensemble` and `time`. Check the coordinate arrays, not only positional shape,
especially when `output_coords` selects a subset. Confirm every requested
variable is an initialized array and that each member coordinate is unique.
If a checkpoint restart is used, inspect `completed_ensembles` metadata and
ensure the IO store is compatible with resumed writes.

## Checkpoint and reproducibility failures

### A restart repeats a batch or does not match the first run

A checkpoint level below 2 is not sufficient for a guaranteed mid-rollout
component restart; the workflow warns and reruns the current batch from lead
time zero. Model and perturbation state is opt-in. `Gaussian` stores its RNG
state when checkpointing is enabled, but custom perturbations and internal
HENS residuals need their own checkpoint state. Construct restart-sensitive
components inside the selected checkpoint context and use a fresh tiny test to
compare the first post-restart perturbation.

### `completed_ensembles` is present but output is incomplete

Checkpoint metadata only records members after their final successful write.
Inspect the latest checkpoint session and the output store together. Do not
mark a run complete from metadata alone if the IO backend has asynchronous
writes; flush/close the backend first. If the store contains partial data from
a failed non-atomic setup, use a fresh output store rather than overwriting
member slices blindly.

## Downstream diagnostics and statistics

### A statistic says a dimension is missing or coordinates are incompatible

Use the ordered coordinate dictionary to find the `ensemble` axis; do not
assume it is axis zero after custom transformations. A statistic such as
`mean(["ensemble"])` returns coordinates with that dimension removed. For
`crps`, `energy_score`, `brier_score`, or `rank_histogram`, the observation
must not include `ensemble` and must match all remaining coordinate values.
Map both tensors to a shared coordinate system before calling the metric.

A full-field `energy_score` can allocate pairwise member distances over all
selected dimensions. Reduce to a bounded spatial/variable set or use a cheaper
summary when memory is limited. A standard deviation with one member has no
meaningful sample spread; use at least two members for uncertainty summaries.

### Diagnostic state leaks between ensemble sequences

A diagnostic model may be stateful (for example, a tracker with a path buffer).
Reset it between independent initial times or construct a fresh instance. Keep
its output coordinate system and filter any NaN padding according to that
model's documented output contract. Do not call `run.diagnostic` expecting it
to iterate over an existing ensemble store; use a member-aware custom loop.

## Optional dependencies and environment

An import failure from a perturbation or statistic generally means its targeted
extra is missing or incompatible. Install the package's named extra in the
active project environment, then re-run a small import/shape check. Spherical
perturbations need the `perturbation` extra; CRPS, energy score, rank histogram,
and some other metrics may need the `statistics` extra. Model extras are
independent. Avoid mixing incompatible dependency groups without checking the
project's supported Python range (`>=3.11,<3.15`) and the selected backend.
