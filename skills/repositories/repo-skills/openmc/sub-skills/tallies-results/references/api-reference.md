# Tally and result API reference

This reference covers the public Python objects used to define tallies and to
read result files. It assumes the base package and its Python dependencies are
importable. A compiled `libopenmc` is not required to construct ordinary tally
objects or to read a compatible statepoint, summary, track, or particle-restart
file, although native transport-generated files and some plotting paths have
additional prerequisites.

## Define a tally and its filters

A typical tally has one or more filters, one or more scores, and optionally a
list of nuclides:

```python
energy = openmc.EnergyFilter([0.0, 1.0, 1.0e6, 2.0e7])
tally = openmc.Tally(
    name="flux by energy",
    filters=[energy],
    nuclides=["U235"],
    scores=["flux"],
    estimator="tracklength",
)
```

Important contracts:

- `Tally` accepts `tally_id`, `name`, `scores`, `filters`, `nuclides`,
  `estimator`, `triggers`, and `derivative`. Duplicate filters, scores, and
  nuclides are rejected by the Python API.
- Valid estimator choices are `analog`, `collision`, and `tracklength`.
  Leaving it unset allows OpenMC to choose an appropriate estimator. Outgoing
  energy, change-in-angle, and scattering-moment cases need an estimator
  compatible with post-collision information; do not override an automatic
  choice without checking the score/filter combination.
- With no explicit nuclide, input tally XML may be empty in that dimension, but
  a statepoint represents the result with one `total` nuclide bin. Inspect the
  reader's `tally.nuclides` rather than assuming the input and output lists are
  textually identical.
- `multiply_density` controls whether reaction-rate scores are multiplied by
  atom density. Preserve it when comparing or combining tallies.
- `higher_moments = True` requests the additional third and fourth accumulated
  moments. Properties such as `sum_third`, `sum_fourth`, `vov`, `skew`, and
  `kurtosis` are meaningful only when the output contains those moments and
  enough realizations.
- A `Trigger` has a type of `variance`, `std_dev`, or `rel_err`, a numeric
  threshold, and optional score selection/zero handling. Document
  `ignore_zeros=True`; it can allow a trigger to pass while zero bins remain.

### Filter selection

Use the filter's constructor rather than treating all bins as the same type.
The following are common choices:

| Need | Public object | Bin/unit contract |
| --- | --- | --- |
| Event domain | `MaterialFilter`, `CellFilter`, `UniverseFilter`, `SurfaceFilter` | IDs of the corresponding input objects |
| Incident energy | `EnergyFilter(values)` | Successive nonnegative, ascending eV edges form adjacent `(low, high)` bins |
| Outgoing energy | `EnergyoutFilter(values)` | Successive nonnegative, ascending outgoing-energy edges; check estimator/score compatibility |
| Spatial field | `MeshFilter(mesh)` | Pass a mesh object; bins are mesh indices, not arbitrary coordinate lists |
| Particle kind | `ParticleFilter(values)` | Particle names, PDG numbers, or supported particle-type values |
| Time | `TimeFilter(values)` | Successive nonnegative, ascending time edges in seconds |
| Birth/instance | `CellBornFilter`, `CellFromFilter`, `DistribcellFilter`, `CellInstanceFilter` | Cell IDs, source/from-cell IDs, instances, or cell-instance pairs |
| Reaction/angle | `ReactionFilter`, polar/azimuthal/cosine/change-in-angle filters | Use each class's reaction or angular bin validation |

Other versions of the public API include mesh-material, mesh-surface, delayed
group, energy-function, particle-production, and specialized phase-space
filters. Confirm the installed API's constructor and score restrictions before
writing a portable recipe. A filter's `shape`, `num_bins`, and `bins` are more
reliable than assumptions about its underlying array type.

A tally's logical result shape is:

```text
(num_filter_bins, num_nuclides, num_scores)
```

`num_filter_bins` is the product of the filter bin counts. The first dimension
is flattened according to filter order and filter strides; it is not necessarily
a mesh's visible `(x, y, z)` order. Inspect `tally.filters`,
`tally.filter_strides`, `tally.nuclides`, `tally.scores`, and `tally.shape` before
indexing or exporting. Use `get_reshaped_data(..., expand_dims=True)` for a
mesh-aware dimension expansion rather than guessing C- or Fortran-order.

Export the tally collection through the input workflow:

```python
openmc.Tallies([tally]).export_to_xml("tallies.xml")
```

A tally XML file alone does not make geometry, materials, source, settings,
executable, or nuclear data valid. Route those concerns to the sibling
model/runtime/data skills.

## Read statepoints and summaries

Use a statepoint as a context manager and disable automatic file association
when provenance is uncertain:

```python
with openmc.StatePoint("statepoint.10.h5", autolink=False) as sp:
    print(sp.version, sp.run_mode, sp.n_realizations)
    tally = sp.get_tally(name="flux by energy")
    mean = tally.mean
    sigma = tally.std_dev
```

