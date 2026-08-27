# Component extension reference

## Tensor model coordinates

Use `CoordSystem` from `earth2studio.utils.type`, an ordered mapping of axis
names to NumPy arrays. Public gridded conventions are latitude north-to-south
(typically `90` to `-90`) and longitude from `0` to `360` without a repeated
endpoint. Use Earth2Studio lexicon identifiers such as `t2m`, `u10m`, `v10m`,
`z500`, and `tcwv`; a custom name needs an explicit consumer contract and is not
automatically understood by every model or source.

For a normal tensor model, make `input_coords()` return a fresh mapping. Put
`"batch": np.empty(0)` first. A prognostic normally exposes
`lead_time=np.array([np.timedelta64(0, "h")])`, then `variable`, `lat`, and
`lon`; a diagnostic normally has no `lead_time`. Dynamic `time` may be
`np.empty(0)`. Keep the coordinate order identical to the tensor shape.

`handshake_dim(coords, name, index)` checks both presence and position;
`handshake_coords(coords, expected, name)` checks shape and values. Use them in
`output_coords` before constructing the result, not after a failed tensor
operation. `batch_coords()` compresses outer batch axes for coordinate methods;
`batch_func()` compresses matching tensor/coordinate pairs for model calls.
Decorated methods must receive `(tensor, CoordSystem)` positional pairs. If two
inputs are batched, their flattened batch shape and coordinates must agree.

## Prognostic protocol

A custom prognostic must provide:

```python
from collections.abc import Iterator
from typing import Any

import torch

from earth2studio.models.batch import batch_func
from earth2studio.utils.type import CoordSystem


class CustomPrognostic:
    def input_coords(self) -> CoordSystem: ...
    def output_coords(self, coords: CoordSystem) -> CoordSystem: ...
    def __call__(
        self, x: torch.Tensor, coords: CoordSystem
    ) -> tuple[torch.Tensor, CoordSystem]: ...
    def create_iterator(
        self, x: torch.Tensor, coords: CoordSystem
    ) -> Iterator[tuple[torch.Tensor, CoordSystem]]: ...
    def to(self, device: Any) -> "CustomPrognostic": ...
```

The protocol is structural; a PyTorch module supplies `to(device)` naturally.
`output_coords` must validate the input and advance `lead_time` by exactly the
model step. The iterator must yield the input condition first as step zero, then
roll forward indefinitely or for the documented finite sequence. If using
`PrognosticMixin`, preserve its front/rear hooks around each model step so
perturbations and checkpoint-aware state can participate. A simple custom
module can use `@batch_coords()` on `output_coords`, `@batch_func()` on
`__call__`, and a generator that delegates to a decorated helper; test the
chosen decorator arrangement with a batched fixture.

A minimal step is:

```python
@batch_func()
def __call__(self, x, coords):
    out_coords = self.output_coords(coords)
    return self.core(x), out_coords

def create_iterator(self, x, coords):
    yield x, coords
    while True:
        x, coords = self(x, coords)
        yield x, coords
```

Do not use a diagnostic for time integration. Do not expose a source-model
latitude order merely because the private core uses one; convert internally and
return public coordinates.

## Diagnostic protocol and missing-coordinate failure

A diagnostic supplies `input_coords`, `output_coords`, `__call__`, and `to`; it
has no iterator and normally no `lead_time`. It may transform variables or
resolution, but every returned axis still needs a coordinate entry. If a custom
implementation computes `out` with shape `(batch, variable, lat, lon)` and its
`output_coords` omits `"variable"`, the result is invalid even if the tensor
has the right number of elements. Depending on where it is consumed, the first
symptom can be a `KeyError`, a coordinate handshake failure, an IO shape error,
or a silent label mismatch. Repair by:

1. Calling `self.output_coords(coords)` before the numerical operation.
2. Validating input `variable`, `lat`, and `lon` positions and values.
3. Returning an output mapping with a `variable` array whose length equals
   `out.shape[variable_axis]` (for example `np.array(["t2m_c"])`).
4. Checking `list(out.shape) == [len(v) for v in out_coords.values()]` in a tiny
   test. Use `map_coords` only when the target values exist or numeric nearest
   mapping is explicitly intended.

