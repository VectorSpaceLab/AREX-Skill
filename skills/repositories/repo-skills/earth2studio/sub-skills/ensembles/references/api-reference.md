# Ensemble and perturbation API reference

This reference records the public contracts used by the `ensembles` router. It
is intentionally limited to ensemble execution and perturbation behavior; it
does not enumerate every model or IO backend.

## `run.ensemble`

```python
from earth2studio.run import ensemble

ensemble(
    time: list[str] | list[datetime] | list[np.datetime64],
    nsteps: int,
    nensemble: int,
    prognostic: PrognosticModel,
    data: DataSource,
    io: IOBackend,
    perturbation: Perturbation,
    batch_size: int | None = None,
    output_coords: CoordSystem = OrderedDict({}),
    device: torch.device | None = None,
    verbose: bool = True,
    checkpoint: Checkpoint | CheckpointSession | NullCheckpoint = NullCheckpoint(),
) -> IOBackend
```

### Inputs and execution order

- `time` accepts strings, `datetime`, or `numpy.datetime64` values. It is
  normalized to a time array before data fetch.
- `nsteps` is the number of prognostic advances after the initial state. The
  workflow writes the initial state and stops after the slice at `nsteps`.
- `nensemble` is the number of member IDs. The output coordinate is
  `np.arange(nensemble)`; IDs are zero-based and contiguous.
- `prognostic` is moved to `device`, explicitly or to CUDA when available and
  CPU otherwise. Its `input_coords()` and `output_coords()` define required
  fields and output axes.
- `data` must satisfy the `DataSource` contract used by `fetch_data`. It is
  fetched once for the initial condition. If the prognostic object has an
  `interp_method` attribute, that method and `prognostic.input_coords()` are
  passed as the interpolation target; otherwise the fetch uses nearest-neighbor
  behavior.
- `io` is initialized with the model output coordinates after the workflow
  removes an empty `batch` coordinate, adds `time` and generated `lead_time`,
  and prepends `ensemble`. The `variable` coordinate is split into array names.
- `perturbation` is called once per ensemble batch after the initial tensor is
  repeated along a new leading `ensemble` axis and mapped to model input
  coordinates.
- `batch_size=None` means `nensemble`; otherwise the workflow clamps it to
  `min(nensemble, batch_size)`. A caller should still pass a positive value;
  zero or negative values are invalid configuration even though validation is
  not performed before the internal batch arithmetic.
- `output_coords` selects output variables/dimensions through coordinate
  mapping. It does not change the model's input or perturbation fields.
- `checkpoint` records `completed_ensembles` after a member batch finishes and
  can resume from the first incomplete member. Component state restoration is
  opt-in; see the checkpoint notes below.

The implementation's effective sequence is:

```text
x0, coords0 = fetch_data(data, time, model input variables/lead_time, device,
                         interp_to, interp_method)
create IO coordinates with ensemble/time/lead_time
for batch_id in range(0, nensemble, batch_size):
    coords = {"ensemble": member IDs for this batch} + coords0
    x = repeat(x0, batch length)
    x, coords = map_coords(x, coords, prognostic.input_coords())
    x, coords = perturbation(x, coords)
    for x, coords in prognostic.create_iterator(x, coords):
        map to output_coords and write member/time/lead_time slices
```

The perturbation must therefore be able to handle the batch length, not just the
full requested `nensemble`.

## Tensor and coordinate rules

For a normal global prognostic output, each selected variable is stored with
coordinates equivalent to:

```text
ensemble, time, lead_time, variable-independent output dimensions
```

The workflow's `split_coords` call removes `variable` from each named array.
The initial input tensor presented to a perturbation has a leading member axis,
then the source/model axes (usually `time`, `lead_time`, `variable`, `lat`,
`lon`, subject to the model contract). Do not infer axis positions from the
Python tensor alone: use the ordered `coords` mapping and `map_coords`.

A perturbation returns `(new_x, new_coords)`. The safe default is to preserve
both tensor shape and coordinate values. A perturbation may replace values, but
must not silently reorder members, variables, time, or lead time. Model batch
axes are leading dynamic axes and must accept any nonzero batch size; model
objects normally advertise an empty `batch` coordinate before execution.

## Perturbation protocol

```python
from earth2studio.perturbation import Perturbation

class MyPerturbation:
    @torch.inference_mode()
    def __call__(self, x: torch.Tensor, coords: CoordSystem):
        return new_x, new_coords
```

The runtime protocol is a callable with the equivalent signature:

```python
(x: torch.Tensor, coords: CoordSystem)
    -> tuple[torch.Tensor, CoordSystem]
```

It is a `typing.Protocol`, not a required base class. The callable runs under
inference mode in the built-ins. Custom code should preserve the input device,
dtype, rank, and coordinate order unless it intentionally documents a model
mapping.

## Built-in perturbation families

