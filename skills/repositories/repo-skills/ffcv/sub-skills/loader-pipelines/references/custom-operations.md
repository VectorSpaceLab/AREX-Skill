# Custom `Operation` contracts

Subclass `ffcv.pipeline.operation.Operation` when a transform needs FFCV's
preallocated buffers, Numba compilation, field metadata, or index-aware
execution. A `torch.nn.Module` does not need this class; place it in a pipeline
and Loader wraps it as `ModuleWrapper`.

## Minimum implementation

```python
from dataclasses import replace
from typing import Callable, Optional, Tuple
from ffcv.pipeline.allocation_query import AllocationQuery
from ffcv.pipeline.operation import Operation
from ffcv.pipeline.state import State

class Doubler(Operation):
    def generate_code(self) -> Callable:
        def code(x, dst):
            dst[:x.shape[0]] = x * 2
            return dst
        return code

    def declare_state_and_memory(
        self, previous_state: State
    ) -> Tuple[State, Optional[AllocationQuery]]:
        return previous_state, AllocationQuery(
            previous_state.shape, previous_state.dtype, previous_state.device
        )
```

The constructor of `Operation` initializes `metadata` and `memory_read` to
`None`. During graph collection Loader calls:

- `accept_field(field)` with the source field object;
- `accept_globals(metadata, memory_read)` with that field's metadata and the
  storage-reader callback;
- `declare_state_and_memory(previous_state)` to validate and advance state;
- `declare_shared_memory(previous_state)` and optionally
  `generate_code_for_shared_state()` for state initialized once per epoch/
  operation; and
- `generate_code()` to obtain the callable used at runtime.

`generate_code()` is a factory. It may capture immutable configuration and the
compiler iterator. It must return a callable, not execute the operation during
pipeline construction.

## State contract

`State` fields are:

| Field | Meaning |
|---|---|
| `shape` | Per-sample shape, excluding batch dimension. Use a tuple (the existing implementation also accepts list-like values, but tuple is the safe contract). |
| `dtype` | NumPy dtype while JIT/NumPy, torch dtype once tensor conversion occurs. |
| `device` | Torch device for tensor stages; CPU for the initial NumPy state. |
| `jit_mode` | True only for CPU NumPy/Numba-compatible stages. A JIT state cannot carry a torch dtype or non-CPU device. |

Use `dataclasses.replace(previous_state, ...)`; do not mutate the incoming
state. Decoder state starts as CPU/JIT, `uint8`, with unknown shape. A decoder
must establish its actual output shape/dtype. Typical transitions are:

```text
NumPy HWC uint8 CPU/JIT
  -> ToTensor: torch HWC uint8 CPU/non-JIT
  -> ToDevice(cuda): torch HWC uint8 CUDA/non-JIT
  -> ToTorchImage: torch CHW state and BCHW batch view
  -> Convert/Normalize/Module: declared dtype/device as appropriate
```

A shape-changing operation must declare the new shape. A dtype-changing
operation must declare the dtype that its callable returns. A device-changing
operation must allocate or return a result on that device. An incorrect state
can fail far from the operation, often as Numba typing, reshape, device-copy,
or downstream model errors.

## Allocation and callable signatures

`AllocationQuery(shape, dtype, device=None)` asks the graph to create reusable
storage with shape `(batches_ahead + 2, batch_size, *shape)`. A NumPy dtype
produces a NumPy buffer; a torch dtype produces a per-slot torch buffer (with a
best-effort pinned-memory conversion). Return:

- `None` if the operation writes in-place or returns a view/no new storage;
- one `AllocationQuery` for one output buffer; or
- a sequence/tuple of queries when the callable needs multiple buffers.

The operation callable normally receives `(input, allocated_memory)`. A
`with_indices` callable receives `(input, allocated_memory, batch_indices)`.
Decoders have their own `(batch_indices, destination, metadata, storage_state)`
shape. Never allocate a new batch-sized result on every call when the result
can use the supplied buffer.

The iterator slices each allocated operation buffer to the active count before
calling a stage. A final batch can therefore have `len(batch_indices) <
loader.batch_size`. Write only `[:n]`, return only the active slice, and avoid
reading stale rows. For tuple allocations, the iterator recursively slices
each component. If the operation returns a view or input in place, its state
must match that effective result, not the unused destination.

Example shape-changing operation:

```python
class PickTopLeft(Operation):
    def generate_code(self):
        def code(images, dst):
            h, w, c = images.shape[1:]
            dst[:images.shape[0]] = images[:, :h // 2, :w // 2]
            return dst[:images.shape[0]]
        return code

    def declare_state_and_memory(self, previous_state):
        h, w, c = previous_state.shape
        shape = (h // 2, w // 2, c)
        return replace(previous_state, shape=shape), AllocationQuery(
            shape, previous_state.dtype, previous_state.device
        )
```

`AllocationQuery.device=None` is appropriate for NumPy allocations. A torch
buffer must use the target device and a torch dtype. Do not request a torch
allocation while `jit_mode=True`: `State.__post_init__` rejects that
combination.

## JIT and stage boundaries

