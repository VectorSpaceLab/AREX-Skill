# Loader and pipeline construction

This reference is the parameter and control-flow catalog for `ffcv.loader.Loader`
and `ffcv.pipeline.PipelineSpec`. It is distilled from the loader, pipeline,
traversal, docs, and basic/partial/filter tests in this checkout. Treat the
installed code as authoritative for version-specific behavior.

## Loader contract

```python
Loader(
    fname, batch_size, num_workers=-1, os_cache=DEFAULT_OS_CACHE,
    order=OrderOption.SEQUENTIAL, distributed=False, seed=None,
    indices=None, pipelines={}, custom_fields={}, drop_last=True,
    batches_ahead=3, recompile=False, order_kwargs={},
)
```

| Parameter | Meaning and operating choice |
|---|---|
| `fname` | Existing FFCV `.beton` file. Its reader metadata determines field names and default decoder classes. |
| `batch_size` | Maximum number of samples passed through every stage and returned. Allocation buffers are sized for this value, while the final batch may be shorter. |
| `num_workers` | Compiler/Numba and PyTorch thread count, not a Python worker-process count. Values `<1` resolve to the current CPU affinity. |
| `os_cache` | Selects OS-backed cache when true, process/page cache when false. Choose with order and memory constraints; correctness is independent of the cache choice. |
| `order` | `OrderOption.SEQUENTIAL`, `RANDOM`, `QUASI_RANDOM`, or a `TraversalOrder` subclass. `QUASI_RANDOM` is rejected for distributed loaders. |
| `distributed` | Makes sequential/random traversal use PyTorch `DistributedSampler` semantics over `loader.indices`. It requires the usual initialized distributed process group when the sampler is iterated. |
| `seed` | Traversal seed. With distributed random order and no seed, Loader warns and chooses `0`; other missing seeds are generated. Set it explicitly for reproducible comparisons. |
| `indices` | Sequence of dataset sample ids to expose. The traversal operates on this selected set, not necessarily `range(num_samples)`. |
| `pipelines` | Mapping from output name to a sequence of operations, `PipelineSpec`, or `None`. Missing field entries use the default decoder + `ToTensor`; `None` disables the field. |
| `custom_fields` | Mapping needed by `Reader` for custom encoded field types and their field classes/decoders. |
| `drop_last` | If true (the default), `len(loader)` and iteration omit the trailing incomplete batch. If false, the final batch is returned with its real length. |
| `batches_ahead` | Bounded queue and ring-buffer look-ahead. It also sizes `batches_ahead + 2` operation buffers and CUDA streams. More overlap costs memory. |
| `recompile` | Regenerate/compile graph code on every `__iter__` call. Keep false for fixed operations; use true when generated implementation/state changes by epoch. |
| `order_kwargs` | Keyword arguments passed when `order` is a custom `TraversalOrder` subclass. Built-in enum values do not use this. |

`FFCV_DEFAULT_CACHE_PROCESS` changes the default cache selection: a truthy
integer selects process cache and otherwise OS cache. Do not depend on the
ambient default in a reproducibility or performance report; record the
resolved value.

## Default versus explicit fields

The loader collects reader handlers in reader order. For every reader field
not disabled or replaced, `Graph` asks the field for its decoder class and
creates a decoder root. `PipelineSpec.accept_decoder` then:

1. accepts an explicit decoder in `PipelineSpec.decoder`, or consumes the first
   transform if it is an instance of the field's decoder class;
2. instantiates the field default decoder if no decoder was supplied;
3. appends `ToTensor()` only for a true default pipeline (a string source with
   no decoder and no transforms); and
4. wraps each `torch.nn.Module` transform in `ModuleWrapper`.

A sequence supplied as `pipelines['field']` becomes
`PipelineSpec('field', decoder=None, transforms=sequence)`. Therefore the
following are distinct:

```python
# field default decoder + ToTensor
Loader(path, 32, pipelines={})

# explicit decoder, then only the listed transforms (add ToTensor yourself)
{'image': [SimpleRGBImageDecoder(), ToTensor(), ToTorchImage()]}

# field is not loaded and is absent from returned outputs
{'unused_label': None}
```

An explicit pipeline that omits `ToTensor` returns a NumPy array when all of its
operations remain in JIT mode. Conversely, an explicit decoder followed by
`ToTensor` returns a CPU torch tensor until `ToDevice` moves it. A pipeline key
may also be a `PipelineSpec`; this is useful when `source` is an operation
reference rather than a field name, but the source operation must resolve
unambiguously in the graph.

The output tuple follows `pipeline_specs` insertion order: reader fields are
added in reader order, then extra custom pipeline names. Disabling fields and
using a subset of named pipelines can therefore change tuple positions; bind
or document outputs by pipeline keys rather than assuming every stored field is
present.

## Decoder-first patterns

For scalar/vector fields use the appropriate field decoder and explicit
conversion:

