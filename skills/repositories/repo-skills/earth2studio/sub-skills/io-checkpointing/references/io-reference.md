# IO backend reference

This reference distills the public `earth2studio.io` contract. Import names from
`earth2studio.io`; all built-ins expose at least `add_array(coords, array_name,
...)` and `write(x, coords, array_name)`. `IOBackend` is a runtime-checkable
`Protocol`, so a custom backend need not inherit it.

## Common contract

```python
class IOBackend(Protocol):
    def add_array(
        self, coords: CoordSystem, array_name: str | list[str], **kwargs
    ) -> None: ...
    def write(
        self,
        x: torch.Tensor | list[torch.Tensor],
        coords: CoordSystem,
        array_name: str | list[str],
    ) -> None: ...
```

`coords` is an ordered mapping from dimension name to a one-dimensional NumPy
coordinate array, unless a backend's multidimensional-coordinate support is
being used. Tensor axes follow mapping order. `x` and `array_name` can each be a
single value or a list; list lengths must match. Built-ins also commonly expose
`__contains__`, `__getitem__`, `__len__`, `__iter__`, `coords`, and `read`, but
these are not required by the protocol.

Array names are mandatory because one backend can hold multiple fields. A
common pattern is:

```python
from earth2studio.utils.coords import split_coords

io.write(*split_coords(x, coords, dim="variable"))
```

`split_coords` returns tensors/coordinates/names for one array per variable.
When an array is initialized with a `variable` coordinate instead, retain that
axis and use one name such as `fields`.

## ZarrBackend

```python
ZarrBackend(
    file_name: str | None = None,
    chunks: dict[str, int] = {
        "ensemble": 1, "time": 1, "lead_time": 1, "variable": 1,
    },
    backend_kwargs: dict[str, Any] = {"overwrite": False},
    zarr_codecs: CompressorsLike = None,
)
```

- With no `file_name`, the backend uses a Zarr `MemoryStore`; a path creates a
  local store. `backend_kwargs` are passed to `zarr.group`; `overwrite=True`
  enables the Zarr group/array overwrite behavior where supported.
- `chunks` is keyed by coordinate name. Dimensions absent from the data are
  ignored; unspecified dimensions default to their coordinate length when an
  array is created.
- `add_array(coords, array_name, data=None, **kwargs)` creates coordinate arrays
  and one or more data arrays. `data` may be one tensor, a list, or `None`.
  A missing `data` array uses float32 and a `None` fill value by default. Existing
  arrays are skipped unless `overwrite=True` is passed to the array creation.
- `write(x, coords, array_name)` supports partial writes selected by coordinate
  values and creates a missing data array lazily. Prefer `add_array` first for a
  stable schema and to avoid distributed first-write races.
- `read(coords, array_name, device="cpu")` returns `(tensor, coords)`. The
  requested dimension names must exist. A multidimensional coordinate must be
  present in full and have the same shape as the stored coordinate.
- Values are moved to CPU/NumPy for storage. GPU tensors therefore synchronize
  at this boundary; use `KVBackend(device="cuda")` only when an in-memory GPU
  tensor dictionary is actually intended.

A safe baseline is a persistent path plus explicit chunks for iterative axes:

```python
io = ZarrBackend(
    "forecast.zarr",
    chunks={"time": 1, "lead_time": 1, "lat": 90, "lon": 180},
)
io.add_array(total_coords, ["t2m", "u10m"])
io.write([t2m_step, u10m_step], step_coords, ["t2m", "u10m"])
```

The built-in Zarr backend is the normal choice when datetime/timedelta
coordinates matter. Zarr v3 codecs are optional; compression changes storage
and performance, not the coordinate contract.

## AsyncZarrBackend

```python
AsyncZarrBackend(
    file_name: str | None,
    parallel_coords: CoordSystem,
    fs_factory: Callable | None = None,
    blocking: bool = True,
    pool_size: int = 8,
    async_timeout: int = 600,
    zarr_kwargs: dict[str, Any] = {"mode": "a"},
    zarr_codecs: CompressorsLike = None,
    chunked_coords: dict[str, int] = {},
    shard_coords: dict[str, int] = {},
    max_inflight_shards: int = 4,
    store: str | zarr store | obstore store | None = None,
    store_kwargs: dict[str, Any] = {},
)
```

The exact type union for `store` depends on the installed Zarr/obstore
versions; accepted forms are described below. `file_name` is required unless
`store` is supplied. `parallel_coords` must contain the complete value set for
each index dimension that will be written in parallel. Values must be unique.
The backend fixes those dimensions to chunk size 1. Non-parallel coordinates
are initialized from the first write and must match the complete stored array on
every later write; sliced writes of those coordinates are intentionally not
supported for thread safety.

Public methods with distinct behavior:

- `add_array(coords, array_name, dtype=np.float32, **kwargs)` creates the schema
  up front and is idempotent for distributed setup. It accepts `dtype`, not a
  template data tensor; extra compatibility kwargs are ignored with a warning.
- `write(x, coords, array_name)` prepares/validates inputs and performs a
  synchronous API call. With `blocking=True` it waits. With `blocking=False` it
  schedules work on the loop pool and copies tensors to CPU first so callers may
  reuse/mutate their buffers after the call.