`StatePoint` validates the HDF5 `filetype` and the supported major format
version when opened. It lazily reconstructs filters, meshes, tallies, and
optional derivatives. Useful metadata includes `run_mode`, `n_batches`,
`current_batch`, `n_particles`, `n_realizations`, `runtime`,
`global_tallies`, `keff`/`k_generation` where applicable, `source`, `tallies`,
`filters`, `meshes`, and `version`.

Use `sp.get_tally` with `id`, `name`, `scores`, `filters`, `nuclides`,
`estimator`, `filter_type`, and the `exact_filters`, `exact_scores`, and
`exact_nuclides` flags. Default matching is a subset search; enable exact flags
when a partial match could select the wrong tally. A failed lookup raises
`LookupError`.

For result selection:

```python
values = tally.get_values(scores=["flux"], value="mean")
rel_err = tally.get_values(scores=["flux"], value="rel_err")
mesh_data = tally.get_reshaped_data(value="mean", expand_dims=True)
```

Supported values include `mean`, `std_dev`, `rel_err`, `sum`, `sum_sq`, and,
when enabled, `sum_third` and `sum_fourth`. `rel_err` is computed as
`std_dev / mean`; inspect zero and non-finite means before using it. A
`get_pandas_dataframe()` includes filter, nuclide, score, mean, and standard
 deviation columns. Distribcell path columns require a matching summary.

`openmc.Summary(path)` reconstructs geometry/material context from a summary
HDF5 file. It is useful for distribcell paths and geometry-aware dataframes, but
it is not proof that the summary belongs to the statepoint. Open the intended
summary explicitly, compare file version/provenance and geometry/tally IDs, then
call `sp.link_with_summary(summary)`. If association is uncertain, leave the
statepoint unlinked and use ordinary scalar/array tally data only.

## Tally arithmetic, aggregation, and uncertainty

Tally arithmetic requires populated operands. Before applying `+`, `-`, `*`,
`/`, or `**`:

1. Confirm both operands contain results and were loaded from the intended
   statepoint, or attach results with `tally.add_results(statepoint)`.
2. Compare filter types/bins and order, nuclides, scores, shapes,
   `num_realizations`, estimator, and `multiply_density`.
3. Decide whether an entrywise operation, a cross-product, a slice, or a sum is
   intended. Use `can_merge`, `get_slice`, or `summation` to make that choice
   explicit; do not flatten arrays until equal lengths happen to hide a label
   mismatch.
4. Inspect `derived`, labels, shape, mean, and standard deviation after the
   operation.

Scalar arithmetic preserves the tally's labels. Tally-to-tally operations can
combine different nuclide or score dimensions according to the hybrid product
rules, so check the resulting labels and dimensions. The built-in propagated
uncertainty model assumes independent operands. Tallies from the same run are
often correlated, so a propagated ratio uncertainty is not automatically a
rigorous confidence interval. Mask zero or near-zero denominators and report
excluded/non-finite bins.

`Tally.summation` aggregates selected scores, filter bins, or nuclides and can
retain an aggregate filter; `get_slice` selects bins and can remove singleton
filters. The returned object is derived and must be checked as a new labeled
tally. A zero standard deviation may represent zero contribution, identical
batch values, or too few realizations. Negative variance under a square root
can indicate roundoff or inconsistent accumulated moments; preserve raw
moments and diagnose rather than silently clipping.

## Tracks and particle restart

- `openmc.Tracks(path)` returns a list-like collection of `Track` objects.
  `Track.identifier` is `(batch, generation, particle)`. Structured state fields
  include position `r`, direction `u`, energy `E`, time, weight, cell ID,
  cell instance, and material ID. Use `Tracks.filter(...)` or
  `Track.filter(...)` before plotting.
- `Track.plot()`/`Tracks.plot()` require Matplotlib. `Tracks.write_to_vtk(path)`
  requires VTK. Keep the original track HDF5 if optional conversion fails.
- `openmc.Particle(path)` reads one particle-restart record: batch/generation,
  particle ID/type, weight, energy, position, direction, and run metadata. It
  does not restart transport or validate future input/data/build compatibility.

A regular track file, collision-track file, statepoint, summary, and particle
restart have different `filetype` values and version contracts. Select the
matching reader instead of coercing one format into another.

## Plot specifications and result plots

Native geometry plotting is an input/output workflow:

```python
plot = openmc.SlicePlot()
# configure origin, width, pixels, basis, color_by, and optional filename
openmc.Plots([plot]).export_to_xml("plots.xml")
```

`SlicePlot`, `VoxelPlot`, wireframe raytrace, and solid raytrace descriptions
are exported as XML. PNG or voxel output requires a compatible OpenMC
executable and applicable image/native support. `openmc.voxel_to_vtk(...)` is an
optional conversion that imports VTK only when called.

Python result plots use already-read tally arrays or track structured arrays.
For an energy spectrum, derive bin centers/widths from the `EnergyFilter` and
verify that the mean vector has the same bin order. For a mesh map, use the
filter/tally reshape helper and labels, not a guessed square. An empty plot is
an output/data question until the selected bins and input file are verified.
