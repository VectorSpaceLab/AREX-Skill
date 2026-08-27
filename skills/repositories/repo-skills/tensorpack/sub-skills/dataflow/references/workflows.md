# Tensorpack DataFlow Workflows

Use these recipes to build, inspect, debug, and optimize Tensorpack data
pipelines without relying on original repository files. All snippets are small
patterns: adapt names, shapes, and directories to the user's project.

## Custom source DataFlow

Use a source `DataFlow` when the user's data format is not already covered by a
built-in dataset loader.

```python
import numpy as np
from tensorpack.dataflow import DataFlow, RNGDataFlow

class MyRecords(RNGDataFlow):
    def __init__(self, records, shuffle=True):
        self.records = list(records)
        self.shuffle = shuffle

    def __len__(self):
        return len(self.records)

    def __iter__(self):
        idxs = np.arange(len(self.records))
        if self.shuffle:
            self.rng.shuffle(idxs)
        for k in idxs:
            rec = self.records[k]
            yield [rec.image, rec.label]
```

Checklist:

1. Yield one datapoint at a time; prefer list components (`[image, label]`) for
   broad wrapper compatibility.
2. Implement `__len__()` only if it is meaningful. If filtering or dynamic
   sampling changes size, either omit it or document that it is approximate.
3. Use `RNGDataFlow` if iteration shuffles or samples randomly.
4. Call `df.reset_state()` before standalone iteration. Tensorpack
   `InputSource` and built-in parallel wrappers call it where they own the
   process.
5. Do not iterate one non-reentrant instance in two places concurrently; create
   two instances or materialize/cache if two consumers need the same data.

For a quick prototype, wrap an existing generator:

```python
from tensorpack.dataflow import DataFromGenerator

def gen():
    for item in records:
        yield [load_image(item.path), item.label]

df = DataFromGenerator(gen)
df.reset_state()
for image, label in df:
    ...
```

## Compose maps, batches, and debug prints

Common composition:

```python
from tensorpack.dataflow import (
    DataFromList, MapData, MapDataComponent, BatchData, PrintData,
)

# Each element is already a datapoint: [path, label].
df = DataFromList(datapoints, shuffle=True)

# Map one component without mutating the original datapoint.
df = MapDataComponent(df, lambda path: decode_image(path), index=0)

# Filter full datapoints by returning None.
df = MapData(df, lambda dp: dp if dp[0] is not None else None)

# Inspect only the first two datapoints when they are pulled.
df = PrintData(df, num=2, max_depth=2, max_list=4)

# Batch fixed-shape components. Use use_list=True for variable-sized images.
df = BatchData(df, batch_size=32, remainder=False)
```

Rules of thumb:

- `MapDataComponent` is safer than manual in-place mutation because it
  shallow-copies and replaces one component.
- Returning `None` from a mapper discards a datapoint and makes length less
  reliable.
- `BatchData(..., use_list=True)` is the right interim step for variable-sized
  raw images before resize/crop transforms make them stackable.
- Use `remainder=True` for validation/inference when the final partial batch is
  required, but only if length is accurate.

## Image augmentation pipeline

Use image augmentors when the transformation maps an image to an image and the
same random transform may need to be replayed on annotations.

```python
from tensorpack.dataflow import AugmentImageComponent
from tensorpack.dataflow import imgaug

train_augs = [
    imgaug.GoogleNetRandomCropAndResize(target_shape=224),
    imgaug.ToFloat32(),
    imgaug.RandomOrderAug([
        imgaug.BrightnessScale((0.6, 1.4)),
        imgaug.Contrast((0.6, 1.4), rgb=False),
    ]),
    imgaug.ToUint8(),
    imgaug.Flip(horiz=True),
]

df = AugmentImageComponent(df, train_augs, index=0, copy=False)
df = BatchData(df, 64)
```

For annotations:

```python
augs = imgaug.AugmentorList([
    imgaug.ResizeShortestEdge(256),
    imgaug.CenterCrop((224, 224)),
])

tfm = augs.get_transform(image)        # samples randomness once
new_image = tfm.apply_image(image)
new_boxes_xy = tfm.apply_coords(boxes_xy.astype('float32'))
```

Important details:

- Tensorpack image datasets such as `ILSVRC12` yield BGR images because they use
  OpenCV decode. Keep RGB/BGR explicit when using contrast/saturation/lighting
  policies or model preprocessing.
- `ToFloat32()` before photometric augmentors avoids repeated casts;
  `ToUint8()` after them reduces copy/IPC size.
- `AugmentImageComponent.reset_state()` resets augmentor RNG. If using
  augmentors manually inside custom subprocesses, call `reset_state()` in that
  subprocess or rely on Python's supported at-fork reset behavior where present.

