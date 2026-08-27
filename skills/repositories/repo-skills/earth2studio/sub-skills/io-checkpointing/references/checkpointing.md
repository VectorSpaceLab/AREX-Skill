# Checkpointing and restart reference

`earth2studio.utils.checkpoint.Checkpoint` is a persistent catalog of restart
rows for one logical inference run. It is deliberately independent of the
chosen IO backend: forecast fields remain in Zarr, NetCDF, xarray, or another
store, while the checkpoint records progress metadata and any opt-in component
state. It never copies model weights into the checkpoint.

## Configure a catalog

```python
Checkpoint(
    name: str,
    path: str | Path | None = None,
    mode: Literal["overwrite", "append"] = "overwrite",
    flush_interval: int | None = 1,
    history_size: int | None = None,
    level: Literal[0, 1, 2] = 2,
    rank: int | None = None,
    world_size: int | None = None,
    device: str | torch.device = torch.device("cpu"),
)
```

- `name` identifies the logical run and is included in manifests.
- `path` is the durable checkpoint directory. If omitted, the default is
  `$EARTH2STUDIO_CACHE/checkpoints/<name>`, or
  `~/.cache/earth2studio/checkpoints/<name>` when that variable is unset.
- `mode="overwrite"` retains the latest row for matching labels. Use
  `mode="append"` for row history and optionally cap it with `history_size`.
- `flush_interval=1` commits every accepted `write`; `flush_interval=None`
  leaves writes pending until an explicit `flush()`. It must be positive when
  supplied.
- `level` must be exactly 0, 1, or 2. `device` is where component tensor state
  can be staged before serialization; it is not the inference device selector.
- For distributed execution, rank folders are used when `world_size > 1`.
  Explicit `rank`/`world_size` remove ambiguity; otherwise Earth2Studio attempts
  PhysicsNeMo's manager and then common environment variables.

A checkpoint context is required for clear state binding:

```python
checkpoint = Checkpoint(
    "forecast", path="forecast.checkpoint", mode="append",
    flush_interval=1, history_size=4, level=2,
)
with checkpoint as ckpt:
    run.deterministic(..., io=io, checkpoint=ckpt)
```

With an empty catalog, `with checkpoint` opens a new session. If rows exist it
selects the latest row. For a specific row, use `with checkpoint.select(-1) as
ckpt:` or `select(0)`. `select` supports negative indexing and raises
`IndexError` when the catalog is empty or the position is invalid. `print` or
`repr(checkpoint)` displays row metadata; `checkpoint.catalog` returns committed
entries for the current rank.

## Levels and what they mean

Checkpoint levels are a request to components, not a promise that every model
supports restart:

| Level | Catalog behavior | Intended restart scope |
| --- | --- | --- |
| `0` | Progress and explicit metadata only; no bound component state is serialized. | Track completion, but components restore no state. |
| `1` | Components may serialize state needed for a workflow item, such as an ensemble member. | Restart item/batch boundaries when component support exists. |
| `2` | Components may serialize state needed inside an autoregressive rollout. | Continue a rollout from its saved boundary when the component implements it. |

Always verify the selected model, perturbation, and custom component's
checkpoint support. A level-2 catalog with a non-checkpoint-aware component is
not a level-2 restart guarantee. Built-in deterministic and diagnostic workflows
warn and rerun from lead time zero when a selected checkpoint's catalog level is
below 2. The ensemble workflow uses `completed_ensembles` metadata to skip
finished members; its first incomplete batch may restart from a saved lead time
only when level 2 is available.

## Built-in workflow semantics

`run.deterministic(..., checkpoint=...)`, `run.diagnostic(...,
checkpoint=...)`, and `run.ensemble(..., checkpoint=...)` use the checkpoint
session supplied by the caller. Deterministic and diagnostic runs:

1. Build or reuse the output IO schema.
2. Fetch the normal initial condition.
3. Construct a prognostic iterator; checkpoint-aware components restore their
   state in the active context.
4. Write the successful output slice to IO.
5. Call `ckpt.write(lead_time=current_lead_time)` after that write.
6. Flush before return.