`run.diagnostic` maps prognostic output to the diagnostic input, calls the
single-step diagnostic, then maps to the requested IO coordinates. A custom
output field must therefore be named in `output_coords` and selected in the
workflow's `output_coords` override if it is the desired stored result.

## Data source protocols

Choose the narrowest source type:

| Type | Call shape | Return |
|---|---|---|
| `DataSource` | `(time, variable)` | xarray `DataArray`, with time/variable and spatial dimensions |
| `ForecastSource` | `(time, lead_time, variable)` | xarray `DataArray`, including lead time |
| `DataFrameSource` | `(time, variable, fields=None)` | pandas-like `DataFrame` |
| `ForecastFrameSource` | `(time, lead_time, variable, fields=None)` | pandas-like `DataFrame` |

The array source call accepts a `datetime`, list, or `TimeArray` and a variable
string/list/`VariableArray`. Return physical units, explicit time and variable
coordinates, and a stable dimension order. Forecast outputs must represent both
requested time and lead time; verify their `dims` with `fetch_data` because
source-specific layout is not a license to rely on positional coincidence.

DataFrame sources must expose a PyArrow `SCHEMA`. `fields` selects a subset of
that schema; validate unknown names and incompatible types. `fetch_dataframe`
normalizes the request, calls the source, adds `attrs["request_time"]` and
`attrs["request_lead_time"]`, and returns pandas on CPU or cudf on CUDA when
available. DA models commonly require those request attributes.

For synchronous sources, normalize with `prep_data_inputs` or
`prep_forecast_inputs`; if the source has an async implementation, keep the
sync wrapper and async method behavior equivalent. Remote caching, partial
fetches, authentication, and provider-specific packages are source-specific;
do not add them to a local smoke check.

## Lexicon and physical units

When remote names differ from public names, define a source lexicon with
`metaclass=LexiconType`, a `VOCAB` mapping, and `get_item(name)` returning
`(source_key, modifier)`. `::` is the established separator for structured keys
such as `"UGRD::200 mb"`. Apply modifiers after loading raw data and document
unit/sign conversions. A lexicon is an explicit tested subset, not an exhaustive
listing of a remote store. Align DataFrame fields with `E2STUDIO_SCHEMA` where
possible and use `variable`, `time`, `lat`, `lon`, and `elev` consistently.

## Perturbation protocol and ensemble composition

A perturbation implements inference-mode `__call__(x, coords) -> (y, coords)`.
It changes the tensor supplied to an ensemble workflow; it is not merely a noise
sampler. Earth2Studio boundaries carry physical units, so noise amplitude and
normalization must be defined per variable. A wrapper can apply an existing
perturbation only to selected variable slices, then restore the untouched
fields. Preserve coordinates unless the perturbation explicitly changes them.

`run.ensemble` constructs an ensemble axis first, calls the perturbation, and
then rolls the prognostic in batches. A safe custom perturbation checks the
expected `ensemble`, `time`, `lead_time`, `variable`, `lat`, and `lon` positions
when its algorithm needs them. `batch_size` controls the number of ensemble
members run per batch; it does not change the metric ensemble axis in stored
outputs. Seeded generators are preferable for reproducible tests; stateful
random generators need checkpoint/state tests when checkpointing is supported.

## Data assimilation protocol

A DA model may consume pandas/cudf DataFrames, xarray DataArrays, or both. The
structural methods are:

- `__call__(*args) -> tuple[DataFrame | DataArray, ...]` for stateless updates;
- `create_generator(*args)` for stateful send/yield updates;
- `init_coords()` for required initial state, or `None` if stateless;
- `input_coords()` returning one `FrameSchema`/`CoordSystem` per input;
- `output_coords(input_coords, *args, **kwargs)` returning one per output;
- `to(device)` for device movement.

Use `FrameSchema` for observation columns and `CoordSystem` for gridded arrays.
Validate required fields early. For GPU tabular paths, cudf/cupy are optional;
keep a CPU/pandas test as the baseline. A stateful generator must be primed
before `.send()` and should handle `GeneratorExit` when it owns resources.

Any component that filters observations by time must type its constructor as
`TimeTolerance` and normalize once with `normalize_time_tolerance`. A single
value means symmetric `(-t, +t)`; a two-element tuple is an asymmetric lower
and upper bound and must satisfy lower <= upper. Store normalized bounds and use
helpers such as `filter_time_range`; do not manually reinterpret the value.
