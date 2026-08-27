# Serialization reference

This reference covers DocArray serialization APIs for `BaseDoc`, `DocList`, `DocVec`, tabular exchange, and FastAPI response routing. For schema construction before serialization, route to sibling [`document-modeling`](../../document-modeling/). For vector indexes and nearest-neighbor search, route to sibling [`vector-indexing`](../../vector-indexing/).

## Verified scope and optional extras

Minimum verified scope: CPU workflows with DocArray base plus `proto`, `pandas`, and `web` extras. The default tensor backend for this skill is `NdArray`. Torch, TensorFlow, JAX, S3, and other external services are optional boundaries and need task-specific verification before relying on them.

Common imports:

```python
from docarray import BaseDoc, DocList, DocVec
from docarray.typing import NdArray
```

Optional extras and when they matter:

| Extra | Install form | Needed for | Boundary |
| --- | --- | --- | --- |
| `proto` | `pip install "docarray[proto]"` | Protobuf methods, protobuf bytes/binary protocols, and `lz4` compression. | Required for the verified protobuf round-trip path. |
| `pandas` | `pip install "docarray[pandas]"` | `to_dataframe()` and `from_dataframe()`. | Verified for CPU tabular workflows. |
| `web` | `pip install "docarray[web]"` | `from docarray.base_doc import DocArrayResponse` and FastAPI response rendering. | Verified only for import/use of the response class, not for serving a production app. |
| `aws` | `pip install "docarray[aws]"` | `s3://` `DocList` stores and `S3DocStore`. | Optional docs-only unless future tasks provide credentials/network. |

Compression names accepted by bytes/binary collection methods are `lz4`, `bz2`, `lzma`, `zlib`, `gzip`, or `None`. `lz4` comes from the `proto` extra; the other listed compressors use Python's standard compression modules.

## Protocol matrix

| Object | JSON | Protobuf | Bytes/base64 | Binary files | Tabular |
| --- | --- | --- | --- | --- | --- |
| `BaseDoc` | `doc.json()` or `doc.to_json()`; restore with `MyDoc.parse_raw(json_str)` or `MyDoc.from_json(json_str)`. | `doc.to_protobuf()`; `MyDoc.from_protobuf(proto_msg)`. | `doc.to_bytes(protocol="protobuf", compress=None)`; `MyDoc.from_bytes(data, protocol="protobuf", compress=None)`. `doc.to_base64(...)`; `MyDoc.from_base64(...)`. | No dedicated `save_binary()` wrapper on `BaseDoc`; use `Path.write_bytes(doc.to_bytes(...))` and `MyDoc.from_bytes(Path.read_bytes(), ...)`. | No CSV/DataFrame methods directly on one `BaseDoc`; wrap a homogeneous batch in `DocList[MyDoc]`. |
| `DocList[MyDoc]` | `docs.to_json()` returns a JSON string; `DocList[MyDoc].from_json(json_data)` accepts `str`, `bytes`, or `bytearray`. Row-oriented JSON list. | `docs.to_protobuf()`; `DocList[MyDoc].from_protobuf(proto_msg)`. | `docs.to_bytes(protocol="protobuf-array", compress=None, show_progress=False)`; `DocList[MyDoc].from_bytes(data, protocol="protobuf-array", compress=None, show_progress=False)`. `to_base64()` and `from_base64()` use the same protocol/compress options. | `docs.save_binary(file, protocol="protobuf-array", compress=None, show_progress=False)`; `DocList[MyDoc].load_binary(file, protocol="protobuf-array", compress=None, show_progress=False, streaming=False)`. | `docs.to_csv(file_path, dialect="excel")`; `DocList[MyDoc].from_csv(file_path, encoding="utf-8", dialect="excel")`. `docs.to_dataframe()`; `DocList[MyDoc].from_dataframe(df)`. |
| `DocVec[MyDoc]` | `vec.to_json()` returns column-oriented JSON; `DocVec[MyDoc].from_json(json_data, tensor_type=NdArray)`. | `vec.to_protobuf()`; `DocVec[MyDoc].from_protobuf(proto_msg, tensor_type=NdArray)`. | `vec.to_bytes(protocol="protobuf-array", compress=None, show_progress=False)`; `DocVec[MyDoc].from_bytes(data, protocol="protobuf-array", compress=None, show_progress=False, tensor_type=NdArray)`. `from_base64(..., tensor_type=NdArray)`. | `vec.save_binary(file, protocol="protobuf-array", compress=None, show_progress=False)`; `DocVec[MyDoc].load_binary(file, protocol="protobuf-array", compress=None, show_progress=False, streaming=False, tensor_type=NdArray)`. | `DocVec` deliberately does not support CSV. Convert with `vec.to_doc_list().to_csv(...)` and load with `DocList[MyDoc].from_csv(...).to_doc_vec()`. DataFrame works with `vec.to_dataframe()` and `DocVec[MyDoc].from_dataframe(df, tensor_type=NdArray)`. |