All names below are exported from `earth2studio.perturbation`. This is a
selection map, not an exhaustive list of third-party or model-internal methods.

| Class | Constructor | Required shape/coordinate assumptions | Use |
|---|---|---|---|
| `Zero` | `Zero()` | none | Control/identical members; no spread by design. |
| `Gaussian` | `Gaussian(noise_amplitude=0.05, seed=None)` | Amplitude scalar or broadcastable tensor. | Independent element-wise Gaussian noise; supports checkpointed RNG state. |
| `Brown` | `Brown(noise_amplitude=0.05, reddening=2)` | `lat` and `lon` must be the last two coordinate dimensions. | 2-D latitude/longitude reddened noise. |
| `SphericalGaussian` | `SphericalGaussian(noise_amplitude=0.05, alpha=2.0, tau=3.0, sigma=None)` | `lat`/`lon` last; grid must have `N:2N` or `N+1:2N` shape. | Spherical Gaussian random field; needs the `perturbation` extra. |
| `CorrelatedSphericalGaussian` | `CorrelatedSphericalGaussian(noise_amplitude, sigma=1.0, length_scale=5e5, time_scale=48.0)` | `lat`/`lon` last; same equirectangular aspect requirement. | Correlated spherical field for HENS-style seeding; needs the `perturbation` extra. |
| `LaggedEnsemble` | `LaggedEnsemble(source, lags)` | `ensemble`, `time`, `lead_time` must be axes 0, 1, 2; `len(lags)` must equal member count. | Replace each member's initial fields with a source fetch at a lag. |
| `BredVector` | `BredVector(model, noise_amplitude=0.05, integration_steps=20, ensemble_perturb=False, seeding_perturbation_method=Brown())` | Callable model and seeding perturbation; multiple input lead times can be unexpected. | Model-evolved bred-vector perturbation. |
| `HemisphericCentredBredVector` | `HemisphericCentredBredVector(model, data, seeding_perturbation_method, noise_amplitude=0.35, integration_steps=3)` | Time size 1; five or six tensor dimensions; lat/lon and variable axes; warmup source fetch. | Centered hemispheric bred vectors for HENS-like workflows. |

The optional dependency group named `perturbation` supplies
`torch-harmonics` and `scipy`. Installing the group does not install a model,
data credentials, or a compatible accelerator runtime. Use the model's own
extra as well.

## Amplitude and normalization

Built-in noise is applied directly to the tensor it receives. There is no
implicit normalization/denormalization step in the protocol. A scalar
`noise_amplitude` therefore has the units of the model input field, while a
Tensor amplitude must broadcast with `x` (commonly one value per variable and
singleton spatial axes). For mixed-unit variables, prefer a per-variable
broadcast tensor or a wrapper that selects variables explicitly.

A robust variable-specific wrapper follows this contract:

```python
class ApplyToVariable:
    def __init__(self, perturbation, variables):
        self.perturbation = perturbation
        self.variables = {variables} if isinstance(variables, str) else set(variables)

    def __call__(self, x, coords):
        candidate, _ = self.perturbation(x, coords)
        selected = np.isin(coords["variable"], list(self.variables))
        x = x.clone()
        x[..., selected, :, :] = candidate[..., selected, :, :]
        return x, coords
```

The slice above assumes the model puts `variable`, `lat`, and `lon` in those
relative positions; use `map_coords` or compute indices from `list(coords)` for
other models. Always test the wrapper on a tiny fixture and check that
unselected variables are unchanged at the initial slice.

## Checkpoint behavior

`run.ensemble` stores a small `completed_ensembles` metadata list and resets
component write counters between member batches. A checkpoint below level 2
cannot promise a complete mid-rollout restart; the workflow warns and reruns
that batch from lead time zero. Level 2 can resume a rollout only when the model
and perturbation bind compatible component state. `Gaussian` has explicit RNG
state support; custom perturbations must opt in themselves. Do not assume a
random perturbation is reproducible after restart merely because a seed was set.

## Downstream statistic and metric contracts

Statistics use a named coordinate reduction and return `(value, out_coords)`:

```python
from earth2studio.statistics import mean, std

ensemble_mean, mean_coords = mean(["ensemble"])(forecast, forecast_coords)
ensemble_std, std_coords = std(["ensemble"])(forecast, forecast_coords)
```

`crps(ensemble_dimension="ensemble", ...)`,
`energy_score(ensemble_dimension="ensemble", multivariate_dimensions=[...])`,
`brier_score(..., ensemble_dimension="ensemble")`, and
`rank_histogram(ensemble_dimension="ensemble", ...)` take a forecast with the
member axis and an observation without it. They validate coordinate names and
order; remove or map the member coordinate from the observation first. The
energy score can materialize an ensemble-by-ensemble distance over selected
multivariate dimensions, so do not use a full high-resolution grid without a
memory estimate.
