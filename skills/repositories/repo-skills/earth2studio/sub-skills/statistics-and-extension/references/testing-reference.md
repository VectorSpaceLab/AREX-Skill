# Testing and validation reference

## Test the contract before the implementation detail

Use tiny tensors whose dimensions are easy to inspect. Start with CPU; add a
CUDA parameter only when the implementation has device-specific behavior and
skip it when CUDA is unavailable. Every new component should cover a valid call,
returned coordinate order/shape, an invalid coordinate or schema, and any
stateful or optional-dependency branch that is part of the claimed contract.
Tests belong in the consuming repository's `test/` tree, not in this runtime
skill.

A generic tensor assertion is:

```python
out, out_coords = component(x, coords)
assert list(out.shape) == [len(value) for value in out_coords.values()]
for name in component.reduction_dimensions:
    assert name not in out_coords
```

For model components, also assert that `input_coords()` and the input mapping
have the same required dimension positions, that `output_coords()` changes only
what the implementation promises, and that a prognostic iterator's first item
is the original tensor/coordinate pair. For DataFrame/DA components, assert
schema columns, `request_time` metadata, output type/device, and generator
priming/cleanup where relevant.

## Statistics/metric fixtures

Use an ordered mapping, not an unordered dict:

```python
from collections import OrderedDict

import numpy as np
import torch

coords = OrderedDict({
    "ensemble": np.arange(3),
    "time": np.array([np.datetime64("2024-01-01")]),
    "variable": np.array(["t2m"]),
    "lat": np.array([-45.0, 45.0]),
})
x = torch.tensor([[[[1.0, 2.0]], [[2.0, 3.0]], [[3.0, 4.0]]])
```

For a reduction, choose `mean(["lat"])`, check that `lat` disappears and
compare with a hand-calculated result. For weights, use a two-element weight
vector for `lat`; for two reduced axes use a matrix in the same axis order.
Check the constructor rejects a weight with the wrong number of dimensions and
that the call rejects a wrong coordinate length. For `batch_update=True`, split
one known tensor into two batches and compare the final value to a single-call
reference.

For a metric with an ensemble forecast, use `x_coords` with `ensemble` first
and `y_coords` without it. For CRPS/rank/energy score, assert that truth does
not contain the ensemble axis. For RMSE/MAE with `ensemble_dimension`, assert
that the ensemble is removed before the final reduction. For every metric,
validate non-ensemble axes by name and coordinate values before arithmetic.
Include a reordered-truth fixture with the same tensor shape; it must fail the
custom validator rather than produce a plausible but incorrect score.

Check special output axes explicitly: threshold for Brier/FSS, window size for
FSS, bin/histogram data for rank histograms, and metric labels for skill/spread
outputs. For energy score, keep the multivariate fixture small; large full-grid
pairwise distances are not a smoke test.

## Extension fixtures

### Difficult case A: missing diagnostic coordinate

Create a single-variable diagnostic with input axes `batch, variable, lat, lon`
and a tensor of shape `(1, 1, 2, 3)`. Make the broken `output_coords` omit
`variable`, then call the same coordinate validator used by `__call__`. The
check must fail before arithmetic or IO. Repair it with an output variable
array of length one and assert exact shape-to-coordinate agreement. This catches
the common error where a new variable is computed but never advertised.

### Difficult case B: misaligned ensemble metric axes

Create forecast `x` with axes `ensemble, time, variable, lat` and truth `y` with
axes `variable, time, lat`, using lengths `(3, 1, 1, 2)` and `(1, 1, 2)` so
Torch can broadcast despite the semantic order mismatch. A correct metric
wrapper must reject the reordered truth mapping before subtraction. A corrected
truth mapping with `time, variable, lat` should run and produce an output whose
shape matches output coordinates. This case is intentionally beyond a simple
shape assertion.

### Other useful cases

- Prognostic: invalid variable/lead-time coordinates raise, one call advances
  lead time, and the iterator yields step zero before step one.
- Diagnostic: invalid `variable`, latitude, or longitude values raise;
  `to("cpu")`/`to(device)` leaves the returned tensor on the expected device.
- Data source: single and multiple time/variable requests return explicit
  time/variable coordinates; forecast sources include lead time; DataFrame
  `fields` rejects an unknown column.
- Lexicon: a supported public variable maps to a source key and modifier, and a
  missing variable fails clearly rather than being silently passed through.
- Perturbation: `Zero` is identity; a seeded custom perturbation is repeatable;
  selected-variable wrappers leave all other slices unchanged.
- DA: missing `request_time`, missing required observation fields, invalid time
  tolerance, and unprimed generator usage fail with actionable errors.

## Safe commands and candidate native checks

Use the bundled helper from the generated skill tree rather than depending
on a source checkout:

```bash
uv run python <skill-root>/scripts/contract_smoke.py --help
uv run python <skill-root>/scripts/contract_smoke.py --case all
```

The original repository's tests and examples are ground-truth evidence used by
the review package, not runtime dependencies of this skill. They are not
commands for a future agent to reopen from a missing checkout. If a package
maintainer separately runs native tests, preserve the exact optional-extra,
GPU, network, credential, and failure classification; for ordinary Researcher
use, keep the bundled offline contract fixture as the strict gate.

If a statistics or perturbation test is skipped because its extra is absent,
report the missing `statistics`, `perturbation`, `utils`, or model-specific group.
If an example requires a checkpoint or remote source, retain a local protocol
fixture as the strict gate and classify the example as an optional integration
check. Preserve exact failed commands and whether the failure is code,
optional dependency, device, credential, or network related.

## Acceptance checklist

- Every created reference/script is reachable from the skill router.
- The smoke script passes `--help`, parser execution, and the tiny fixture cases.
- Output coordinate order and tensor shape agree for statistics and extensions.
- Weight dimensions and device placement are tested.
- Metric truth axes are semantically aligned, including the reordered-axis case.
- Required optional extras and backend limits are named without claiming
  exhaustive support.
- Native candidates are recorded separately from strict offline gates.
- Known omissions and unresolved failures remain explicit in the handoff.
