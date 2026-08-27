# Tensorpack DataFlow API Reference

This reference distills verified Tensorpack 0.11 public API signatures and
source-confirmed behavior for data pipeline work. Prefer these facts over
memory. If a signature is not shown here, inspect the installed package in the
user environment before using it.

## Import map

```python
from tensorpack.dataflow import (
    DataFlow, FakeData, DataFromList, DataFromGenerator,
    MapData, MapDataComponent, BatchData, RepeatedData, PrintData,
    MultiProcessRunnerZMQ, MultiThreadRunner,
    MultiThreadMapData, MultiProcessMapData, MultiProcessMapDataZMQ,
    LMDBSerializer, NumpySerializer, TFRecordSerializer, HDF5Serializer,
    TestDataSpeed, AugmentImageComponent,
)
from tensorpack.dataflow import dataset, imgaug
from tensorpack.input_source import (
    FeedInput, QueueInput, StagingInput, TFDatasetInput, TensorInput, ZMQInput,
)
```

`tensorpack.dataflow` itself is pure Python and can be used outside Tensorpack
trainers. `tensorpack.input_source` requires Tensorpack/TensorFlow trainer
context.

## DataFlow object contract

| API | Contract | Gotchas |
| --- | --- | --- |
| `class DataFlow()` | Base class. Implement `__iter__()`; optionally implement `__len__()` and override `reset_state()`. | A datapoint should be a list or dict of components. Dict datapoints are only partially supported by wrappers. |
| `__iter__(self)` | Yields one list/dict datapoint at a time. May be finite or infinite. | Many DataFlows are non-reentrant: do not call `iter(df)` a second time before the previous iterator finishes. Create separate instances if two consumers need the same source. |
| `__len__(self)` | Optional rough size. Used for default `steps_per_epoch`, progress bars, and fixed inference iteration counts. | Size may be inaccurate after filtering, dynamic sampling, buffering, or parallelism. If validation/inference depends on exact size, the user is responsible for making it exact. |
| `reset_state(self)` | Must be called once, in the process that will use the DataFlow, before `__iter__()`. Initializes RNG and worker/process state. | A DataFlow is not fork-safe after `reset_state()`. Tensorpack `InputSource` and built-in forking DataFlows call it for their workers; manual standalone use must call it explicitly. |
| `RNGDataFlow.reset_state()` | Initializes `self.rng` as a NumPy `RandomState` with process-distinct seed. | Use `RNGDataFlow` for custom sources/wrappers that need randomness. |

Minimal source DataFlow:

```python
class MyData(DataFlow):
    def reset_state(self):
        # Optional: initialize RNG, file handles, worker-local state.
        pass

    def __iter__(self):
        for record in records:
            yield [record.image, record.label]

    def __len__(self):
        return len(records)   # Only if this is meaningful and stable.
```

## Core sources and wrappers

