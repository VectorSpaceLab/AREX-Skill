# Towhee data structures and conversion contracts

This reference covers the runtime data containers that a Towhee workflow returns or consumes. It is intentionally self-contained; use the public package APIs below rather than depending on a repository checkout.

## Runtime result conversion

A `RuntimePipeline` call returns a Towhee `DataQueue`. For user-facing inspection, wrap the queue with `towhee.DataCollection(result_queue)`:

```python
import towhee

runtime_pipeline = (
    towhee.pipe.input('num')
        .map('num', 'double', lambda x: x * 2)
        .output('num', 'double')
)

result_queue = runtime_pipeline(3)
dc = towhee.DataCollection(result_queue)
row = dc[0]
assert row.num == 3
assert row['double'] == 6
```

Important consumption rule: `DataCollection` materializes rows by reading from the queue. A queue-backed result should be wrapped or converted once, then reuse the `DataCollection`, its list rows, or its dict form for later steps. If a pipeline has `output()` with no schema, or a filter drops all rows, the resulting `DataCollection` is valid but has length `0`.

The result queue also has its own `to_list(kv_format=False)` method after pipeline execution. Use `DataCollection` when you want `Entity` rows, display helpers, or `to_dict()`/`from_dict()` round-tripping; use the queue list only for immediate low-level checks.

## DataCollection API

| API | Contract | Notes |
|---|---|---|
| `towhee.DataCollection(data)` | Public top-level wrapper. Accepts a Towhee result queue or a dict created by `DataCollection.to_dict()`. | Returns the underlying datacollection object. |
| `towhee.datacollection.DataCollection(data)` | Concrete class. | Use this when you need class methods such as `DataCollection.from_dict(...)`. |
| `len(dc)` | Number of materialized rows. | Empty output and filtered output produce `0`. |
| `dc[i]` / `dc[i] = value` | Index row access/mutation. | Normal Python list-style indexing over materialized rows. |
| `iter(dc)` | Iterates `Entity` rows. | Rows expose both attribute and item access. |
| `dc.to_list()` | Returns a Python `list` of row objects. | Rows are `Entity` instances unless manually replaced. |
| `dc.to_dict()` | Returns `{'schema': [...], 'type_schema': [...], 'iterable': [[...], ...]}`. | `type_schema` values are enum names such as `SCALAR` and `QUEUE`. Values must still be serializable if you persist this with plain JSON. |
| `DataCollection.from_dict(data)` | Reconstructs a `DataCollection` from the dict shape above. | Also accepted through `towhee.DataCollection(data)`. |
| `dc.copy(deep=False)` | Shallow copy by default; deep copy with `deep=True`. | Shallow copy preserves row object identity. |
| `dc1 + dc2` | Returns a new `DataCollection` with concatenated rows. | Schemas are expected to match; validate before concatenating different outputs. |
| `dc.prepare_table_data(limit=5)` | Returns `{'headers': schema, 'data': row_values}` for display helpers. | `limit < 0` means all rows. |
| `dc.show(limit=5, tablefmt=None)` | Prints/renders a table. | Chooses HTML in notebooks and console grid outside notebooks unless `tablefmt` is supplied. |

### Serialization pattern

```python
from towhee.datacollection import DataCollection

snapshot = dc.to_dict()
restored = DataCollection.from_dict(snapshot)
assert restored.to_dict() == snapshot
```

`to_dict()` preserves schema, column type names, and row values. It does not convert arbitrary payload objects into plain JSON by itself. For media arrays, model outputs, or other custom objects, either choose a serializer that understands those values or convert payloads to plain Python/numpy-safe forms first.

## Entity rows

`Entity` is a free-schema row object. It stores provided keys as attributes and also supports item lookup:

```python
from towhee.datacollection import Entity

row = Entity(path='a.jpg', score=0.9)
assert row.path == 'a.jpg'
assert row['score'] == 0.9
```

| API | Contract | Common pitfall |
|---|---|---|
| `Entity(**kwargs)` | Create a row with arbitrary attributes. | Attribute names should be valid Python identifiers if you plan to use dot access. |
| `Entity.from_dict(mapping)` | Create a row from a dict. | Values are copied by reference unless they are immutable or copied before passing. |
| `entity.combine(other, ...)` | Updates `entity.__dict__` in place with attributes from each argument. | Returns `None`; do not write `entity = entity.combine(...)`. |
| `str(entity)` | String form of the underlying dict. | Useful for small debugging output, not stable as a storage format. |