## Parallelism decision tree

### Pick a pattern

Use a runner when the whole source+map pipeline can be cloned independently:

```python
df = MyRandomTrainingData(shuffle=True)
df = AugmentImageComponent(df, train_augs, copy=False)
df = MultiProcessRunnerZMQ(df, num_proc=8)
df = BatchData(df, batch_size=128)
```

Use a mapper when one master should enumerate the source once, but the expensive
mapping step should run in parallel:

```python
df = DataFromList(file_label_pairs, shuffle=False)
aug = imgaug.AugmentorList(val_augs)

def map_file(dp):
    path, label = dp
    image = decode_image(path)
    return [aug.augment(image), label]

df = MultiThreadMapData(df, num_thread=8, map_func=map_file,
                        buffer_size=1000, strict=True)
df = BatchData(df, batch_size=64, remainder=True)
```

Decision table:

| Need | Prefer | Why |
| --- | --- | --- |
| Stochastic training; data points are i.i.d.; duplicates/reordering acceptable | `MultiProcessRunnerZMQ` or `MultiThreadRunner` | Runs multiple independent DataFlow instances; high throughput with simple code. |
| Validation/test/inference over a finite set | `MultiThreadMapData`/`MultiProcessMapData` with `strict=True`, then batch with `remainder=True` | Preserves finite membership; runner-style cloning can duplicate/reorder samples. |
| CPU-bound Python/OpenCV transform | Process mapper or process runner | Avoids GIL but pays IPC serialization. |
| I/O-bound or OpenCV releases the GIL | Thread mapper first | Lower IPC overhead; benchmark because scaling depends on machine and transform. |
| Existing TensorFlow session/GPU context exists | Avoid forking after the session is created | Forking a live TF/GPU session is unsafe. Build/reset forking DataFlows before session creation. |
| Windows or spawn-only platform | Avoid ZMQ IPC runners; avoid lambdas in process mappers | ZMQ IPC runner does not support Windows; spawn requires picklable global functions. |

### Combine threads and processes carefully

A useful ImageNet-style validation pattern is:

1. `ILSVRC12Files` yields filenames/labels in exact validation set order.
2. `MultiThreadMapData(..., strict=True)` decodes and augments in parallel.
3. `BatchData(..., remainder=True)` forms evaluation batches.
4. `MultiProcessRunnerZMQ(..., 1)` moves the thread pool into one separate
   process to reduce main-process GIL contention without cloning the data source
   multiple times.

The single-process runner preserves order relative to the wrapped mapper's
output stream; the mapper itself may reorder, so use metrics that depend on set
membership, not original ordering, unless you explicitly add order restoration.

## Serialization roundtrips

Use the bundled helper for dependency checks and deterministic tiny roundtrips:

```bash
python sub-skills/dataflow/scripts/dataflow_serializer_smoke.py \
  --workdir <scratch-dir> --formats numpy
python sub-skills/dataflow/scripts/dataflow_serializer_smoke.py \
  --workdir <scratch-dir> --formats lmdb hdf5
python sub-skills/dataflow/scripts/dataflow_serializer_smoke.py \
  --workdir <scratch-dir> --formats all
```

Manual pattern:

```python
from tensorpack.dataflow import LMDBSerializer

source = MyDataFlow(...)
LMDBSerializer.save(source, output_lmdb_path)
loaded = LMDBSerializer.load(output_lmdb_path, shuffle=False)
loaded.reset_state()
for dp in loaded:
    ...
```

Serializer choices:

- Prefer LMDB for large sequential-read datasets, especially when random reads
  from many small files are the bottleneck.
- Use NumPy `.npz` for tiny fixtures or debugging only; it materializes the
  entire DataFlow in memory.
- Use TFRecord when the user needs TFRecord interoperability and accepts no
  random access / explicit size metadata.
- Use HDF5 when the user wants named component datasets and has `h5py`, but do
  not recommend it for high-throughput lazy loading.

For LMDB ImageNet-style encoded storage:

```python
class EncodedImages(DataFlow):
    def __iter__(self):
        for path, label in file_label_pairs:
            with open(path, 'rb') as f:
                encoded = np.asarray(bytearray(f.read()), dtype='uint8')
            yield [encoded, label]

# Use one runner process if you only want to decouple reading from the caller.
LMDBSerializer.save(MultiProcessRunnerZMQ(EncodedImages(), 1), output_lmdb)
```

When reading back, decode bytes in a mapper, locally shuffle if training, then
batch.

## ImageNet-style pipelines

Training pattern for large images:

