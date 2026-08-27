# Ensemble workflows

These patterns assume `model`, `data_source`, and any optional model packages
are already constructed. They show the ensemble-specific parts only.

## 1. Baseline member batches

Use a disk-backed Zarr store for a normal medium ensemble and choose chunks that
make member/forecast-slice reads cheap:

```python
import numpy as np
from earth2studio.io import ZarrBackend
from earth2studio.perturbation import Gaussian
from earth2studio.run import ensemble

nsteps = 10
nensemble = 16
batch_size = 4
perturbation = Gaussian(noise_amplitude=0.05, seed=42)
io = ZarrBackend(
    "ensemble.zarr",
    chunks={"ensemble": 1, "time": 1, "lead_time": 1},
    backend_kwargs={"overwrite": True},
)
ensemble(
    ["2024-01-01"], nsteps, nensemble, model, data_source, io,
    perturbation, batch_size=batch_size, device=device,
)
```

The workflow repeats the initial tensor only to the current batch, so reducing
`batch_size` reduces the repeated-input and model activation footprint but
increases the number of serial batches. It does not reduce the output store
size. `batch_size=None` is equivalent to using all members in one batch.

A `Zero()` perturbation is useful for a control run, but every member will have
the same initial state. A deterministic model can still diverge later only if
it has its own stochastic/model perturbation hook; do not treat `Zero()` as an
uncertainty source.

## 2. Variable-specific or normalized perturbation

Noise amplitudes are applied in the model-input units. A model with temperature,
humidity, wind, and geopotential fields usually needs different amplitudes or a
normalization-aware wrapper. The wrapper must preserve the leading batch/member
axis and return the original coordinate mapping:

```python
import numpy as np
import torch
from earth2studio.perturbation import Perturbation, SphericalGaussian

class ApplyToVariables:
    def __init__(self, base: Perturbation, variables: str | list[str]):
        self.base = base
        self.variables = [variables] if isinstance(variables, str) else variables

    @torch.inference_mode()
    def __call__(self, x, coords):
        candidate, candidate_coords = self.base(x, coords)
        if list(candidate_coords) != list(coords):
            raise ValueError("perturbation changed coordinate axes")
        var_axis = list(coords).index("variable")
        selected = np.isin(coords["variable"], self.variables)
        if not selected.any():
            raise ValueError("none of the requested variables are present")
        result = x.clone()
        index = [slice(None)] * x.ndim
        index[var_axis] = selected
        result[tuple(index)] = candidate[tuple(index)]
        return result, coords

perturbation = ApplyToVariables(
    SphericalGaussian(noise_amplitude=1.0), "t2m"
)
```

If fields are stored normalized, either provide amplitudes in normalized units
or make the wrapper explicitly denormalize, perturb in physical units, and
renormalize before returning. Do not apply physical-unit amplitudes to a
normalized tensor by assumption. Validate with a zero/constant fixture: the
selected field should change at the initial slice and an unselected field
should remain equal.

`SphericalGaussian` and `CorrelatedSphericalGaussian` require `lat`/`lon` as
the final two coordinates and a supported equirectangular ratio. If the model
grid is not compatible, use `Gaussian`, `Brown` where its grid contract fits,
or a perturbation tailored to the model.

## 3. Lagged initial conditions

A lagged ensemble replaces each repeated initial condition by a fresh source
fetch. The lags are `numpy.timedelta64` values and their count must equal
`nensemble`:

```python
import numpy as np
from earth2studio.perturbation import LaggedEnsemble
from earth2studio.run import ensemble

lags = np.array([
    np.timedelta64(-12, "h"),
    np.timedelta64(-6, "h"),
    np.timedelta64(0, "h"),
])
perturbation = LaggedEnsemble(data_source, lags)
ensemble(
    ["2024-01-01"], 8, len(lags), model, data_source, io,
    perturbation, batch_size=len(lags),
)
```

`LaggedEnsemble` requires the incoming `ensemble`, `time`, and `lead_time`
axes at positions 0, 1, and 2. Since `run.ensemble` invokes a perturbation
per batch, a smaller `batch_size` gives the perturbation fewer members than the
full `lags` array and raises its length mismatch. Use one batch or implement a
batch-aware lagged wrapper. Negative lags use past analysis times. Positive
lags are explicitly unsuitable for ordinary forecasting, though they can be
useful in hindcast studies.

## 4. Temporal interpolation in an ensemble

Use a prognostic interpolation wrapper as the `prognostic` argument when the
application needs sub-step output. For example, an `InterpModAFNO` instance
must have its base prognostic model configured (`px_model`) and its model
extra installed. The workflow notices `interp_method` while fetching initial
data and maps the source to the interpolation model's input grid.

```python
from earth2studio.models.px import InterpModAFNO
from earth2studio.run import ensemble

interpolating_model = InterpModAFNO.load_model(
    interpolation_package,
    px_model=base_model,
)
ensemble(
    ["2024-01-01"],
    nsteps=24,                 # use the interpolating model's step contract
    nensemble=8,
    prognostic=interpolating_model,
    data=data_source,
    io=io,
    perturbation=Gaussian(0.05),
    batch_size=2,
)
```

Do not hard-code a six-hour lead-time interpretation after wrapping the model.
Inspect `interpolating_model.output_coords(interpolating_model.input_coords())`
and the returned IO coordinates. The interpolation wrapper still needs all
variables and grid features required by its own input contract; interpolation
is not a generic post-processing resize.

