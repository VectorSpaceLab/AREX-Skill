# Training, subsets, and distributed integration

A Loader is an iterable of already-decoded field outputs. Treat its tuple
schema and device placement as part of the model/training contract rather than
moving every batch opportunistically in the training loop.

## Single-device training

```python
import torch
from ffcv.loader import Loader, OrderOption
from ffcv.fields.decoders import IntDecoder, SimpleRGBImageDecoder
from ffcv.transforms import ToTensor, ToDevice, ToTorchImage, Squeeze

train_loader = Loader(
    'train.beton', batch_size=512, num_workers=8,
    order=OrderOption.RANDOM, seed=0, drop_last=True,
    pipelines={
        'image': [SimpleRGBImageDecoder(), ToTensor(),
                  ToDevice(torch.device('cuda:0')), ToTorchImage()],
        'label': [IntDecoder(), ToTensor(), ToDevice(torch.device('cuda:0')),
                  Squeeze()],
    },
)

for images, labels in train_loader:
    optimizer.zero_grad(set_to_none=True)
    with torch.autocast(device_type='cuda', dtype=torch.float16):
        loss = criterion(model(images), labels)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

If `drop_last=True`, every batch is full, which is useful for fixed-shape
batch statistics and many distributed training setups. If it is false, the
last batch can be smaller; model/loss code and custom operations must accept
that. Do not infer a batch's active length from the allocated buffer shape.

A CPU pipeline can instead return tensors and move them in the loop, but that
forgoes the overlap and pinned-buffer opportunities of `ToDevice`. Choose one
owner for device movement: either pipeline placement or the loop, not both.

`ToTorchImage` is required for conventional image models that expect BCHW.
Its default channels-last result pairs well with a model converted with
`model.to(memory_format=torch.channels_last)`. For labels, scalar decoders
usually emit a trailing singleton dimension; use `Squeeze()` only when the
criterion expects shape `(B,)`.

## Epoch, ordering, and reproducibility

`Loader.__iter__` samples the next traversal epoch, selects the number of
indices implied by `len(loader) * batch_size`, increments `next_epoch`, and
returns an `EpochIterator`. With a fixed explicit seed:

- sequential non-distributed epochs repeat the selected index order;
- random non-distributed epochs use a different NumPy permutation for each
  epoch from `seed + epoch`;
- distributed sequential/random loaders call the sampler's `set_epoch(epoch)`;
- native random transforms remain random unless their implementation ties
  randomness to indices or another explicit key.

Thus a fixed traversal seed alone does not make random crops/flips identical
between epochs. If exact augmentation replay is required, use an index-aware
operation with a stable seed scheme and test it under both sequential and
random orders. If only sample-order reproducibility is required, record the
seed, epoch, subset, rank/world size, and batch size.

`recompile=True` is not a randomness switch. It regenerates graph functions
each epoch and is only needed when an operation's generated code or compile-
time state changes. Normal per-call random transforms do not need it.

## Distributed setup

Construct one loader per distributed rank with the same `.beton` path,
`indices`, batch size, pipeline schema, order, and explicit seed. Initialize the
PyTorch process group before the first distributed iteration. For supported
built-in orders:

```python
# each process has its own local CUDA device
loader = Loader(
    'train.beton', batch_size=128,
    distributed=True,
    order=OrderOption.RANDOM,
    seed=0,
    drop_last=True,
    pipelines=rank_local_pipelines,
)
```

`Random` uses `DistributedSampler(shuffle=True, seed=seed, drop_last=False)`;
`Sequential` uses the same sampler with `shuffle=False`. The sampler pads its
index stream as needed to make rank lengths even because `drop_last=False` is
passed to the sampler; Loader's own `drop_last` then truncates local batches
according to its selected order length. Verify global sample accounting for
your world size and desired epoch policy instead of assuming ordinary
single-process length.

The Loader does not accept a distributed rank/device argument. `ToDevice`
should target the current rank's `torch.device`, commonly selected from
`LOCAL_RANK`; all ranks should otherwise construct equivalent pipeline graphs.
Do not use `OrderOption.QUASI_RANDOM` with `distributed=True`: its constructor
raises `NotImplementedError` before iteration. For a distributed dataset that
is larger than RAM, test sequential or random order with process cache instead
of silently substituting quasi-random behavior.

Use an explicit seed when distributed random order is requested. If omitted,
Loader warns and uses seed `0` specifically to match PyTorch distributed
sampler behavior. Do not let ranks independently generate seeds.

## Subsets and filtering in training

For a known train/validation split, pass the original dataset ids:

```python
train_ids = np.arange(0, 90000, dtype=np.int64)
valid_ids = np.arange(90000, 100000, dtype=np.int64)
train = Loader(path, 512, indices=train_ids, order=OrderOption.RANDOM,
               seed=0, drop_last=True, pipelines=pipelines)