- `async_write(x, coords, array_name)` is the coroutine form. It does not copy
  tensors before the coroutine completes, so do not mutate the input buffers.
- `flush()` drains in-flight writes and emits incomplete shard buffers. `close()`
  calls `flush()` and must be explicit, especially in non-blocking mode.
- `async_flush()` is the coroutine equivalent. `coords` reads the live store;
  `__getitem__` flushes pending writes and is intended for inspection, not a hot
  write loop. The `.store` property exposes the underlying store for optional
  final metadata consolidation.

Async Zarr currently does not support overwriting existing stores as a general
operation. Parallel coordinate arrays in an existing store must exactly match
the constructor values. Establish arrays with one process/rank before concurrent
first writes. Do not use a consolidated-metadata snapshot as the live source for
creation; the backend requires live store membership and forces live metadata.

### Local, remote, and object stores

Preferred examples:

```python
parallel = {"time": times, "lead_time": lead_times}
local = AsyncZarrBackend("forecast.zarr", parallel_coords=parallel)
remote = AsyncZarrBackend(
    None,
    parallel_coords=parallel,
    store="s3://bucket/prefix/forecast.zarr",
    store_kwargs={"region": "us-east-1"},
    blocking=False,
)
```

`store` accepts a plain local path, `s3://`, `gs://`, or `file://` URL resolved
through obstore, an obstore store instance, or an already constructed writable
Zarr store. A read-only store raises `ValueError`. `file_name` and `fs_factory`
are ignored when `store` is supplied. `store_kwargs` is valid only for a URL
string. Credentials are resolved by the runtime store configuration; do not
embed them in code or generated skill files.

`fs_factory` is a deprecated compatibility route for fsspec-backed local or
remote filesystems. If used without `store`, it must be callable; remote
filesystem instances must be asynchronous. Prefer `store` for new cloud code.

### Chunking and sharding

`chunked_coords` chooses chunk lengths for non-parallel dimensions. `shard_coords`
chooses the number of elements per Zarr v3 shard. A shard size must be a positive
multiple of that coordinate's chunk size. A non-parallel dimension is written as
one complete slice, so a shard on it must cover the full dimension; otherwise
add that dimension to `parallel_coords` or increase its shard size.

Sharding reduces object/file count without changing the logical chunk layout.
Each live shard buffer holds the shard in host memory; `max_inflight_shards`
bounds concurrent flushes. A rough per-process planning estimate is:

```text
max_inflight_shards * 4 * prod(shard_shape) * itemsize
    + pool_size * write_bytes
```

This is a planning estimate, not a guarantee. Reduce shard size or
`max_inflight_shards` when memory is tight. A partial final shard is emitted by
`close()` using the array fill value for unwritten positions. A shard already
present in the store takes a read-modify-write merge path; align restart
boundaries to shard boundaries when possible.

Never let two processes own different chunks of the same shard. Each process
buffers and writes a complete shard independently; the later full write can
silently discard another rank's values. Shard along a dimension one process
owns in full (often `lead_time` for a forecast), not the distributed initial
condition dimension. See [checkpointing](checkpointing.md) for restart coupling.

## NetCDF4Backend

```python
NetCDF4Backend(
    file_name: str,
    backend_kwargs: dict[str, Any] = {"mode": "r+", "diskless": False},
)
```

The backend forces `format="NETCDF4"`. Use `backend_kwargs={"mode": "w"}`
when creating a new file. Coordinates are stored as one-dimensional NetCDF
dimensions; time and lead-time values are encoded/decoded with NetCDF units and
calendar metadata. `add_array` accepts optional template tensors and
`write` supports coordinate-selected writes. Use `close()` to release the file.
NetCDF is a single-file alternative, not a replacement for Async Zarr's
non-blocking/object-store/sharding path.

## XarrayBackend and KVBackend

```python
XarrayBackend(coords=OrderedDict({}), **xr_kwargs)
KVBackend(device="cpu")
```

`XarrayBackend` creates an in-memory `xarray.Dataset`; pass the complete
coordinate set when initializing it. `add_array` accepts xarray DataArray
kwargs, and `read(..., dtype=torch.float32, device="cpu")` returns a tensor and
coordinates. `KVBackend` stores tensors in a Python dictionary on the selected
device, creates zero-filled float32 arrays when no template is supplied, and
provides `to_xarray(**xr_kwargs)`. Neither backend persists data by itself.
Both use the same coordinate-value selection and full multidimensional-coordinate
rules as the other synchronous built-ins.

## Minimal validation matrix

For a new output configuration, validate all of the following with tiny arrays:

1. `add_array` creates coordinate and data members with expected shapes.
2. A full write and a subset write round-trip through `read`.
3. Datetime/timedelta coordinates retain their intended dtype/values.
4. Array-name splitting writes independent fields without a variable axis.
5. Async non-blocking output is correct after `close()`; for sharding, test a
   trailing partial shard and a fresh-process restart into that store.
6. Reopen the final store with the intended reader (for example xarray for
   Zarr/NetCDF) before launching a long or remote run.
