# Data Models, Files, and UDF Binding

DataChain stores data as typed signals. A signal can be a scalar Python type or a
Pydantic/DataChain model whose nested fields flatten into database columns while
remaining a logical object in Python.

## Signals and Nested Models

```python
from pydantic import BaseModel
import datachain as dc

class Box(BaseModel):
    x: float
    y: float

class Detection(BaseModel):
    label: str
    confidence: float
    box: Box

def detect(file: dc.ImageFile) -> Detection:
    ...

chain = dc.read_storage("s3://bucket/images/", type="image", anon=True)
chain = chain.map(detection=detect)
```

The logical signal is `detection`. Nested leaves are queryable as dot paths such
as `detection.label`, `detection.confidence`, and `detection.box.x`. Flat exports
use dotted column names. The physical database layer may use backend-specific
flattening, so use the public dot-path API in user code and examples.

Use `dc.DataModel` instead of plain `BaseModel` when you want automatic model
registration and DataChain-specific model metadata:

```python
class ImageSummary(dc.DataModel):
    caption: str
    tags: list[str]
```

## File Signals

`read_storage` produces a `File` signal by default. `type=` selects a subclass:

| `read_storage(type=...)` | Logical file class | Common use |
| --- | --- | --- |
| `"binary"` | `dc.File` | Generic bytes, metadata, unknown formats. |
| `"text"` | `dc.TextFile` | Text files sent to UDFs or LLM text inputs. |
| `"image"` | `dc.ImageFile` | PIL-style image reads and vision LLM/model inputs. |
| `"audio"` | `dc.AudioFile` | Audio metadata/decoding workflows. |
| `"video"` | `dc.VideoFile` | Video metadata/frame workflows. |

A file signal includes metadata such as source, path, size, version, etag,
latest flag, modified time, and location. Read file contents only when the task
requires it.

## Avoid Accidental File Downloads

If a UDF only needs metadata, bind the exact nested fields with `params=`:

```python
import datachain as dc

def extension(path: str) -> str:
    return path.rsplit(".", 1)[-1].lower()

chain = (
    dc.read_storage("s3://bucket/images/", anon=True)
    .map(ext=extension, params=["file.path"])
)
```

This passes a string path into the UDF instead of a `File` object and avoids
opening/downloading the file.

## UDF Output Type Rules

Every `map`, `gen`, and Python `agg` output must have a known type.

Preferred:

```python
def size_kb(size: int) -> int:
    return size // 1024

chain.map(size_kb=size_kb, params=["file.size"])
```

Allowed for `str` lambdas:

```python
chain.map(name=lambda path: path.rsplit("/", 1)[-1], params=["file.path"])
```

Required for non-`str` lambdas:

```python
chain.map(size_kb=lambda size: size // 1024,
          params=["file.size"],
          output={"size_kb": int})
```

For multi-field related outputs, return one model instead of several separate
columns when the values form a logical object.

## `from __future__ import annotations`

Avoid `from __future__ import annotations` in modules that define DataChain UDF
return types. It stringifies annotations and can make schema resolution fail
because DataChain needs the actual class/type object.

## Setup Values and Stateful UDFs

Use `.setup()` for model/client initialization:

```python
import datachain as dc

def embed(text: str, model) -> list[float]:
    return model.encode(text)

(
    dc.read_dataset("chunks")
    .setup(model=lambda: load_embedding_model())
    .settings(parallel=8)
    .map(embedding=embed, params=["chunk.text", "model"])
    .save("chunk_embeddings")
)
```

Stateful `Mapper`, `Generator`, and `Aggregator` classes are useful when setup
and teardown need to live with the UDF object. Prefer ordinary functions plus
`.setup()` when possible.

## Schema Inspection

Use:

```python
print(chain.schema)
print(chain.schema.flatten())
```

The printable schema shows the logical tree. `flatten()` returns public dotted
leaf names. Always verify read-back values when behavior depends on nested
schema persistence or backend conversion; a declared schema alone is not enough
for backend-sensitive changes.