### Protocol selection rules

- Prefer JSON for human-readable payloads, simple HTTP bodies, and schemas with `Union` fields involving `BaseDoc` subclasses.
- Prefer protobuf or `protobuf-array` for compact verified DocArray round-trips when `docarray[proto]` is installed.
- Use pickle protocols only for trusted Python-only data. Do not unpickle untrusted bytes.
- Use base64 when a bytes payload must travel through a text-only channel. Always pass the same `protocol` and `compress` values on encode and decode.
- Use `save_binary()`/`load_binary()` for durable local binary files. When `streaming=True`, use single-document protocols such as `protocol="protobuf"` or `protocol="pickle"`; whole-array protocols such as `protobuf-array`, `pickle-array`, and `json-array` are loaded as complete arrays.
- File suffixes can override explicit binary protocol/compress choices. For example, a suffix like `.protobuf.gzip` is interpreted as `protocol="protobuf"` and `compress="gzip"`. Pass explicit arguments when the filename is ambiguous.

Important mismatch to avoid: `BaseDoc.to_base64()` defaults to `protocol="protobuf"`, while `BaseDoc.from_base64()` defaults to `protocol="pickle"` in this version. Pass `protocol` explicitly on both sides for every `BaseDoc` base64 round-trip.

## Core examples

### `BaseDoc` JSON, protobuf, bytes, and base64

```python
from docarray import BaseDoc
from docarray.typing import NdArray

class ItemDoc(BaseDoc):
    text: str
    embedding: NdArray[3]

doc = ItemDoc(text="alpha", embedding=[1, 2, 3])

json_payload = doc.to_json()
assert ItemDoc.from_json(json_payload).text == "alpha"

proto_msg = doc.to_protobuf()
assert ItemDoc.from_protobuf(proto_msg).text == "alpha"

wire_bytes = doc.to_bytes(protocol="protobuf", compress=None)
assert ItemDoc.from_bytes(wire_bytes, protocol="protobuf", compress=None).text == "alpha"

wire_text = doc.to_base64(protocol="protobuf", compress=None)
assert ItemDoc.from_base64(wire_text, protocol="protobuf", compress=None).text == "alpha"
```

### `DocList` JSON, protobuf-array bytes, base64, and binary file

```python
from pathlib import Path
from docarray import BaseDoc, DocList

class RowDoc(BaseDoc):
    text: str
    score: int

docs = DocList[RowDoc]([RowDoc(text="a", score=1), RowDoc(text="b", score=2)])

json_payload = docs.to_json()
assert DocList[RowDoc].from_json(json_payload)[1].score == 2

proto_msg = docs.to_protobuf()
assert DocList[RowDoc].from_protobuf(proto_msg)[0].text == "a"

payload = docs.to_bytes(protocol="protobuf-array", compress=None)
assert DocList[RowDoc].from_bytes(payload, protocol="protobuf-array", compress=None)[1].text == "b"

encoded = docs.to_base64(protocol="protobuf-array", compress=None)
assert DocList[RowDoc].from_base64(encoded, protocol="protobuf-array", compress=None)[0].score == 1

path = Path("rows.docs.bin")
docs.save_binary(path, protocol="protobuf-array", compress=None)
assert len(DocList[RowDoc].load_binary(path, protocol="protobuf-array", compress=None)) == 2
```

### `DocVec` with explicit `tensor_type`

