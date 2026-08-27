---
name: coordinate-transformations
description: "Transform coordinates between pyproj CRS and projections with
  explicit axis-order, operation-selection, array, time, bounds, pipeline, and
  grid-availability checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Coordinate transformations

Use this route when the job executes a coordinate operation: CRS-to-CRS
conversion, a PROJ pipeline, a projection-only conversion, transformed bounds,
or selection/diagnosis of alternative operations. Begin with
[`references/workflows.md`](references/workflows.md), then consult the focused
references before choosing an operation.

## Route and boundaries

- Use `Transformer.from_crs` for a CRS-to-CRS operation, including datum or
  coordinate-frame changes. Inspect the selected operation before trusting
  results.
- Use `Transformer.from_pipeline` when the operation is an explicit PROJ
  pipeline or an identified coordinate-operation object. Use
  `TransformerGroup` when alternatives, area-of-interest ranking, accuracy
  constraints, or missing grids must be compared.
- Use `Proj` only for a projection operation within the projection's own datum
  or for a deliberately specified PROJ projection. It is not a generic datum
  transformation tool.
- CRS construction, axis metadata, authority lookup, and database queries go
  to [`../crs-and-database/SKILL.md`](../crs-and-database/SKILL.md).
- Network policy, PROJ data directories, grid discovery, and explicit grid
  synchronization go to
  [`../cli-data-and-network/SKILL.md`](../cli-data-and-network/SKILL.md).
- Distance, area, azimuth, and ellipsoidal calculations go to
  [`../geodesic-calculations/SKILL.md`](../geodesic-calculations/SKILL.md).

## Minimum operating sequence

1. Write down source and target CRS, coordinate order, units, dimensionality
   (2D/3D/4D), geographic area, and whether the input is degrees or radians.
2. Validate the CRS definitions and their axis metadata through the CRS route.
   If application data is conventionally `(longitude, latitude)`, create the
   transformer with `always_xy=True` and document that contract.
3. Create one reusable `Transformer`; do not use the deprecated module-level
   `transform` or `itransform` for new code. Apply `Transformer.transform` or
   `itransform` to scalar, array, or point-stream inputs.
4. For a datum-sensitive or regional conversion, select with an
   `AreaOfInterest` and appropriate `authority`, `accuracy`, and
   `allow_ballpark` constraints. Use `only_best=True` only when an unavailable
   best operation must be a hard error.
5. When operation availability is uncertain, inspect a `TransformerGroup`:
   compare `transformers`, `unavailable_operations`, `best_available`,
   operation descriptions, accuracies, and grid metadata. Do not infer that a
   missing grid is downloadable or that network access is permitted.
6. Validate the output shape, units, plausible range/area of use, and a
   reverse transformation when the operation has an inverse. Use
   `errcheck=True` at validation boundaries so invalid points fail explicitly;
   retain the default `inf` behavior only when the caller has a defined policy
   for invalid points.

## Core contracts

- **Inputs:** CRS-compatible user inputs or an explicit pipeline; coordinate
  scalars, equal-shaped arrays, point iterables, optional `z` and `t`; optional
  area and operation-selection constraints.
- **Outputs:** transformed `x, y` and optional `z, t` with the input container
  family preserved where supported; an iterator for `itransform`; a four-value
  tuple for `transform_bounds`; operation metadata and group availability
  state for diagnostics.
- **Expected signals:** a transformer has a useful `description`, `definition`,
  `accuracy`, `area_of_use`, and (where supported) `operations`; a group makes
  best and unavailable alternatives visible. A successful numeric result is
  not by itself proof that the desired operation or axis convention was used.
- **Recovery:** first correct CRS/axis/unit assumptions, then inspect operation
  metadata and area of use, then classify missing-grid and data/network issues.
  Escalate data-directory and network changes to the CLI/data route rather than
  silently enabling remote access.

## Focused references

- [`references/api-reference.md`](references/api-reference.md): signatures,
  parameters, return shapes, metadata, and API selection.
- [`references/workflows.md`](references/workflows.md): repeatable workflows
  for CRS conversion, pipelines, arrays/time, bounds, and operation choice.
- [`references/axis-order-and-grids.md`](references/axis-order-and-grids.md):
  axis traps, area and accuracy filters, `TransformerGroup`, and grid policy.
- [`references/troubleshooting.md`](references/troubleshooting.md): symptoms,
  checks, and recovery for invalid results, arrays, pipelines, axes, and grids.

## Publication checks

Before handing this route to a caller, confirm that every transformation has
an explicit coordinate order and unit contract, that any grid-dependent result
records availability and fallback behavior, and that validation covers output
shape plus at least one plausibility or round-trip check. Keep download and
network side effects outside this route unless the caller has separately
approved the CLI/data workflow.