```python
from ffcv.fields.decoders import FloatDecoder, IntDecoder, NDArrayDecoder
from ffcv.transforms import Squeeze, ToDevice, ToTensor

pipelines = {
    'x': [NDArrayDecoder(), ToTensor(), ToDevice('cuda:0')],
    'y': [FloatDecoder(), ToTensor(), Squeeze(), ToDevice('cuda:0')],
    'class': [IntDecoder(), ToTensor(), Squeeze()],
}
```

For an image, a typical CPU-augmentation/GPU-training pipeline is:

```python
import torch
import torchvision.transforms as transforms
from ffcv.fields.decoders import RandomResizedCropRGBImageDecoder
from ffcv.transforms import (
    Convert, RandomHorizontalFlip, ToDevice, ToTensor, ToTorchImage,
)

image_pipeline = [
    RandomResizedCropRGBImageDecoder((224, 224)),  # decoder first
    RandomHorizontalFlip(),                         # NumPy/JIT CPU
    ToTensor(),
    ToDevice('cuda:0', non_blocking=True),
    ToTorchImage(),                                 # BCHW view/contiguous copy
    Convert(torch.float16),
    transforms.Normalize(mean, std),                # wrapped torchvision module on GPU
]
```

Here `mean` and `std` are caller-supplied per-channel statistics. FFCV wraps
the `torchvision.transforms.Normalize` module automatically after `ToTensor`;
this placement also ensures it receives a BCHW CUDA tensor.


Do not put a NumPy/JIT transform after `ToTensor`, or a GPU transform before
`ToDevice`. See [image-pipelines.md](image-pipelines.md) for decoder and
transform shape details.

## Operation graph and shared stages

The graph starts with one decoder node per field, then one transform node per
listed operation. A `PipelineSpec` whose source is an operation can refer to a
previous operation result; the operation must occur exactly once or graph
construction raises an ambiguity/not-found error. This can expose one decode
or transform result under multiple output names, but it does not create a new
independent copy.

At graph construction, each operation receives its field (`accept_field`) and
field metadata plus the memory reader (`accept_globals`). The graph walks
branches with a `State`, collects per-operation and shared-state allocations,
then groups nodes into alternating JIT and non-JIT stages. Even stages are
compiled by `Compiler` when enabled; torch stages remain Python-callable.

A result is selected by leaf output name. Every callable receives the prior
result and the operation's allocated memory argument; decoders additionally
receive field metadata and storage state. Index-aware operations receive
`batch_indices` as a third/user-visible argument. The exact custom-operation
contract is in [custom-operations.md](custom-operations.md).

## Traversal, subset, and batch semantics

- Non-distributed sequential order returns `loader.indices` as provided.
- Non-distributed random order returns a NumPy permutation generated from
  `seed + epoch`.
- Distributed sequential/random order uses `DistributedSampler` over the
  selected index array and calls `set_epoch(epoch)`. Keep the same selected
  indices and seed on all ranks.
- Quasi-random order shuffles within storage pages and samples among a bounded
  active page set. It needs process-cache page metadata and raises for
  distributed mode.
- `__iter__` takes the next order, truncates it to `len(loader) * batch_size`,
  then chunks it. `drop_last=True` truncates the order to complete batches;
  `drop_last=False` yields the final shorter chunk.
- Allocated ring buffers are full `batch_size` buffers. Graph stages and custom
  transforms must slice outputs to the actual number of indices. The iterator
  selects `buffer[slot][:count]` (recursively for tuples) before calling a
  stage.
- `len(loader)` is floor division for `drop_last=True` and ceiling division
  otherwise. The loader does not report the number of raw dataset records when
  `indices` is a subset.

## Filtering and subsets

Use `indices` when the subset is already known:

```python
subset = np.asarray([0, 4, 9, 20], dtype=np.int64)
loader = Loader(path, batch_size=2, indices=subset,
                drop_last=False, pipelines=pipelines)
```

`loader.filter(field_name, condition)` constructs a temporary sequential,
non-dropping loader that disables every other field, applies the selected
field's pipeline/default pipeline, and tests each sample. It then constructs a
new loader using the original arguments plus the selected sample ids. The
condition receives one decoded sample. Because the temporary scan computes
`sample_id = batch_number * original_batch_size + within_batch_position`, use
`filter` with the normal full dataset indexing contract; for a prefiltered
loader or unusual distributed setup, prefer explicit `indices` and a separate
predicate pass. Filtering is a material scan, not a lazy predicate.

The final filtered loader restores the original order/pipeline/drop policy but
uses the selected ids. A disabled field returns no tuple element; a filter
condition should therefore name a field that is actually available in its
temporary pipeline.

## Construction checklist

Before a run, record: field-to-output mapping; decoder and every transform in
order; intermediate `(shape, dtype, device, jit_mode)`; batch size and whether
partial batches are expected; `indices`; order/seed/distributed; cache mode;
`drop_last`; and whether `recompile` is intentional. Validate one complete
batch, one partial batch when enabled, and at least one complete epoch.
