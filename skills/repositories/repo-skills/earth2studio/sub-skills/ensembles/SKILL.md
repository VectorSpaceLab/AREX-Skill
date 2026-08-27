---
name: ensembles
description: "Run Earth2Studio ensemble forecasts with controlled perturbations,
  bounded member batching, temporal interpolation, checkpoint restart, and
  ensemble-aware downstream analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ensemble forecasts

Use this skill when the task needs multiple prognostic rollouts from one or
more initial conditions, controlled initial-condition perturbations, member-wise
uncertainty, or ensemble verification. The primary entry point is
`earth2studio.run.ensemble`; it returns the same IO object supplied by the
caller, populated with an explicit `ensemble` coordinate.

This skill owns:

- `nensemble`, `batch_size`, `device`, output shape, and member bookkeeping.
- Built-in and custom perturbation selection, normalization, and coordinate
  requirements.
- Medium-range, temporally interpolated, lagged, HENS-style, and cyclone-
  analysis handoffs.
- Reducing or verifying ensemble outputs with diagnostics and statistics.

It does not replace deterministic model/data setup, the general IO backend
catalog, model-package download, or a complete cyclone tracker recipe. Keep
those concerns in the caller's model/data/IO skills. Support is not exhaustive:
model-specific extras, accelerator support, licenses, and data-source access
remain prerequisites for the selected components.

## Fast route

1. Confirm that the prognostic model accepts a leading dynamic member axis and
   record its `input_coords()`, output step, variables, and spatial grid.
2. Choose a perturbation whose units and coordinate assumptions match the model.
   Use `Zero()` only for a deliberately identical control ensemble.
3. Choose `nensemble` and a GPU-fitting `batch_size`; do not use the full
   ensemble as a batch merely because it is the default.
4. Pre-create an IO store whose coordinates have `ensemble` first, followed by
   `time`, `lead_time`, and the model output dimensions. See
   [workflows](references/workflows.md).
5. Run the contract in [API reference](references/api-reference.md), then
   validate member count, lead-time count, finite values, and perturbation
   spread before computing statistics.
6. For a large or asynchronous store, run the offline configuration check:
   `python scripts/check_ensemble_config.py --help`.

## Minimal invocation

```python
import numpy as np
from earth2studio.io import ZarrBackend
from earth2studio.perturbation import SphericalGaussian
from earth2studio.run import ensemble

io = ZarrBackend(
    "forecast.zarr",
    chunks={"ensemble": 1, "time": 1, "lead_time": 1},
    backend_kwargs={"overwrite": True},
)
result = ensemble(
    time=["2024-01-01"],
    nsteps=10,
    nensemble=8,
    prognostic=model,
    data=data_source,
    io=io,
    perturbation=SphericalGaussian(noise_amplitude=0.15),
    batch_size=2,
    output_coords={"variable": np.array(["t2m", "tcwv"])},
    device=device,
)
```

`nsteps=10` produces `nsteps + 1` lead-time slices, including the initial
slice. `batch_size=2` still writes all eight members with member coordinates
`0..7`; it only limits concurrent model state. `output_coords` is a coordinate
selection, not a perturbation selection.

## Decide before running

- **Small/medium ensemble:** use `Gaussian` for independent unstructured noise,
  `SphericalGaussian` for a spatially correlated spherical field, or a custom
  wrapper for variable-specific amplitudes. Set `batch_size` to the largest
  value that fits the model and perturbation working set.
- **Analysis-time lags:** use `LaggedEnsemble` only when the source can fetch
  each lag and `len(lags) == nensemble`. Negative lags are appropriate for
  forecasting; positive lags are for hindcast-like use, not future prediction.
- **Medium-range finer cadence:** pass a correctly configured prognostic
  interpolation wrapper (for example `InterpModAFNO`) as `prognostic`. The
  ensemble workflow detects its `interp_method` while fetching initial data;
  do not manually resize the initial tensor.
- **HENS or cyclone uncertainty:** use the selected model/checkpoint and its
  compatible HENS perturbation as a separate run. Keep `batch_size` small,
  write one store per checkpoint when needed, then combine outputs only after
  checking member coordinate semantics. The HENS perturbation needs model/data
  warmup and spherical-grid assumptions; it is not a generic noise shortcut.
- **Huge ensemble:** stream batches to a disk-backed, ensemble-aware store.
  Avoid in-memory output and avoid `batch_size=nensemble` unless the state is
  known to fit. For `AsyncZarrBackend`, `ensemble` and `lead_time` must be in
  `parallel_coords` because built-in ensemble writes partial slices on both
  axes; call `close()` for non-blocking writes. See the synthetic check and
  recovery notes in [troubleshooting](references/troubleshooting.md).

## Output and downstream handoff

The built-in workflow writes one array per selected variable. The normal array
layout is `[ensemble, time, lead_time, ...model output dimensions...]`; the
coordinate dictionary is the authority when a model has extra dimensions.
Check `array.shape[0] == nensemble` and `array.shape[2] == nsteps + 1` for a
single start time before analysis. A subset `output_coords` can remove
variables or spatial points, so validate against the requested subset rather
than the full model grid.

For member summaries, apply a statistic to tensors with an `ensemble` coordinate
and reduce that named dimension, for example
`earth2studio.statistics.mean(["ensemble"])` or
`earth2studio.statistics.std(["ensemble"])`. Use `crps`, `energy_score`,
`brier_score`, or `rank_histogram` only with their metric contracts: the
observation tensor must not contain `ensemble`, and expensive full-field energy
scores should be avoided unless memory is budgeted. For a diagnostic model,
map each forecast tensor to `diagnostic.input_coords()` and call the diagnostic
on the member-batched tensor in a custom loop; `run.diagnostic` itself is not an
ensemble runner. Concrete patterns are in [workflows](references/workflows.md).

## Verification gates

Before accepting a run, confirm:

- the selected extras and model/data prerequisites import;
- the perturbation returns the same tensor rank, member length, device, and
  compatible coordinates;
- all requested member IDs are present, with no missing or duplicate writes;
- initial perturbation spread is plausible in the model's physical units;
- all output arrays have the requested `nsteps + 1` lead times and finite values;
- a tiny CPU fixture works before a long GPU run; and
- the chosen downstream diagnostic/statistic receives matching coordinates.

Use [API reference](references/api-reference.md) for exact signatures and
[troubleshooting](references/troubleshooting.md) for predictable failures.

## Bundled helper and evidence limits

- `scripts/check_ensemble_config.py` performs only local arithmetic and
  compatibility checks; it never downloads data, models, or credentials.
- The built-in list in the API reference is a useful selection map, not an
  exhaustive model or backend inventory.
- Native candidates for verification are the ensemble workflow tests, the
  perturbation contract tests, the getting-started ensemble example, and the
  medium-range interpolation/HENS examples. They require the relevant model,
  data, optional extras, and often GPU/network resources; this skill does not
  claim to have run them.
- Intentionally omitted: deterministic fetch/model construction, generic IO
  tuning beyond ensemble slicing, serving clients, distributed orchestration,
  and a full cyclone tracker implementation.