`DocVec` deserializers accept `tensor_type=...`. If omitted, the default is `NdArray`, even when the original vector came from another tensor framework.

```python
from docarray import BaseDoc, DocList, DocVec
from docarray.typing import NdArray

class VectorDoc(BaseDoc):
    text: str
    embedding: NdArray[3]

docs = DocList[VectorDoc]([
    VectorDoc(text="a", embedding=[1, 0, 0]),
    VectorDoc(text="b", embedding=[0, 1, 0]),
])
vec = docs.to_doc_vec(tensor_type=NdArray)

payload = vec.to_bytes(protocol="protobuf-array", compress=None)
loaded = DocVec[VectorDoc].from_bytes(
    payload,
    protocol="protobuf-array",
    compress=None,
    tensor_type=NdArray,
)
assert loaded.tensor_type == NdArray
assert loaded.embedding.shape == (2, 3)
```

Use `tensor_type=TorchTensor` or `tensor_type=TensorFlowTensor` only after the matching optional framework is installed and verified. Otherwise keep the verified `NdArray` path.

### CSV and DataFrame exchange

CSV is a row-based scalar exchange format. It is appropriate for homogeneous `DocList` objects whose fields are strings, numbers, booleans, optional scalar values, or nested scalar/URL-like access paths. It is not a reliable tensor or list-like payload format.

```python
from docarray import BaseDoc, DocList, DocVec
from docarray.typing import NdArray

class MetricDoc(BaseDoc):
    label: str
    count: int
    score: float

docs = DocList[MetricDoc]([
    MetricDoc(label="ok", count=2, score=0.5),
    MetricDoc(label="good", count=3, score=0.75),
])

docs.to_csv("metrics.csv", dialect="excel")
assert DocList[MetricDoc].from_csv("metrics.csv")[0].label == "ok"

df = docs.to_dataframe()
assert DocList[MetricDoc].from_dataframe(df)[1].count == 3
assert DocVec[MetricDoc].from_dataframe(df, tensor_type=NdArray).tensor_type == NdArray
```

`DocVec.to_csv()` and `DocVec.from_csv()` raise `NotImplementedError` because `DocVec` is column-oriented. Convert through `DocList` only for scalar-compatible schemas:

```python
vec = docs.to_doc_vec(tensor_type=NdArray)
vec.to_doc_list().to_csv("metrics.csv")
vec2 = DocList[MetricDoc].from_csv("metrics.csv").to_doc_vec(tensor_type=NdArray)
```

## FastAPI response routing

Install the `web` extra and import the response class from `docarray.base_doc`:

```python
from fastapi import FastAPI
from docarray import BaseDoc
from docarray.base_doc import DocArrayResponse
from docarray.typing import NdArray

class InputDoc(BaseDoc):
    text: str

class OutputDoc(BaseDoc):
    embedding: NdArray[3]

app = FastAPI()

@app.post("/embed", response_model=OutputDoc, response_class=DocArrayResponse)
async def embed(doc: InputDoc) -> OutputDoc:
    return OutputDoc(embedding=[0, 0, 0])
```

For `DocList`, type FastAPI parameters and return values as normal Python lists, then convert at the route boundary:

```python
from typing import List
from docarray import DocList

@app.post("/batch", response_class=DocArrayResponse)
async def batch(docs: List[InputDoc]) -> List[OutputDoc]:
    docs = DocList[InputDoc].construct(docs)
    outputs = DocList[OutputDoc]([OutputDoc(embedding=[0, 0, 0]) for _ in docs])
    return list(outputs)
```

Send a `DocList` body with `docs.to_json()` and parse a list response with `DocList[OutputDoc].from_json(response.content.decode())`.

## Protobuf limitations to route around

- Protobuf deserialization does not support `Union` fields involving `BaseDoc` subclasses. Use JSON for schemas such as `Union[TextDoc, ImageDoc]`.
- Basic scalar unions such as `Union[int, str]` can round-trip through protobuf in the covered tests, but mixed document unions should not use protobuf.
- Protobuf dictionary keys must be strings. Non-string dict keys raise during serialization.
- Recursive/cyclic document references raise errors during protobuf conversion.