| Object | Verified signature | Role | Gotchas |
| --- | --- | --- | --- |
| `FakeData` | `(shapes, size=1000, random=True, dtype='float32', domain=(0, 1))` | Synthetic list datapoints with one component per shape. Useful for speed checks and smoke tests. | `random=True` generates values every iteration and can itself be expensive. `random=False` reuses a generated datapoint copy. |
| `DataFromList` | `(lst, shuffle=True)` | Wraps a Python list of datapoints; implements length. | With `shuffle=True`, call `reset_state()` so its RNG is initialized. |
| `DataFromGenerator` | `(gen)` | Wraps an iterable or a callable returning an iterable. | Public docs say it does not have reliable length; source attempts `len(self._gen)`, which fails for ordinary generator functions. |
| `MapData` | `(ds, func)` | Applies `func(datapoint)` to every datapoint. Return `None` to drop/filter a datapoint. | Do not mutate input datapoints in place unless safe; filtering can make `__len__()` inaccurate. |
| `MapDataComponent` | `(ds, func, index=0)` | Applies `func` to one list index or dict key, shallow-copies the datapoint, and replaces that component. | Return `None` to drop the datapoint. For tuples, output is converted to list so the component can be replaced. |
| `BatchData` | `(ds, batch_size, remainder=False, use_list=False)` | Groups datapoints into batches. Components are stacked on a new leading dimension by default. | Same-shape scalar/array/string components are expected unless `use_list=True`. Use `remainder=True` only when `len(ds)` is accurate. |
| `RepeatedData` | `(ds, num)` | Repeats a finite DataFlow `num` times; `num=-1` repeats forever. | Infinite repeats have no length and raise `NotImplementedError` from `__len__()`. Useful before trainer inputs that need infinite data. |
| `PrintData` | `(ds, num=1, name=None, max_depth=3, max_list=3)` | Identity proxy that prints type, shape, dtype, and range for the first datapoints. | Use for debugging component shape/range issues. It only prints when datapoints are actually pulled. |
| `TestDataSpeed` | `(ds, size=5000, warmup=0)` | Benchmarks iteration speed with optional warmup and progress bar. | Do not infer full training bottlenecks from the first iterations. Benchmark DataFlow alone before tuning it. |

## Parallel runners and mappers

| Object | Verified signature | Pattern | Correctness and performance notes |
| --- | --- | --- | --- |
| `MultiProcessRunnerZMQ` | `(ds, num_proc=1, hwm=50)` | Forks `num_proc` independent copies of a DataFlow and collects results through ZeroMQ. | `num_proc=1` preserves input order. `num_proc>1` preserves only distribution for i.i.d. stochastic training; it can duplicate and reorder datapoints. Fork happens in `reset_state()`, so fork before creating unsafe sessions. ZMQ is not thread-safe; avoid concurrent iteration. Not supported on Windows. |
| `MultiThreadRunner` | `(get_df, num_prefetch, num_thread)` | Creates independent DataFlow instances in threads and collects with a queue. | `get_df` must return a fresh DataFlow per thread unless the DataFlow is stateless. Subject to Python GIL; still duplicates/reorders when multiple independent workers are used. |
| `MultiThreadMapData` | `(ds, num_thread=None, map_func=None, *, buffer_size=200, strict=False)` | One master iterates `ds`; threads run the mapping function in parallel. | Preserves set semantics better than runner-style parallelism but not ordering. `strict=True` guarantees the same finite set as `MapData` if iterated to `StopIteration`; undefined for infinite sources. |
| `MultiProcessMapData` | `(ds, num_proc=None, map_func=None, *, buffer_size=200, strict=False)` | Alias/variant of ZMQ process mapper. | Use for CPU-bound Python or OpenCV transforms when serialization overhead is acceptable. Mapping function must be picklable on spawn-based platforms. |
| `MultiProcessMapDataZMQ` | `(ds, num_proc=None, map_func=None, *, buffer_size=200, strict=False)` | Process mapper with ZeroMQ pipe. | Same semantics as `MultiProcessMapData`: reordered outputs, strict finite-set option, IPC overhead. |

Decision shortcut: runner = run many copies of the whole DataFlow; mapper = run
only the expensive map step in parallel. Use runner for stochastic training
sources with enough worker randomness. Use mapper for validation or finite-set
processing where the source should be iterated once.

## Serializers

