---
name: statistics-and-extension
description: "Use Earth2Studio statistics, metrics, perturbations, and component
  protocols to build and validate safe custom inference extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Statistics and extension

Use this sub-skill when a request needs a reduction or verification metric, a
custom prognostic/diagnostic/data source/assimilation/perturbation component, or
a small workflow that composes those contracts. It targets Earth2Studio 0.18.0a0
public APIs and Python 3.11–3.14. It does not enumerate every model, data source,
backend, or optional extra.

## Route the request

- **Reduction:** one input, named `reduction_dimensions`; use `Statistic`.
- **Verification:** forecast `x` plus truth `y`; use `Metric` and validate the
  non-ensemble axes before arithmetic.
- **Derived physical field:** use a diagnostic, not a statistic.
- **Time stepping:** implement a prognostic and its initial-condition-first
  iterator.
- **Data access:** implement the matching array or DataFrame source protocol;
  add a lexicon only when source keys need translation.
- **Observation update:** implement the DA protocol with explicit schemas.
- **Ensemble initial-state change:** implement a `Perturbation`; it receives and
  returns a tensor/coordinate pair.

Read the focused contracts before editing:

- [Statistics and metrics](references/statistics-reference.md)
- [Component extension contracts](references/extension-reference.md)
- [Testing and validation](references/testing-reference.md)
- [Failure recovery](references/troubleshooting.md)
- [Offline contract smoke check](scripts/contract_smoke.py)

## Non-negotiable coordinate contract

Treat a `CoordSystem` as an ordered mapping whose values describe tensor axes in
exactly the same order. `batch` is the first dynamic model axis when using
`batch_coords()`/`batch_func()`. Common public model axes are `time`,
`lead_time`, `variable`, `lat`, and `lon`; a prognostic has `lead_time`, while a
single-step diagnostic normally does not. Do not silently reorder axes to make a
broadcast work.

For every custom component:

1. Define `input_coords()` with fresh arrays and explicit Earth2Studio variable
   names, physical units, and latitude/longitude conventions.
2. Validate required dimension positions with `handshake_dim` and required values
   with `handshake_coords` (or a deliberate equivalent for tabular schemas).
3. Build `output_coords` from a copy, removing only reduced dimensions or changing
   only the documented output fields. Every returned tensor axis needs a matching
   coordinate variable of the same length.
4. Keep data in physical units at component boundaries. Normalize only inside a
   component and undo that normalization before returning.
5. Test both a valid tiny tensor and a malformed coordinate mapping. Coordinate
   shape equality alone is not enough when semantic axis order differs.

## Minimal implementation loop

1. Write the input/output contract, axis order, variable vocabulary, units,
   optional dependencies, device behavior, statefulness, and whether network or
   checkpoints are required. Keep network/download actions out of smoke checks.
2. Select the smallest protocol. A statistic only removes dimensions; a
   diagnostic may add or transform variables; a prognostic must advance
   `lead_time`; a source must return xarray or DataFrame data with the required
   metadata; DA may return multiple state/observation outputs.
3. Implement the protocol and coordinate validation before the numerical method.
   Use `@batch_coords()` and `@batch_func()` for ordinary tensor model patterns,
   and use inference mode for inference-only perturbations/forwards.
4. Compose through the verified workflow signatures. Use
   `run.deterministic(time, nsteps, prognostic, data, io, output_coords=..., device=..., verbose=..., checkpoint=...)`,
   `run.diagnostic(..., diagnostic, data, io, ...)`, or
   `run.ensemble(..., nensemble, ..., perturbation, batch_size=..., ...)`.
5. Validate output coordinates and tensor shapes at every boundary. For metrics,
   compare forecast and truth axes by name and coordinate values before calling a
   built-in reduction; an accidental same-shape subtraction can still be wrong.
6. Run the offline smoke check, focused unit tests, then applicable native tests or
   examples. Report skipped optional-backend/network checks rather than claiming
   support for them.

## Common statistical recipes

```python
import torch

from earth2studio.statistics import lat_weight, mean, rmse

weights = lat_weight(torch.as_tensor(latitudes))
area_mean = mean(["lat"], weights=weights)
score = rmse(["lat", "lon"], weights=grid_weights,
             ensemble_dimension="ensemble")
```

`mean`, `variance`, and `std` can maintain state with `batch_update=True`.
Metrics such as RMSE/MAE can reduce an ensemble mean when
`ensemble_dimension` is supplied. CRPS, rank histograms, and energy score expect
an ensemble axis in forecast `x` and no such axis in truth `y`. Use the exact
weight dimensionality and output-coordinate rules in the statistics reference.

## Safe validation commands

From any directory, run the bundled checker by its installed skill path:

```bash
uv run python <skill-root>/scripts/contract_smoke.py --help
uv run python <skill-root>/scripts/contract_smoke.py --case all
```

When developing a custom component in your own project, run that project's
focused tests in its managed environment after the bundled contract smoke. A
missing optional Earth2Studio group is a limitation to report, not a reason to
install an unbounded dependency set. See the testing reference for the local
fixture expectations; the original repository's native test paths are review
evidence, not runtime dependencies.

## Scope boundaries and handoff

This sub-skill covers component implementation, statistics/metric axes and
weights, lexicon/time-tolerance conventions, focused tests, and safe local
validation. It intentionally excludes release/CI operations, package-wide
maintainer workflows, serving-client construction, exhaustive catalogues, and
remote data/model downloads. Preserve those limits in the downstream handoff.
Record native candidates and the two difficult synthetic cases: a diagnostic
whose returned coordinate mapping omits its output `variable`, and an ensemble
metric whose truth axes are reordered but retain a broadcastable shape.