`Compiler` compiles functions with Numba when enabled. Set
`code.is_parallel = True` only when the implementation is safe for parallel
iteration (each row must not race on shared output/state). Use
`Compiler.get_iterator()` so one-thread mode uses `range` and multi-thread mode
can use `prange`.

The graph groups operations into alternating JIT and non-JIT stages. A native
NumPy stage can be compiled; a torch stage cannot be Numba compiled. `ToTensor`
is normally the first non-JIT boundary. A custom operation that stays in
NumPy must return a JIT-compatible state. A custom torch operation should
return a non-JIT state and must not be placed before `ToTensor`.

Do not capture unsupported Python objects in a compiled callable. If code needs
runtime metadata, use the `accept_globals` values or immutable NumPy arrays.
If operation behavior changes its generated function or state across epochs,
set Loader `recompile=True`; changing only random values does not require
recompilation.

## `with_indices` and deterministic behavior

Set the attribute on the generated callable, not merely on the operation:

```python
class ReplaceFixed(Operation):
    def __init__(self, changed_ids, label):
        super().__init__()
        self.changed_ids = np.sort(np.asarray(changed_ids))
        self.label = label

    def generate_code(self):
        ids = self.changed_ids
        label = self.label
        rng_range = Compiler.get_iterator()
        def code(labels, _, batch_indices):
            for row in rng_range(len(batch_indices)):
                pos = np.searchsorted(ids, batch_indices[row])
                if pos < len(ids) and ids[pos] == batch_indices[row]:
                    labels[row] = label
            return labels
        code.is_parallel = True
        code.with_indices = True
        return code

    def declare_state_and_memory(self, previous_state):
        return previous_state, None
```

The generated graph inspects `code.with_indices` and appends the current
`batch_indices`. These are the actual sample ids selected by traversal,
including a user-supplied subset's ids. This enables stable fixed corruption,
poisoning, or per-example lookup across epochs and order changes. Sort ids and
use `searchsorted` or a compiled lookup rather than Python set membership.

For deterministic random augmentation, derive a stable per-sample or
per-example key from the dataset id plus an explicit experiment seed. Be aware
that the repository's `ImageMixup`/`LabelMixup` deliberately seed from the
last id in a batch, so the result is deterministic for a given batch grouping
but changes when order, subset, rank, or batch size changes. If invariance to
batch grouping is required, write a custom per-index scheme instead. Avoid
calling global `np.random.seed` from parallel rows unless the resulting
sequence/races are explicitly acceptable.

## Shared state

Use `declare_shared_memory(previous_state)` when an operation needs one buffer
or state initializer shared by multiple graph nodes/branches. Return an
`AllocationQuery` (or sequence) and implement
`generate_code_for_shared_state()` with a callable accepting that shared
buffer. The graph tracks operations by object identity and avoids reinitializing
an operation's shared state on every referenced branch. Keep shared mutation
thread-safe and document whether it is per epoch, per loader, or immutable.
Most transforms need neither hook; returning `None` is the safe default.

## Torch modules and `ModuleWrapper`

Any `torch.nn.Module` in a sequence is replaced with `ModuleWrapper(module)` by
`PipelineSpec.accept_decoder`. The wrapper calls `module(inp)` and declares no
state or allocation change. Therefore the module's real output shape, dtype,
device, and allocation behavior must match its declared-input assumptions. The
wrapper is intentionally a thin bridge, not a shape inference layer.

Use a module after `ToTensor`; use `ToDevice` before a module whose parameters
are on CUDA. If a module changes shape or dtype, prefer an explicit custom
operation or verify downstream state/model compatibility carefully. A module on
CPU triggers a graph warning because a torch transform on CPU is usually much
slower than a native operation; the warning is not a correctness failure.

## Failure-resistant custom-op checklist

1. Test the callable directly on a small batch and a one-row partial batch.
2. Assert `State` after each operation, including dtype, layout, device, and
   JIT boundary.
3. Test with `Compiler.set_enabled(True)` and `False` if it can be compiled.
4. Test `drop_last=False`; ensure no stale allocation rows leak into output.
5. If index-aware, reorder a fixed `indices` subset across epochs and assert
   identity-based behavior, not batch-position behavior.
6. If shared, exercise two output branches and assert initialization occurs once.
7. Test both CPU and CUDA paths only when their dependencies/hardware are
   available; retain an explicit optional/block reason otherwise.

## Evidence anchors

- `ffcv/pipeline/operation.py`, `state.py`, `allocation_query.py`, `pipeline.py`,
  `graph.py`, `compiler.py`: contracts, stage grouping, allocation, codegen.
- `ffcv/transforms/module.py`, `ops.py`, `normalize.py`, `mixup.py`,
  `poisoning.py`, `replace_label.py`: representative implementations.
- `docs/ffcv_examples/custom_transforms.rst` and
  `docs/ffcv_examples/transform_with_inds.rst`: custom operation and index
  patterns.
- `tests/test_basic_pipeline.py`, `test_partial_pipeline.py`,
  `test_partial_batches.py`, and `test_image_normalization.py`: executable
  state, partial-output, compile, and device evidence.
