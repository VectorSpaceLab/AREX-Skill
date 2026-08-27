# Dataset-writing workflows

These are distilled conversion patterns. They use only source objects and
shard paths that the caller already has; they do not fetch data.

## 1. Preflight and a small indexed smoke file

An indexed source needs `__len__` and `__getitem__`. Its item must be a tuple or
list in the same order as `fields.values()`.

```python
import json
import numpy as np
from ffcv.writer import DatasetWriter
from ffcv.fields import FloatField, IntField

class SmokeDataset:
    def __init__(self, n):
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, index):
        return (index, float(np.sin(index)))

source = SmokeDataset(32)
fields = {"index": IntField(), "value": FloatField()}
sample = source[0]
assert len(source) > 0 and isinstance(sample, (tuple, list))
assert len(sample) == len(fields)
json.dumps(sample[1])  # adapt this check to the actual field schema

writer = DatasetWriter("smoke.beton", fields, num_workers=1)
writer.from_indexed_dataset(source, indices=[0, 1, 2, 3], chunksize=2)
```

The writer's worker code zips `fields.values()` and the sample. It does not
turn a mapping-valued sample into values:

```python
# Wrong: iteration yields "image", then "label".
def bad_item(sample):
    return {"image": sample["image"], "label": sample["label"]}

FIELD_ORDER = ("image", "label")
fields = {"image": image_field, "label": label_field}

def good_item(sample):
    return tuple(sample[name] for name in FIELD_ORDER)
```

Keep `FIELD_ORDER`, mapping insertion order, and the adapter coupled. Validate
several samples in the parent process before starting writer processes; a short
or long tuple can otherwise leave a field unwritten or silently ignore extras.

## 2. Indexed subsets, write order, and chunks

```python
selected = np.array([9, 2, 7, 4], dtype=np.int64)
writer.from_indexed_dataset(
    source,
    indices=selected.copy(),
    chunksize=64,
    shuffle_indices=False,
)
```

`indices` refers to positions in `source`, not destination positions. The file
has four dense destination rows (`0..3`) containing source rows `9, 2, 7, 4`.
`indices=None` becomes `np.arange(len(source))`. With
`shuffle_indices=True`, FFCV shuffles the selected index sequence before
enumerating destination rows; when passing a NumPy array, pass a copy if the
caller must retain the original order because the implementation shuffles it
in place.

`chunksize` is the number of `(destination_index, source_index)` pairs put in a
work chunk. Small chunks improve load balancing for variable-cost samples but
increase queue overhead; large chunks reduce scheduling overhead for cheap,
uniform samples. It does not change the meaning of source or destination
indices.

`shuffle_indices` is write-time persistence order. It is separate from a later
`Loader(order=...)` traversal choice and should not be used as a substitute for
training-time sampling.

## 3. Resource controls after the smoke test

```python
writer = DatasetWriter(
    "train.beton",
    fields,
    page_size=1 << 24,  # 16 MiB; power of two and >= 2 MiB
    num_workers=4,
)
writer.from_indexed_dataset(source, chunksize=256)
```

The writer accepts a power-of-two `page_size` in
`[1 << 21, 1 << 32)`. Each individual allocation must fit in a page; a sample
with several fields must be restartable as a whole when it crosses a page
boundary. Increase the page size for a known large encoded image/byte/array, or
reduce the encoded sample size. More writer processes multiply allocator and
source activity; start at one while diagnosing. `num_workers=-1` uses the
current process CPU affinity.

## 4. Convert already-available WebDataset shards (optional)

The optional `webdataset` package is imported by the writer only when this path
is used. Shards must already exist locally; `/data/already-present/shards` is an
external, caller-provided example path and is not part of this bundle:

```python
from glob import glob
from os import path
from ffcv.writer import DatasetWriter
from ffcv.fields import IntField, RGBImageField

shards = sorted(glob(path.join("/data/already-present/shards", "*.tar")))

def pipeline(dataset):
    # The final object must yield (image, label), not a dict.
    return dataset.decode("rgb8").to_tuple("jpg:png;jpeg", "cls")

fields = {
    "image": RGBImageField(max_resolution=256),
    "label": IntField(),
}
writer = DatasetWriter("train.beton", fields, num_workers=4)
writer.from_webdataset(shards, pipeline)
```

`from_webdataset` first counts each shard by iterating
`pipeline(WebDataset(shard))` through a thread pool, computes cumulative
sample offsets, then sends `(shard, offset)` work to writer processes. The
pipeline therefore must be safe to construct and run repeatedly in workers and
must yield exactly the field arity. Test it against one local shard in the
parent process. Keep `sorted(...)` shard order when reproducible file order is
needed. There is intentionally no network fallback here.

## 5. Structural read-back

```python
from ffcv.reader import Reader

reader = Reader("train.beton")
assert reader.num_samples == expected_count
assert reader.field_names == ["image", "label"]
assert len(reader.handlers) == 2
print(reader.page_size, reader.alloc_table.shape)
```

`Reader.field_names` contains logical descriptor names. In contrast,
`reader.metadata` is built from anonymous structured names (`f0`, `f1`, ...),
so low-level metadata checks use `reader.metadata["f0"]`, not
`reader.metadata["image"]`. For pointer-backed fields, this check proves
pointers and sizes exist; use the appropriate decoder to verify payload content.

A version/build mismatch is rejected by `Reader` before useful read-back. The
current checkout's setup metadata says `1.0.1` while the module reports `1.0.2`,
so validate a file with the same installed build that wrote it.

## 6. JSON and variable bytes through a loader

`JSONField` is stored as a NUL-terminated UTF-8 byte array. The loader's
ordinary byte decoder returns a padded batch, so unpack it explicitly:

```python
from ffcv import Loader
from ffcv.fields import JSONField
from ffcv.fields.basics import IntDecoder
from ffcv.fields.bytes import BytesDecoder

loader = Loader(
    "records.beton",
    batch_size=8,
    num_workers=1,
    pipelines={
        "index": [IntDecoder()],
        "document": [BytesDecoder()],
    },
)
for index, encoded_document in loader:
    documents = JSONField.unpack(encoded_document)
    # Compare documents with the source objects here.
```

`JSONField.unpack` finds the first NUL, decodes UTF-8, and returns one Python
object for a single sample or a list for a batch. In this version,
`JSONField.from_binary` is inherited from `BytesField`, so the reader-side
handler may be a `BytesField`; that does not remove the need to use
`JSONField.unpack` for JSON semantics.

For raw `BytesField`, the decoded batch has the maximum byte length in that
batch. Store a separate `IntField` length or define an unambiguous sentinel if
exact trimming is required. Do not infer each original length from the padded
array shape.

## 7. Custom field registration

A custom field is written with type id 255 because the writer's type table uses
exact classes. Registration is by logical field name when reading:

```python
loader = Loader(
    "captions.beton",
    batch_size=8,
    num_workers=1,
    pipelines={"caption": [StringDecoder()]},
    custom_fields={"caption": StringField},  # class, not instance
)
```

`Reader(path, custom_handlers={"caption": StringField})` is the lower-level
form. The class must be importable in every reader process. First verify that
omitting registration raises the expected `ValueError`; then verify the
registered loader round trip. See [fields-and-formats.md](fields-and-formats.md)
for the `Field` serialization contract and a fixed-width example.