valid = Loader(path, 512, indices=valid_ids, order=OrderOption.SEQUENTIAL,
               drop_last=False, pipelines=pipelines)
```

Index-aware transforms receive those original ids, not `0..len(subset)-1`.
That is essential for fixed poisoning/relabeling and deterministic per-example
augmentation. If a subset is itself shuffled, the ids remain the stable identity
while the batch positions change.

`filter(field_name, condition)` is a convenience scan: it creates a sequential,
non-dropping temporary loader with all other fields disabled, tests the decoded
sample, and returns a new loader with selected ids. It is eager and can be
expensive. The implementation records ids using the temporary batch position,
so prefer explicit ids for already-subsetted or complex distributed data. A
condition should be pure and should not depend on field tuple position from a
multi-field batch; it receives one sample of the chosen field.

## Field tuple schema

The returned tuple is ordered by active pipeline outputs, not necessarily by
all fields in the `.beton` file. Use an explicit `None` to remove unused
outputs, and keep train/eval pipeline dictionaries with the same active order
when zipping loaders or comparing labels. A pipeline that references an
operation result can expose a derived output without decoding another field.

A safe integration pattern is to unpack immediately and assert contracts on a
first batch:

```python
images, labels = next(iter(loader))
assert images.ndim == 4 and images.shape[1] == 3
assert labels.ndim == 1 and labels.shape[0] == images.shape[0]
assert images.device == labels.device
```

For partial validation batches, use `images.shape[0]` for accounting. Do not
use `len(loader) * batch_size` as the actual number of returned samples unless
`drop_last=True`.

## Train/eval differences

Keep decoder shape stable between train and evaluation when the model expects a
fixed resolution. Typical choices are random-resized-crop + native augmentations
for training and center-crop for evaluation. Both should end in the same
`ToTensor`/`ToDevice`/`ToTorchImage` layout and dtype stages. For CIFAR-like
fixed images, the default decoder is valid; for variable-resolution images,
both train and eval pipelines must use a crop decoder.

Set `drop_last=True` for training when incomplete batches would destabilize
batch-dependent operations or distributed step accounting. Set it false for
evaluation when every sample must be scored, and ensure transforms and metrics
handle the final short batch.

## Bounded training verification

Before a long run:

1. Build a tiny `.beton` fixture with a known id field and, if relevant, both
   fixed and variable image records.
2. Run one complete batch through the exact train pipeline; assert shape,
   dtype, device, tuple order, and label alignment.
3. Run one epoch with `drop_last=False` and count ids. Run the train policy with
   `drop_last=True` and verify only the documented tail is omitted.
4. Run two seeded epochs and check order semantics separately from augmentation
   randomness. For distributed jobs, run a small world-size smoke if the
   process group/GPU environment permits; otherwise record it as optional.
5. Only then add autocast, optimizer, scheduler, and model timing.

## Evidence anchors

- `docs/making_dataloaders.rst`, `docs/ffcv_examples/cifar10.rst`, and
  `docs/ffcv_examples/linear_regression.rst`: training patterns, device
  placement, `drop_last`, and large-data integration.
- `ffcv/loader/loader.py`, `epoch_iterator.py`, and
  `ffcv/traversal_order/{sequential,random,quasi_random}.py`: epoch, batching,
  distributed, and device-stream behavior.
- `tests/test_partial_batches.py`, `test_loader_filter.py`, and
  `test_basic_pipeline.py`: output count, filtering, and integration checks.