## 5. HENS-style and multi-checkpoint runs

A HENS-style perturbation is stateful in its construction: it uses the
prognostic model, a data source for warmup times, and a seeding perturbation.
A typical strategy is:

1. Load one compatible checkpoint/model at a time.
2. Build a per-variable noise amplitude, often with only selected fields
   nonzero, then construct `CorrelatedSphericalGaussian` and
   `HemisphericCentredBredVector`.
3. Run `run.ensemble` with a small `batch_size` into a distinct Zarr store.
4. Delete the model/perturbation and release accelerator memory before loading
   the next checkpoint.
5. Open the stores for downstream concatenation and verify the resulting member
   coordinate/index semantics before calculating mean or spread.

`HemisphericCentredBredVector` fetches warmup times based on
`integration_steps`, expects a single `time` coordinate at perturbation call,
and emits centered positive/negative states. It clips humidity, precipitation,
and related nonnegative fields identified by its variable names. It is not a
replacement for a generic Gaussian perturbation, and its data/model warmup
cost must be included in the budget. HENS checkpoint licenses and model extras
are separate prerequisites.

For a cyclone analysis, keep the ensemble member axis while mapping each
member's forecast fields to the tracker diagnostic input. Trackers maintain
path state; reset that state between independent sequences. A tracker may emit
`[batch, path, step, variable]`-like output with NaN padding, so filter missing
path points before comparing members. This skill does not choose a tracker or
implement a full tropical-cyclone workflow.

## 6. Async Zarr for sliced member writes

The built-in workflow calls `io.add_array` once and then writes partial member
and lead-time slices. `AsyncZarrBackend` can be used only when its parallel
coordinate contract matches those writes. Construct it with the complete sets
of values before the run, including `ensemble` and `lead_time`:

```python
import numpy as np
from earth2studio.io import AsyncZarrBackend
from earth2studio.run import ensemble

step = model.output_coords(model.input_coords())["lead_time"][0]
times = np.asarray([np.datetime64("2024-01-01")])
lead_times = np.asarray(
    [step * i for i in range(nsteps + 1)], dtype=step.dtype
)
io = AsyncZarrBackend(
    "ensemble-async.zarr",
    parallel_coords={
        "ensemble": np.arange(nensemble),
        "time": times,
        "lead_time": lead_times,
    },
    blocking=False,
)
ensemble(
    times, nsteps, nensemble, model, data_source, io,
    Gaussian(0.05), batch_size=batch_size,
)
io.close()
```

The exact dtype construction for `lead_times` may need to follow the model's
returned NumPy timedelta dtype. The important invariant is that every value
written by the workflow belongs to the complete parallel coordinate arrays.
Without `ensemble` in `parallel_coords`, the async backend treats a batch's
partial member coordinate as a nonparallel dimension and rejects the write.
Without `lead_time`, each rollout slice is likewise incompatible. The offline
checker catches this configuration before model execution.

For sharding, a shard size along a parallel coordinate must be a positive
multiple of its chunk size (parallel dimensions use chunk size 1). Sharding
reduces file count but buffers host memory. In multi-process jobs, do not let a
shard contain data owned by more than one process. Always close a non-blocking
backend and surface delayed write errors before declaring success.

## 7. Checkpointed member batches

```python
from earth2studio.utils.checkpoint import Checkpoint

checkpoint = Checkpoint("ensemble-run", flush_interval=1, level=2)
with checkpoint as session:
    ensemble(
        ["2024-01-01"], 12, 32, model, data_source, io,
        Gaussian(0.05, seed=7), batch_size=2,
        checkpoint=session,
    )
```

The workflow records completed member IDs after a complete final lead-time
write. On retry it starts at the first incomplete member. A component that does
not persist its own state can still force a batch restart from lead time zero,
and a perturbation with unpersisted RNG/internal residual state may not replay
identically. Verify the checkpoint level and component support in a tiny run.

## 8. Summaries, verification, and diagnostics

For a tensor loaded from a memory backend, keep its coordinate order alongside
it and reduce by name rather than by a hard-coded axis:

```python
from earth2studio.statistics import mean, std

mean_value, mean_coords = mean(["ensemble"])(forecast, forecast_coords)
spread_value, spread_coords = std(["ensemble"])(forecast, forecast_coords)
```

For a forecast `forecast` with coordinates containing `ensemble`, and an
observation `truth` with the same non-member coordinates:

```python
from earth2studio.statistics import crps, energy_score

score, score_coords = crps(
    ensemble_dimension="ensemble",
    reduction_dimensions=["lat", "lon"],
)(forecast, forecast_coords, truth, truth_coords)
```

Use `energy_score` only after choosing bounded multivariate dimensions. Its
pairwise member calculation can be much larger than the stored forecast. Use
`brier_score(..., ensemble_dimension="ensemble")` for threshold probabilities
and `rank_histogram` for calibration checks; both require observation
coordinates without `ensemble`.

`run.diagnostic` fetches one initial condition and is not a replacement for an
ensemble driver. For member-wise diagnostics, either map and call a
batch-compatible diagnostic on all members or loop over member slices, reset
stateful diagnostics between independent sequences, and retain the diagnostic
output coordinates. Then apply statistics to the diagnostic result, not to an
unmapped prognostic tensor.
