# Workflow API reference

This reference is a compact operating contract for Earth2Studio 0.18-style
workflow composition. It is deliberately limited to deterministic and
prognostic-plus-diagnostic inference.

## `earth2studio.run`

```python
run.deterministic(
    time: list[str] | list[datetime] | list[np.datetime64],
    nsteps: int,
    prognostic: PrognosticModel,
    data: DataSource,
    io: IOBackend,
    output_coords: CoordSystem = OrderedDict({}),
    device: torch.device | None = None,
    verbose: bool = True,
    checkpoint: Checkpoint | CheckpointSession | NullCheckpoint = NullCheckpoint(),
) -> IOBackend
```

```python
run.diagnostic(
    time: list[str] | list[datetime] | list[np.datetime64],
    nsteps: int,
    prognostic: PrognosticModel,
    diagnostic: DiagnosticModel,
    data: DataSource | ForecastSource,
    io: IOBackend,
    output_coords: CoordSystem = OrderedDict({}),
    device: torch.device | None = None,
    verbose: bool = True,
    checkpoint: Checkpoint | CheckpointSession | NullCheckpoint = NullCheckpoint(),
) -> IOBackend
```

Both functions move models to `device` (`cuda` when available, otherwise
`cpu`, if `device` is omitted), normalize `time`, initialize the IO coordinate
array, fetch initial data, and iterate through `nsteps + 1` states. They write
the initial state at lead time zero and return the supplied IO object. `nsteps`
is a count of model steps, not hours; derive it from the model's lead-time
increment and keep it non-negative and integral.

`run.deterministic` requires a `DataSource` and applies `output_coords` to the
prognostic output at each iteration. `run.diagnostic` accepts a `DataSource`
or `ForecastSource`; it maps the prognostic state to the diagnostic input,
executes the diagnostic, maps to `output_coords`, and writes the diagnostic
fields. The built-in diagnostic path writes direct diagnostic outputs rather
than both intermediate and derived fields.

`checkpoint` can be omitted. With a checkpoint object/session, the workflow
records lead-time progress. A checkpoint with insufficient component state can
warn and rerun from lead time zero; a complete checkpoint can resume or return
immediately when all requested steps have already been written. Do not treat a
partial output store as a complete forecast without checking its metadata.

## Model protocols

A prognostic object need not inherit a concrete base class, but must provide:

```python
prognostic(x, coords) -> (x_next, coords_next)
prognostic.create_iterator(x, coords) -> iterator[(x_step, coords_step)]
prognostic.input_coords() -> CoordSystem
prognostic.output_coords(input_coords) -> CoordSystem
prognostic.to(device) -> PrognosticModel
```

The iterator yields the initial condition first. The model's input coordinate
`lead_time` describes history offsets (often timedeltas), while its output
coordinate lead time describes the next step. Model implementations may keep
state in their iterator.

A diagnostic object must provide:

```python
diagnostic(x, coords) -> (x_derived, coords_derived)
diagnostic.input_coords() -> CoordSystem
diagnostic.output_coords(input_coords) -> CoordSystem
diagnostic.to(device) -> DiagnosticModel
```

Diagnostic models are instantaneous transforms: they do not time-integrate.
The returned tensor and coordinate dictionary must agree in dimension order.
`Identity` is a coordinate-insensitive diagnostic useful for protocol smoke
checks; `Persistence` is a test prognostic that advances by its configured
`dt` and accepts a domain coordinate dictionary.

## Data and coordinate contracts

`DataSource.__call__(time, variable) -> xarray.DataArray` provides analysis or
initial-condition fields. `ForecastSource.__call__(time, lead_time, variable)`
provides fields indexed by both initialization time and lead time.

The run functions internally use:

```python
fetch_data(
    source=data,
    time=time,
    variable=prognostic.input_coords()["variable"],
    lead_time=prognostic.input_coords()["lead_time"],
    device=device,
    interp_to=<model input coords when supported>,
    interp_method=<model interp_method or "nearest">,
)
```

The legacy/default result is `(torch.Tensor, CoordSystem)`. Interpolation is
performed while preparing source data when a target model grid is provided.
For regular 1-D coordinates, `map_coords` can select, roll, or nearest-map
common dimensions. It cannot perform general regular-to-curvilinear mapping;
2-D latitude/longitude cases should be handled by `fetch_data`/data
preparation. A missing output dimension raises `KeyError`; unsupported or
non-present coordinate values can raise `ValueError`.

A `CoordSystem` is an ordered mapping from dimension name to NumPy array.
Order is tensor dimension order. `batch`, `time`, and `lead_time` are treated
as workflow metadata dimensions by the mapper. Common physical dimensions are
`variable`, `lat`, and `lon`; model-specific dimensions also occur.

## Output and IO contract

The workflow calls:

```python
io.add_array(total_coords_without_variable, var_names)
io.write(x, coords, array_name)
```

where `total_coords` includes `time` and a flattened `lead_time` axis with
`nsteps + 1` entries, and `var_names` is the `variable` coordinate. The IO
object must implement `add_array` and `write`; the package exposes these public
backend names:

- `ZarrBackend`
- `AsyncZarrBackend`
- `NetCDF4Backend`
- `XarrayBackend`
- `KVBackend`

This list is not a recommendation matrix. Choose the backend according to the
separate IO requirements; a small in-memory smoke path can use `ZarrBackend()`
without a store path. A workflow returns the same backend instance, so inspect
it or call backend-specific persistence methods after inference.

`output_coords` is an override/filter mapping. Omitted or empty means retain
the model-produced coordinates. A variable restriction controls which arrays
are written. Coordinate restrictions are applied at every step, so use values
that are present or numerically mappable on the produced grid. Do not use an
output coordinate key absent from the model output.

## Model package loading

Auto-loadable model classes expose the class methods:

```python
package = ModelClass.load_default_package()
model = ModelClass.load_model(package)
```

`load_default_package()` returns the default package description; accessing
assets during `load_model()` may download or use a cache. A caller may instead
use `ModelClass.from_pretrained(...)` where that model supports the mixin, but
this sub-skill does not prescribe remote URIs. The selected model's optional
extra, checkpoint licensing, credentials, and hardware must be checked before
running. Never infer that a model is CPU-capable solely because the workflow
accepts `device="cpu"`.

## Output inspection

The built-in examples inspect a Zarr result with `io.root.tree()` and access
arrays by variable name, for example `io["t2m"]`. Backend APIs differ, so
avoid assuming that every backend exposes the same inspection helpers. At a
minimum, verify the expected variable names, time count, lead-time count
(`nsteps + 1`), and spatial coordinate sizes before downstream analysis.
