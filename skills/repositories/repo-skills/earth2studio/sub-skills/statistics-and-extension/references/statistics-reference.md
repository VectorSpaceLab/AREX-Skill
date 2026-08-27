# Statistics and metric reference

## Protocols and output coordinates

The public protocols are structural (`runtime_checkable`), so a custom class does
not need to inherit a base class. A `Statistic` provides:

```python
import torch

from earth2studio.statistics import Statistic
from earth2studio.utils.type import CoordSystem

class MyStatistic:
    @property
    def reduction_dimensions(self) -> list[str]: ...

    def output_coords(self, input_coords: CoordSystem) -> CoordSystem: ...

    def __call__(
        self, x: torch.Tensor, coords: CoordSystem
    ) -> tuple[torch.Tensor, CoordSystem]: ...
```

A `Metric` has the same property and `output_coords`, but its call accepts
`(x, x_coords, y, y_coords)`. By convention `x` is forecast/prediction and `y`
is observation/truth. A reduction removes dimensions from the coordinate mapping;
the returned tensor must have exactly the lengths and order of the returned
mapping. Validate every requested reduction dimension before indexing it.

A robust output-coordinate implementation is:

```python
from collections import OrderedDict
from earth2studio.utils.coords import handshake_dim

def output_coords(self, input_coords: CoordSystem) -> CoordSystem:
    out = input_coords.copy()
    for dim in self.reduction_dimensions:
        handshake_dim(input_coords, dim)
        out.pop(dim)
    return out
```

If the result adds a result axis (for example thresholds, windows, or metric
labels), add that axis deliberately and place it where the returned tensor puts
it. Do not leave reduced dimensions in `out`; do not remove an axis that still
exists in the returned tensor. A `__str__` method is not part of the protocol,
but is useful as the IO array name and should be stable (for example,
`"lat_lon_rmse"`).

## Reductions and weights

The built-in moments are `mean`, `variance`, and `std`. Their constructors are:

```python
mean(
    reduction_dimensions: list[str],
    weights: torch.Tensor = None,
    batch_update: bool = False,
)
variance(reduction_dimensions, weights=None, batch_update=False)
std(reduction_dimensions, weights=None, batch_update=False)
```

When `weights` is supplied, its number of dimensions must equal the number of
reduction dimensions. At call time its shape must equal the coordinate lengths in
reduction-dimension order:

```python
expected = [len(coords[d]) for d in coords if d in reduction_dimensions]
assert list(weights.shape) == expected
```

Weights are expanded with singleton axes for non-reduced dimensions. A missing
weight is treated as ones. Put weights on the same device as the input tensor
before arithmetic; the built-ins do this internally. `lat_weight(lat)` computes
`cos(lat * pi / 180)` and divides by its mean. It accepts a NumPy array or a
Torch tensor and preserves that array family.

Use `batch_update=True` only when calls are sequential pieces of one logical
sample stream. The object retains running state (`n`, sums, or component
statistics); do not reuse it across independent forecasts, variables, or
coordinate regimes. Every batch must describe the same non-updated axes and use
compatible weight shapes. Test a streamed result against a single-call result.

## Metric alignment and ensemble axes

Before a metric call, establish an axis contract. If forecast `x` has an
ensemble dimension and truth `y` does not, the non-ensemble dimensions must occur
in the same order and have equal coordinate values (or an explicitly documented
broadcastable singleton coordinate). A safe local validator is:

```python
import numpy as np


def require_metric_axes(
    x_coords: CoordSystem,
    y_coords: CoordSystem,
    ensemble_dimension: str | None = None,
) -> None:
    expected = [d for d in x_coords if d != ensemble_dimension]
    if list(y_coords) != expected:
        raise ValueError(
            f"truth axes {list(y_coords)} do not match forecast axes {expected}"
        )
    for dim in expected:
        if x_coords[dim].shape != y_coords[dim].shape or not np.array_equal(
            x_coords[dim], y_coords[dim]
        ):
            raise ValueError(f"coordinate values differ for {dim}")
```

Do this check even when Torch would broadcast the tensors: equal lengths with
reordered semantic axes can silently score the wrong fields. Built-in metrics
perform different levels of explicit coordinate checking, so custom code should
not assume that arithmetic will detect a bad mapping.

`rmse(reduction_dimensions, weights=None, batch_update=False,
ensemble_dimension=None)` optionally takes the ensemble mean of `x` before
computing the weighted mean square error against `y`. `mae` follows the same
shape of API. `spread_skill_ratio` and `skill_spread` use an ensemble dimension
plus reduction dimensions; truth has no ensemble axis. `acc` expects `time` and
`variable` and can fetch an optional climatology. If `x` contains `lead_time`,
its truth/climatology path must also represent that axis as appropriate.

Ensemble scoring rules have stricter roles:

- `crps(ensemble_dimension, reduction_dimensions=None, weights=None, fair=False)`
  reduces the forecast ensemble axis; truth must not contain it. Optional
  fair-CRPS support belongs to the `statistics` extra.
- `rank_histogram(ensemble_dimension, reduction_dimensions, number_of_bins=None,
  randomize_ties=True)` returns `histogram_data` and `bin` axes in addition to
  the unreduced truth coordinates. The default bin count is ensemble size plus
  one.
- `energy_score(ensemble_dimension, multivariate_dimensions,
  reduction_dimensions=None, weights=None, fair=False)` removes the ensemble
  and multivariate axes. Full spatial multivariate grids can be very memory
  intensive; select dimensions for a tiny validation first.
- `brier_score` and `fss` can use an optional ensemble axis and add explicit
  `threshold` (and for FSS, `window_size`) result axes.

The package also exposes ACC, log-spectral distance, FSS, Brier score, rank,
CRPS, energy score, RMSE/MAE, spread/skill, moments, and latitude weighting.
This is a usable inventory, not an exhaustive promise of backend or optional
extra support.

## Custom statistic workflow

1. Decide whether the operation reduces existing axes or creates a new physical
   field. Use this protocol only for reductions/metrics; use a diagnostic for a
   derived field with a new variable.
2. Put fixed climatology/constants on the correct device in `__call__`, and keep
   units explicit. For a point-index statistic, select by coordinate values or
   use `map_coords`; never assume a hard-coded tensor index without checking the
   coordinate mapping.
3. Form a copied output mapping by removing the exact reduced axes. If the
   operation has time-varying metadata, derive it from `coords["time"]` and
   `coords["lead_time"]` rather than inventing a tensor axis.
4. Add `__str__` for IO naming and a `reduction_dimensions` property even when
   the calculation uses helper reductions internally.
5. Exercise a one-cell or two-cell fixture, a weighted fixture, a missing-axis
   error, and (for metrics) an axis-order mismatch error.

The seasonal SOI pattern is instructive: it declares point coordinate contracts,
maps the tensor to those points, removes the selected variable/lat/lon axes, and
returns a named scalar-like statistic. Preserve that contract pattern without
copying its network climatology acquisition into an offline check.
