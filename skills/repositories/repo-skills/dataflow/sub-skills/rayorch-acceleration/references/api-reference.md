# API reference

## Public surface

| Member | Signature | What it does |
| --- | --- | --- |
| `RayAcceleratedOperator` | `RayAcceleratedOperator(op_cls, replicas=1, num_gpus_per_replica=0.0, env=None)` | Wraps a DataFlow `OperatorABC` class for RayOrch-backed execution. |
| `op_cls_init` | `op_cls_init(*args, **kwargs)` | Stores constructor args for the wrapped operator and returns the same wrapper. |
| `run` | `run(storage, *args, **kwargs)` | Lazily creates Ray actors, shards records into contiguous chunks, runs the wrapped operator, and writes results back to `storage`. |
| `shutdown` | `shutdown()` | Kills all Ray actors held by the wrapper and clears internal state. |
| `__repr__` | `repr(wrapper)` | Shows wrapped class, replica count, and lazy/initialized state. |

## Behavior details
- The wrapper is still an `OperatorABC`, so you can drop it into normal, batched, and stream-batched pipelines.
- `op_cls_init(...)` mirrors the wrapped operator constructor. The IDE should expose the wrapped `__init__` parameters.
- Instance-level `run` keeps the wrapped operator's named `run` parameters. That lets `PipelineABC.compile()` bind `input_*` / `output_*` kwargs correctly.
- Actors are created lazily on first `run()` so pipeline compilation does not pay model-loading cost.
- The wrapper uses contiguous sharding, so deterministic row order is preserved when the wrapped operator is row-independent.
- Inner actor storage is `InMemoryStorage`; the caller's outer `FileStorage` / batched storage is unchanged.
- `num_gpus_per_replica=0.0` is the CPU fallback path. Fractional GPU values such as `0.25` or `0.5` should be stated explicitly when sharing a device.
- `env` is forwarded as a RayOrch runtime environment registry key.
- `shutdown()` is the cleanup boundary. Compiled pipelines already invoke it after each stage; manual scripts should call it themselves.

## Minimal pattern

```python
from dataflow.rayorch import RayAcceleratedOperator

scorer = (
    RayAcceleratedOperator(MyOp, replicas=4, num_gpus_per_replica=0.0)
    .op_cls_init(...)
)
scorer.run(storage=storage.step(), input_key="text", output_key="score")
scorer.shutdown()
```