| Serializer | Verified methods | Optional dependency | Role and gotchas |
| --- | --- | --- | --- |
| `LMDBSerializer` | `save(df, path, write_frequency=5000)`; `load(path, shuffle=True)` | `lmdb` | Recommended for large sequential-read datasets. Keys are indices and values are Tensorpack-serialized datapoints. `load(..., shuffle=False)` preserves stored order. If deserialization is the bottleneck, read raw LMDB datapoints and deserialize in a parallel mapper. |
| `NumpySerializer` | `save(df, path)`; `load(path, shuffle=True)` | NumPy | Writes the whole DataFlow into a compressed `.npz` object array. Simple but memory-heavy and much slower than LMDB/TFRecord for large datasets. |
| `TFRecordSerializer` | `save(df, path)`; `load(path, size=None)` | TensorFlow | Stores Tensorpack-serialized bytes in a TFRecord file. TFRecord has no random access and no size metadata; pass `size` to get a length-aware DataFlow. |
| `HDF5Serializer` | `save(df, path, data_paths)`; `load(path, data_paths, shuffle=True)` | `h5py` | Writes each datapoint component to the corresponding HDF5 dataset path. `data_paths` length must match datapoint component count. Not lazy/performance-oriented; prefer LMDB for large pipelines. |

Optional dependencies are guarded by dummy classes in Tensorpack: if a dependency
is unavailable, constructor or class attribute access raises an import-focused
error such as "Cannot import 'lmdb', therefore 'LMDBSerializer' is not
available". Use the bundled smoke script from the parent skill to test installed
availability with tiny data.

## Dataset loaders and layouts

| Loader | Verified signature | Output | Layout/dependency notes |
| --- | --- | --- | --- |
| `dataset.Mnist` | `(train_or_test, shuffle=True, dir=None)` | `[image, label]`; image is `28x28` float in `[0, 1]`; label is int. | `train_or_test` is `'train'` or `'test'`. If files are missing, loader may download into Tensorpack's dataset cache unless a prepared `dir` is supplied. |
| `dataset.Cifar10` | `(train_or_test, shuffle=None, dir=None)` | `[image, label]`; image is `32x32x3` in `[0, 255]`; label is int. | Defaults to shuffling training. `dir` should contain/extract CIFAR Python batches. |
| `dataset.SVHNDigit` | `(name, data_dir=None, shuffle=True)` | `[img, label]`; image is `32x32x3` in `[0, 255]`; label is `0..9`. | `name` is `'train'`, `'test'`, or `'extra'`. Requires `scipy.io`; missing `.mat` files may trigger download. |
| `dataset.ILSVRC12` | `(dir, name, meta_dir=None, shuffle=None, dir_structure=None)` | `[image, label]`; image is uint8 `H x W x 3` BGR; label is `0..999`. | `dir` contains split subdirectories. `name` is `'train'`, `'val'`, or `'test'`. Requires OpenCV. Validation directory may be original flat layout or train-like class subdirectories. |
| `dataset.ILSVRC12Files` | `(dir, name, meta_dir=None, shuffle=None, dir_structure=None)` | `[filename, label]` instead of decoded image. | Use when `cv2.imread`/decode should happen in a parallel mapper. Same layout rules as `ILSVRC12`. |
| `dataset.ILSVRCMeta` | `(dir=None)` | Metadata helper for synset words, synsets, image lists, and ImageNet mean. | May acquire Caffe-style metadata if missing. Keep user answers explicit about dataset/metadata availability. |

`ILSVRC12` training layout expects `dir/train/<synset>/*.JPEG`. Validation can
be original flat `dir/val/*.JPEG` with metadata mapping, or a train-like
`dir/val/<synset>/*.JPEG` layout when `dir_structure='train'`.

## Image augmentation API