At level 2, a deterministic/diagnostic selected row resumes at
`write_count - 1`, so the already-recorded boundary is not yielded twice. The
normal initial condition is still fetched; the checkpoint does not replace data
source access. A component's iterator is responsible for yielding the next
state. If the selected row already covers the requested horizon, the workflow
returns without another inference step.

For ensemble runs, metadata includes the completed member indices. The workflow
can resume unfinished batches and uses `batch_size` to control members per
batch. Do not assume changing `nensemble`, `batch_size`, coordinate order, or
model state is compatible with an existing catalog; validate explicitly.

## Custom loops and durable boundaries

Write IO first, then record only small restart metadata:

```python
with checkpoint as ckpt:
    for step_coords, values in steps:
        io.write(values, step_coords, "t2m")
        ckpt.write(
            lead_time=step_coords["lead_time"][-1],
            last_complete_index=int(step_coords["lead_time"].shape[0]),
        )
    ckpt.flush()
```

A `write` increments the session `write_count`. It may return a committed
`CheckpointEntry` when `flush_interval` is reached, otherwise `None`. `flush`
commits pending metadata and state atomically; it returns `None` when nothing is
pending. Do not mark a lead time complete before the associated IO write has
succeeded. For non-blocking Async Zarr, call `io.flush()`/`io.close()` before
(or as part of) the boundary so the checkpoint does not get ahead of durable
output.

Checkpoint metadata is for small restart properties, not forecast arrays. It
supports JSON-like scalars/containers, dates and times, NumPy datetime/timedelta
and non-object arrays, Torch tensors/devices/dtypes, NumPy dtypes, and nested
serializable dataclasses. Unsupported objects raise
`CheckpointSerializationError`; object-dtype arrays and non-string dict keys
are not supported. Writes use temporary commit directories and atomic rename;
invalid stale temporary entries are ignored/cleaned on later writes.

## Component state binding

A restartable component binds a dataclass instance:

```python
from dataclasses import dataclass
import torch
from earth2studio.utils.checkpoint import bind_checkpoint_state

@dataclass
class NoiseState:
    rng_state: torch.Tensor | None = None

class RestartableNoise:
    def __init__(self, generator: torch.Generator):
        self.generator = generator
        self.state = bind_checkpoint_state(NoiseState())
        if self.state.rng_state is not None:
            self.generator.set_state(self.state.rng_state)
```

Construct such components *inside* `with checkpoint.select(-1)` when saved
state must affect constructor behavior. Binding before the existing session is
active can restore late and emits a warning because constructor side effects
may already have used default state. `bind_checkpoint_state` returns a proxy;
normal dataclass attributes pass through, while read-only metadata includes
`checkpoint_enabled`, `checkpoint_level`, `checkpoint_state_loaded`,
`checkpoint_metadata`, `checkpoint_lead_time`, `checkpoint_write_count`, and
`device`.

State identity is the fully qualified dataclass type. Binding the same state
type twice in one active session raises `CheckpointStateCollision`; use
separate dataclass types for separate components. Saved state is schema-checked;
changes to state identity, fields, or schema raise
`CheckpointStateSchemaError` rather than silently hydrating incompatible data.

## IO/checkpoint restart recipe

For a deterministic restart, persist both locations and use the same logical
coordinate contract:

1. Preallocate the complete `ZarrBackend`/NetCDF output schema for the final
   requested horizon. A stopped run should leave unwritten slices in that
   schema, not create a shorter replacement store.
2. Create `Checkpoint(name, path=..., mode="append", level=2)` and run inside
   its context. Keep `flush_interval` aligned with the desired durable IO
   boundary.
3. On interruption, close/flush asynchronous IO and preserve both paths.
4. Reopen the IO backend and checkpoint using identical array names and
   coordinate values. Select the intended row, usually `select(-1)`.
5. Construct checkpoint-aware components within the selected context, then run
   the remaining horizon. Validate old and newly written slices independently.
6. For sharded Async Zarr, align the stop/resume boundary to the shard size for
   the fast path. If a partial shard was already flushed, the fresh backend
   detects it and merges new chunks rather than replacing the whole shard.

This recipe does not make an unsupported model restartable and does not repair
an output store whose coordinates, array names, shard geometry, or ownership
changed between runs.