```python
df = dataset.ILSVRC12(imagenet_dir, 'train', shuffle=True)
df = AugmentImageComponent(df, train_augs, copy=False)
df = MultiProcessRunnerZMQ(df, num_proc=parallel)
df = BatchData(df, batch_size, remainder=False)
```

Why it works: stochastic training accepts distribution-preserving duplication
and reordering, and the full decode+augment source is cloned across workers.

Validation pattern:

```python
df = dataset.ILSVRC12Files(imagenet_dir, 'val', shuffle=False)
aug = imgaug.AugmentorList([
    imgaug.ResizeShortestEdge(256),
    imgaug.CenterCrop((224, 224)),
])

def map_val(dp):
    path, label = dp
    image = decode_bgr(path)
    return [aug.augment(image), label]

df = MultiThreadMapData(df, parallel, map_val, buffer_size=2000, strict=True)
df = BatchData(df, batch_size, remainder=True)
df = MultiProcessRunnerZMQ(df, 1)
```

Why it differs: validation should not fork several independent copies of the
validation reader because that can duplicate or reorder the exact evaluation set.
`ILSVRC12Files` lets decode happen inside the mapper instead of the source.

## TIMIT-style LMDB pattern

For speech or sequence preprocessing where raw files require external feature
extraction:

1. Build a source `DataFlow` that recursively lists user-provided audio files and
   yields `[feature_array, label_array]`.
2. Keep label parsing and feature extraction deterministic.
3. Use `LMDBSerializer.save(ds, output_lmdb)` to freeze preprocessed examples.
4. For statistics, reopen with `LMDBSerializer.load(output_lmdb, shuffle=False)`
   and stream features to an online mean/std accumulator.
5. Document external dependencies and data licensing; do not make the skill
   download proprietary datasets or compiled audio packages.

Skeleton:

```python
class RawSpeech(DataFlow):
    def __len__(self):
        return len(self.files)

    def __iter__(self):
        for wav_path in self.files:
            feat = extract_feature(wav_path)
            label = parse_label_for(wav_path)
            yield [feat, label]

LMDBSerializer.save(RawSpeech(dataset_dir), output_lmdb)
```

## InputSource bridge to trainers

Use this skill to explain the bridge, then route deeper trainer setup to the
training sub-skill.

Typical training:

```python
from tensorpack.input_source import QueueInput, StagingInput

input_source = QueueInput(df)
# Optional if copy-to-device latency matters:
input_source = StagingInput(input_source, nr_stage=1, device='/gpu:0')
```

When to use each source:

- `QueueInput(df)`: default for DataFlow-backed Tensorpack training; hides CPU
  input latency with a TensorFlow queue.
- `FeedInput(df)`: small debug cases only; feeding large datapoints is slow and
  incompatible with data-parallel reuse.
- `TFDatasetInput(dataset_or_df)`: when the user already has `tf.data.Dataset` or
  wants DataFlow converted to `tf.data`. Ensure infinite training data via
  `.repeat()` or `RepeatedData`.
- `TensorInput(get_tensor_fn, size=None)`: for tensors produced in the graph,
  such as TF readers or constants.
- `ZMQInput(endpoint, hwm, bind=True)`: when a separate process/machine sends
  tensors with Tensorpack ZMQ ops; requires the external op package.

## Performance diagnosis

Use observations before changing pipeline structure.

1. If Tensorpack trainer logs show input queue size near zero, the input pipeline
   is the bottleneck. If the queue is nearly full, route model/trainer speed
   issues to training.
2. Replace real data with `FakeData(shapes, random=False)` to benchmark graph
   speed without data loading.
3. Run `TestDataSpeed(df, warmup=50, size=5000).start()` on the DataFlow alone.
4. Remove augmentation; if speed improves enough, preprocessing is the bottleneck.
5. Make the reader return a tiny token after doing its file read; if speed is now
   enough, IPC/copy/serialization was the bottleneck. If not, disk/network/raw
   read is the bottleneck.
6. Try fewer/more mapper workers and change `buffer_size`; benchmark each change
   instead of guessing.
7. If random reads from many compressed files are slow, serialize encoded bytes
   to LMDB and read sequentially.
8. If IPC is the bottleneck, reduce payload size before crossing process/network
   boundaries: keep uint8 or JPEG bytes until decode/normalize must happen.
9. If a distributed preprocessing stage is needed, use Tensorpack's ZMQ dataflow
   conceptually, but document endpoint, high-water mark, and external op/package
   requirements explicitly.

Do not optimize DataFlow until the user can name which component is slow: CPU
augmentation, raw disk read, network storage, Python-to-TF copy, IPC
serialization, or graph/trainer computation.