| Object | Verified signature | Role and gotchas |
| --- | --- | --- |
| `imgaug.AugmentorList` | `(augmentors)` | Applies a list of image augmentors in order. `reset_state()` resets every child augmentor. `get_transform(img)` returns a deterministic transform list that can be replayed on related images/coordinates. |
| `imgaug.Flip` | `(horiz=False, vert=False, prob=0.5)` | Random horizontal or vertical flip. Exactly one of `horiz`/`vert` must be true. Coordinate transforms use `(x, y)` coordinates. |
| `imgaug.Resize` | `(shape, interp=1)` | Resize to target `(h, w)` or scalar shape using OpenCV interpolation code. |
| `imgaug.ResizeShortestEdge` | `(size, interp=1)` | Resize while preserving aspect ratio so the shortest edge equals `size`. |
| `imgaug.CenterCrop` | `(crop_shape)` | Center crop to `(h, w)` or scalar shape; input image must be at least that large. |
| `imgaug.GoogleNetRandomCropAndResize` | `(crop_area_fraction=(0.08, 1.0), aspect_ratio_range=(0.75, 1.333), target_shape=224, interp=1)` | ImageNet-style random crop/resize; falls back to shortest-edge resize plus center crop after failed random attempts. |
| `imgaug.ToFloat32` | `()` | Converts image to float32. Useful before chained photometric augmentors to avoid repeated casting. |
| `imgaug.ToUint8` | `()` | Clips to `[0, 255]` and converts to uint8. Useful to reduce IPC/network/copy overhead. |
| `imgaug.Contrast` | `(factor_range, rgb=None, clip=True)` | Applies `x = (x - mean) * factor + mean`; `rgb=None` uses per-channel mean, otherwise converts using RGB/BGR setting. |
| `imgaug.BrightnessScale` | `(range, clip=True)` | Multiplies image values by a random factor sampled from `range`. |
| `imgaug.RandomOrderAug` | `(aug_lists)` | Applies augmentors in randomized order. Useful for photometric policies. |

Design rules:

- Image augmentors expect uint8 images in `[0, 255]`, or floating images in
  `[0, 1]` or `[0, 255]`.
- `augmentor.get_transform(img)` samples randomness and returns a deterministic
  `Transform`; call `apply_image()` on the image and `apply_coords()` on Nx2
  float coordinates to keep annotations aligned.
- `augmentor.augment(img)` is shorthand when no replay is needed.
- `AugmentImageComponent(ds, augmentors, index=0, copy=True,
  catch_exceptions=False)` wraps a DataFlow and automatically resets augmentor
  RNG in its `reset_state()`.
- Use `copy=False` only when in-place augmentation of the original component is
  safe for the pipeline.

## InputSource bridge to trainers

| InputSource | Verified signature | Use | Gotchas |
| --- | --- | --- | --- |
| `FeedInput` | `(ds, infinite=True)` | Iterates a DataFlow and feeds placeholders. | Slow for large datapoints. Reuses placeholders after first `get_input_tensors()` and cannot support data-parallel training. |
| `QueueInput` | `(ds, queue=None)` | Enqueues DataFlow datapoints into a TensorFlow queue on CPU; model dequeues tensors. | Default FIFO queue size is 50. Trainer logs queue-size moving summary; near-zero means input is bottleneck. |
| `StagingInput` | `(input, nr_stage=1, device=None)` | Wraps a feed-free input and prefetches tensors into a TensorFlow `StagingArea`, often on GPU. | Cannot wrap `FeedInput`; cannot be nested; not suitable for `InferenceRunner`; multi-GPU runs must fetch all staged tensors together. |
| `TFDatasetInput` | `(dataset)` | Uses a `tf.data.Dataset` or converts a DataFlow to `tf.data.Dataset`. | Training dataset/DataFlow must be infinite, e.g. `.repeat()` or `RepeatedData`. Conversion supports list datapoints and resets the DataFlow. |
| `TensorInput` | `(get_tensor_fn, size=None)` | Uses tensors produced by a user function under `TowerContext`. | `get_tensor_fn` must return a list/tuple matching model input signature. Size is optional; undefined size raises `NotImplementedError`. |
| `ZMQInput` | `(end_point, hwm, bind=True)` | Receives tensors from a ZeroMQ endpoint using external `zmq_ops`. | Requires `zmq_ops` and a sender using the matching Tensorpack ZMQ dataflow format. |

Trainer bridge shortcut: for normal Tensorpack training from Python DataFlow,
start with `QueueInput(df)`. Add `StagingInput(QueueInput(df), device=...)` only
when copy latency to the accelerator is measurable. Use `FeedInput` mainly for
small debugging tasks.
