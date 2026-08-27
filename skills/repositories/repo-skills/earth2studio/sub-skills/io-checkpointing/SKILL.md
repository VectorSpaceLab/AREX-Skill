---
name: io-checkpointing
description: "Select, initialize, validate, and restart Earth2Studio output
  stores with coordinate-safe IO backends and checkpoint catalogs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Earth2Studio IO and checkpointing

Use this skill when a task must persist Earth2Studio forecast, ensemble, or
other workflow outputs, choose an in-memory or disk-backed representation, tune
Zarr chunking/sharding, or restart a partially completed run. It owns
`earth2studio.io` and `earth2studio.utils.checkpoint`; it does not choose model
weights, data sources, or serving deployments.

## Decide the output contract

1. Write down the complete ordered `CoordSystem` (`OrderedDict[str, np.ndarray]`)
   and the tensor shape it describes. Coordinate insertion order is dimension
   order; do not infer or reorder it casually.
2. Give every stored array an `array_name`. If a `variable` axis should become
   separate arrays, remove it from the store coordinates and use
   `earth2studio.utils.coords.split_coords` for each write.
3. Decide whether output must survive process exit, be read by xarray, be a
   single NetCDF file, stay in memory, or overlap model execution with writes.
4. Preallocate the full output schema before a restartable workflow when using
   `ZarrBackend` or `NetCDF4Backend`. Keep a stable coordinate value and name
   contract across runs. See [data formats](references/data-formats.md).

## Choose a backend

- Use `ZarrBackend(path, chunks=..., backend_kwargs=..., zarr_codecs=...)` for
  the general persistent Zarr v3 path, or omit `path` for a process-local
  `MemoryStore`.
- Use `AsyncZarrBackend(path, parallel_coords=..., blocking=False)` when
  iterative `time`, `lead_time`, or `ensemble` slices should be written while
  computation continues. Always call `close()` (or `flush()`) before reading,
  exit, or handing the store to another process.
- Use `NetCDF4Backend(path, backend_kwargs={"mode": "w"})` for a single NetCDF4
  file. Its coordinates are one-dimensional and its `close()` must be called.
- Use `XarrayBackend(coords)` for a complete in-memory xarray Dataset, or
  `KVBackend(device="cpu")`/`KVBackend(device="cuda")` for a tensor dictionary.
  `KVBackend` is not persistent; call `to_xarray()` before external use.

These are alternatives, not interchangeable restart catalogs. Detailed
constructors, optional extras, and backend-specific limits are in [IO reference](references/io-reference.md).

## Initialize and write

Use a tiny coordinate fixture first, then scale it:

```python
from collections import OrderedDict
import numpy as np
import torch
from earth2studio.io import ZarrBackend

coords = OrderedDict({
    "time": np.array(["2024-01-01"], dtype="datetime64[ns]"),
    "lead_time": np.array([0, 6], dtype="timedelta64[h]"),
    "lat": np.arange(2, dtype=np.float32),
    "lon": np.arange(3, dtype=np.float32),
})
io = ZarrBackend("forecast.zarr", chunks={"time": 1, "lead_time": 1})
io.add_array(coords, "t2m")
io.write(torch.zeros(1, 1, 2, 3), {**coords, "lead_time": coords["lead_time"][:1]}, "t2m")
```

For production, make the write tensor shape match the supplied coordinate
subsets, check `array_name` count against tensor count, and verify with
`io.read(subset_coords, name)` or an independent xarray/Zarr reader. Writes use
coordinate values to find indices; missing dimensions and partial multidimensional
coordinates are errors. More layout examples are in [data formats](references/data-formats.md).

## Async, cloud, and sharded output

For `AsyncZarrBackend`, pass the complete value set for every `parallel_coords`
dimension at construction. Those dimensions are written as one-element chunks;
other dimensions can use `chunked_coords`. `add_array(coords, names, dtype=...)`
can establish schema safely before multiple ranks write. In non-blocking mode
inputs are copied, but asynchronous direct `async_write` does not copy them:
do not mutate its tensors until the coroutine completes.

Use `store="s3://..."`, `"gs://..."`, `"file://..."`, a plain local path, an
obstore store, or a constructed writable Zarr store for object-store output.
Credentials and remote configuration belong in the runtime environment or
`store_kwargs`; never put secrets in a skill or script. `fs_factory` remains a
deprecated compatibility path. Sharding packs chunks into fewer objects, but
uses host memory and requires each shard to belong to one process. Align a
process's ownership and restart boundaries with whole shards. See [IO reference](references/io-reference.md)
for the memory and distributed-write rules.

## Checkpoint a workflow

Checkpoint storage is separate from forecast IO. It stores progress metadata and
opt-in component state, not forecast arrays or model weights. For built-in runs,
construct or reopen the persistent output store and use:

```python
from earth2studio.utils.checkpoint import Checkpoint

checkpoint = Checkpoint(
    "forecast", path="forecast.checkpoint", mode="append",
    flush_interval=1, level=2,
)
with checkpoint as ckpt:
    run.deterministic(..., io=io, checkpoint=ckpt)

# In a later process, construct restart-aware components in this context.
with Checkpoint("forecast", path="forecast.checkpoint", level=2).select(-1) as ckpt:
    run.deterministic(..., io=ZarrBackend("forecast.zarr"), checkpoint=ckpt)
```

The built-in deterministic and diagnostic workflows call `ckpt.write` after a
successful IO write and `ckpt.flush()` before returning. Custom loops should
write a small lead-time marker only after the corresponding data write and call
`flush()` at a durable boundary. `with checkpoint` selects the latest row; use
`select(-1)` or `select(0)` to choose a row explicitly. Levels, component
support, serialization, and resume behavior are detailed in [checkpointing](references/checkpointing.md).

## Validate before expensive execution

Run the bundled offline smoke check from any working directory:

```bash
python path/to/io-checkpointing/scripts/tiny_store_smoke.py --help
python path/to/io-checkpointing/scripts/tiny_store_smoke.py
python path/to/io-checkpointing/scripts/tiny_store_smoke.py --async-zarr --shard-size 2
```

It uses a temporary store, tiny coordinates, partial writes, readback, and
optional sharded asynchronous writes; it does not download data, use cloud
credentials, or delete user paths. For a restart trial, deliberately stop after
part of a shard, call `close()`, reopen with the identical complete
`parallel_coords`, and complete the remaining indices. Confirm all earlier and
later slices, not just the final slice. See [troubleshooting](references/troubleshooting.md)
for store/shard mismatch recovery.

## Boundaries and handoff

Do not claim every model/component supports checkpoints, every cloud provider
is configured, or every backend accepts the same coordinate layout. Do not use
level 2 as proof of model restart support: components opt in. Report backend,
store form, complete coordinate contract, chunk/shard plan, checkpoint name/path
(or that it is disabled), flush policy, verification performed, and unresolved
limits. Omit serving clients, model selection, data fetching, and model weight
management; route those tasks to their sibling skills.

- [IO API, backend matrix, and async/cloud/shard details](references/io-reference.md)
- [Checkpoint levels, catalog, state, and resume semantics](references/checkpointing.md)
- [Coordinate, variable, chunk, and data-format patterns](references/data-formats.md)
- [Predictable failures and recovery](references/troubleshooting.md)
- [Safe tiny-store smoke script](scripts/tiny_store_smoke.py)
