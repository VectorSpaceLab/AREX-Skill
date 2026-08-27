# Coordinate and data-format patterns

## The ordered coordinate model

Earth2Studio moves `(tensor, CoordSystem)` pairs. A `CoordSystem` is an ordered
mapping from coordinate/dimension names to NumPy arrays. The order describes
tensor axes, so a tensor with shape `(1, 2, 3, 4)` and coordinates ordered as
`time, lead_time, lat, lon` must have lengths 1, 2, 3, and 4 respectively.
Common names include `ensemble`, `time`, `lead_time`, `variable`, `lat`, and
`lon`; these names are conventions, not a promise that every component emits
every dimension.

Use one complete schema for durable output:

```python
from collections import OrderedDict
import numpy as np

coords = OrderedDict({
    "time": np.array(["2024-01-01T00:00"], dtype="datetime64[ns]"),
    "lead_time": np.array([0, 6, 12], dtype="timedelta64[h]"),
    "ensemble": np.arange(2),
    "lat": np.linspace(-90, 90, 4, dtype=np.float32),
    "lon": np.linspace(0, 360, 8, endpoint=False, dtype=np.float32),
})
```

A particular write may contain a subset of values for dimensions that the
backend indexes by coordinate value. The tensor must correspond to that subset
in the same order. Validate uniqueness and intended dtype for index coordinates;
Async Zarr rejects duplicate `parallel_coords` values and scalar (0-D)
coordinates.

For built-in workflows, the output coordinate system normally has `time` and a
`lead_time` sequence containing the initial state plus `nsteps` model steps.
The IO backend may save a restricted `output_coords`; this does not change what
is required to restart a model. Keep the full model state and user-facing saved
fields conceptually separate.

## Array names and the variable axis

Every stored data array has a name. There are two valid layouts:

### Keep `variable` as a dimension

```python
coords = OrderedDict({
    "time": times,
    "lead_time": lead_times,
    "variable": np.asarray(["t2m", "u10m"]),
    "lat": lat,
    "lon": lon,
})
io.add_array(coords, "fields")
io.write(x, step_coords, "fields")
```

The field tensor retains its variable axis and `fields` is the array name.

### Split variables into named arrays

```python
variable_names = coords.pop("variable")
io.add_array(coords, variable_names)
for step in iterator:
    io.write(*split_coords(step_x, step_coords, dim="variable"))
```

Each field has dimensions `time, lead_time, lat, lon` and array names such as
`t2m` and `u10m`. This is convenient for xarray and NetCDF consumers. The
number/order of names returned by `split_coords` must agree with the selected
variable axis.

Do not pass a `variable` dimension to an array that was initialized without
one, and do not change between layouts during restart. A missing data array can
be lazily created by synchronous Zarr, xarray, KV, and NetCDF backends, but
schema creation first is safer and is required to avoid Async Zarr multi-process
creation races.

## Date/time and multidimensional coordinates

Synchronous Zarr and Async Zarr accept NumPy datetime and timedelta arrays.
Async Zarr also normalizes object arrays containing Python `datetime` or
`timedelta` values to datetime64/timedelta64. NetCDF encodes `time` and
`lead_time` using NetCDF units/calendar metadata and converts them back to
NumPy time arrays. Use one representation consistently when reopening a store;
compare values, not only string formatting.

Regular latitude/longitude axes are one-dimensional. A two-dimensional mesh
coordinate is supported by synchronous built-ins through coordinate conversion:
the backend stores one-dimensional index coordinates plus the multidimensional
coordinate arrays and records their dimension mapping. On `write` or `read`,
the multidimensional coordinate must be supplied in full with the same shape as
stored. A sliced mesh coordinate is rejected because its mapping is ambiguous.
NetCDF dimensions themselves remain one-dimensional even when a coordinate
variable is multidimensional.

## Backend/data-format matrix

| Backend | Durable by default | Logical representation | Best fit | Important limit |
| --- | --- | --- | --- | --- |
| `ZarrBackend` | Yes with a path; no with omitted path | Zarr group with coordinate/data arrays | General local Zarr, partial writes, xarray readers | Sync writes can block; explicit schema is safer for restart/distributed use |
| `AsyncZarrBackend` | Yes with `file_name` or `store` | Zarr v3 async group | Iterative/non-blocking local, object-store, and sharded writes | Complete `parallel_coords`; explicit `close`; no general overwrite |
| `NetCDF4Backend` | Yes | One NetCDF4 file | Single-file local output | One-dimensional dimensions; explicit close; no Async Zarr sharding |
| `XarrayBackend` | No | In-memory xarray Dataset | Small in-process Dataset composition | Complete coordinate initialization; persistence is caller's job |
| `KVBackend` | No | Dict of PyTorch tensors | Fast in-memory CPU/GPU staging | Process-local only; use `to_xarray()` to export |

This is a supported-path summary, not an exhaustive backend or storage matrix.
Dependency extras and provider-specific setup are environment concerns; do not
infer that an optional cloud or compression extra is installed.

## Chunking and access pattern

Synchronous Zarr `chunks` should reflect the write/read pattern. A chunk size of
1 on `time`, `lead_time`, or `ensemble` favors step/member slices; full spatial
chunks favor whole-field writes. Explicit compression codecs can reduce storage
and remote transfer but add CPU cost. Benchmark with a tiny representative
fixture before scaling to a full field.

Async Zarr fixes each `parallel_coords` dimension at chunk size 1. Use
`chunked_coords={"lat": ..., "lon": ...}` to split non-parallel dimensions.
`shard_coords` groups those chunks into Zarr v3 objects; it does not alter the
logical array shape or chunk-level reads. Each shard size must be a multiple of
the corresponding chunk size. A trailing shard can be smaller than the nominal
size and is emitted at close.

For distributed writes, make a shard wholly owned by one process. For example,
a rank that owns complete forecasts can shard `lead_time`; sharding the
coordinate split across ranks can silently lose data because each rank may
rewrite a full shard. This is an ownership invariant, not merely a performance
preference.

## Store lifecycle and validation

A safe lifecycle is:

1. Build/inspect `coords` and expected tensor shapes.
2. Create the backend and add arrays/coordinates (one rank for Async Zarr).
3. Write a full tiny slice, then a subset slice.
4. Flush/close, reopen with a fresh object, and read back.
5. Validate shape, coordinate values, dtype, and numerical equality.
6. Only then run a long workflow or hand the store to xarray/post-processing.

For Async Zarr, the store's live metadata is authoritative while arrays are
being created. Final metadata consolidation can be performed after all writes if
needed, but do not rely on a stale consolidated snapshot for a later write.

For safe temporary checks, use a temporary directory and never remove a
user-supplied path implicitly. The bundled `tiny_store_smoke.py` exercises a
small synchronous Zarr store and optional Async Zarr sharding without network,
credentials, model loading, or destructive cleanup outside its temporary
workspace.