Correct combine pattern:

```python
left = Entity(a=1)
ret = left.combine(Entity(b=2), Entity(c=3))
assert ret is None
assert left.b == 2 and left.c == 3
```

## DataLoader

`towhee.DataLoader(data_source, parser=None, batch_size=None)` normalizes an iterable or callable data source before passing data into a pipeline.

| Input | Behavior |
|---|---|
| `data_source` is iterable | Iterates it directly. |
| `data_source` is callable | Calls it with no arguments, then iterates the returned object. |
| `parser` is `None` | Uses each source item unchanged. |
| `parser` is callable | Applies `parser(item)` before yielding or batching. |
| `batch_size is None` | Yields parsed items one by one. |
| `batch_size` is positive int | Yields lists of parsed items, with the final list possibly shorter. |

Example with a single-input runtime pipeline:

```python
import towhee

p = towhee.pipe.input('num').map('num', 'ret', lambda x: x + 1).output('ret')

for num in towhee.DataLoader([{'num': 1}, {'num': 2}], parser=lambda row: row['num']):
    assert p(num).to_list()[0][0] in {2, 3}

for batch in towhee.DataLoader([{'num': 1}, {'num': 2}, {'num': 3}], parser=lambda row: row['num'], batch_size=2):
    for result_queue in p.batch(batch):
        assert result_queue.to_list()[0][0] in {2, 3, 4}
```

## Media ndarray wrappers

Towhee media wrappers are numpy ndarray subclasses with lightweight metadata. They behave like arrays while preserving metadata across normal views/slices.

| Wrapper | Constructor | Metadata properties | Notes |
|---|---|---|---|
| `towhee.types.Image` | `Image(data, mode=None)` | `mode`, `width`, `height`, `channel` | `width = shape[1]`, `height = shape[0]`, `channel = shape[2]` when present, else `1`. |
| `towhee.types.AudioFrame` | `AudioFrame(data, sample_rate=None, timestamp=None, layout=None)` | `sample_rate`, `timestamp`, `layout` | Audio data can be 1-D or shaped like the source decoder output. |
| `towhee.types.VideoFrame` | `VideoFrame(data, mode=None, timestamp=None, key_frame=0)` | `mode`, `timestamp`, `key_frame` | Represents a decoded video frame-like array; metadata survives slicing. |

Basic use:

```python
import numpy as np
from towhee.types import Image, AudioFrame, VideoFrame

img = Image(np.zeros((10, 20, 3), dtype=np.uint8), 'RGB')
assert (img.height, img.width, img.channel, img.mode) == (10, 20, 3, 'RGB')

audio = AudioFrame(np.zeros(16000), sample_rate=16000, timestamp=0, layout='mono')
assert audio.sample_rate == 16000

frame = VideoFrame(np.zeros((8, 8, 3), dtype=np.uint8), mode='RGB', timestamp=100, key_frame=1)
assert frame[:4].mode == 'RGB'
```

### PIL and color conversion helpers

```python
from towhee.types.image_utils import from_pil, to_pil, to_image_color
from towhee.types import arg, to_image_color as to_image_color_preprocessor

# PIL.Image.Image -> towhee.types.Image
img = from_pil(pil_img)

# towhee.types.Image -> PIL.Image.Image
pil_img_2 = to_pil(img)

# Direct color conversion using OpenCV color flags such as COLOR_RGB2BGR.
bgr = to_image_color(img, 'BGR')

# Operator/function argument preprocessor style.
@arg(0, to_image_color_preprocessor('RGB'))
def consume_rgb(img):
    return img
```

Color conversion returns the original object when the source has no `mode` attribute or already has the target mode. Unsupported conversions raise `ValueError`. PIL conversion expects a numpy shape and dtype compatible with the image mode, commonly `uint8` for RGB/RGBA/L images.

## Display behavior

`DataCollection.show(limit=5, tablefmt=None)` builds from `prepare_table_data(limit)`. With `tablefmt=None`, Towhee attempts HTML rendering in notebooks and grid/console rendering elsewhere. Table renderers know about `Image`, `VideoFrame`, and `AudioFrame`, but display output is best treated as a human aid, not a storage contract.
