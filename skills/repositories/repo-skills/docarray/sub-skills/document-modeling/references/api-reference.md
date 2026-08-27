# Document modeling API reference

This reference covers the public DocArray APIs used to model multimodal data. It is scoped to document schemas, document collections, and tensor typing. For serialization or storage details, route to sibling [`serialization-storage`](../../serialization-storage/). For indexes and vector search, route to sibling [`vector-indexing`](../../vector-indexing/).

## Verified scope and import surface

Minimum verified scope: CPU workflows with DocArray base plus proto, pandas, and web extras. NumPy-backed `NdArray`, `BaseDoc`, `DocList`, `DocVec`, predefined documents, and dynamic document helpers are covered. Torch, TensorFlow, JAX, media loaders, cloud services, and external vector database backends are optional boundaries and require separate verification before relying on them.

Core imports:

```python
from docarray import BaseDoc, DocList, DocVec
from docarray.documents import AudioDoc, ImageDoc, TextDoc, VideoDoc
from docarray.documents.helper import create_doc, create_doc_from_dict
from docarray.typing import AnyEmbedding, AnyTensor, ImageUrl, NdArray
```

Optional tensor framework imports are lazy and require the matching framework to be installed before use:

```python
from docarray.typing import TorchTensor          # requires torch
from docarray.typing import TensorFlowTensor    # requires tensorflow
from docarray.typing import JaxArray            # requires jax
```

## Core classes and helpers

| API | Verified signature or shape | Use for | Key constraints |
| --- | --- | --- | --- |
| `BaseDoc` | `BaseDoc(*, id: Optional[ID] = <factory>)` | Define one document/data-point schema. | Subclass it; fields are Pydantic fields. `id` is optional and auto-generated when omitted. Assignment is validated. |
| `DocList` | `DocList(docs: Optional[Iterable[T_doc]] = None, validate_input_docs: bool = True)` | Mutable row-oriented sequence of documents. | `DocList[MyDoc]` validates homogeneous schemas; bare `DocList` can hold heterogeneous `BaseDoc` values but loses schema-level bulk field access. |
| `DocVec` | `DocVec(docs: Sequence[T_doc], tensor_type=NdArray)` | Column-oriented batch of homogeneous documents for contiguous tensor access. | Must be parameterized as `DocVec[MyDoc](...)`, must be non-empty, and cannot store heterogeneous documents. Optional tensor/doc columns must be all `None` or all present. |
| `create_doc()` | `create_doc("Name", field=(type, default), __base__=BaseDoc, ...)` | Create a `BaseDoc` subclass dynamically. | `__base__` must be `BaseDoc` or a subclass. Required fields use `...` as the default marker. |
| `create_doc_from_dict()` | `create_doc_from_dict(model_name, data_dict)` | Infer a dynamic schema from example values. | Empty dictionaries raise `ValueError`. Fields whose example value is `None` become `Any`, so tighten those manually if needed. |
| `NdArray` | `NdArray`, `NdArray[dim, ...]`, `NdArray[2, "x", "x"]` | NumPy-backed tensor fields with optional shape validation. | Shape mismatches may be reshaped when possible; impossible mismatches raise validation errors. |
| `AnyTensor` | `AnyTensor` or `AnyTensor[shape]` | Framework-agnostic tensor field. | Use `DocVec(..., tensor_type=...)` when batching ambiguous tensor fields. |

## `BaseDoc` behavior

`BaseDoc` is a specialized Pydantic model. Use normal type hints to declare fields:

```python
from typing import Optional
from docarray import BaseDoc
from docarray.typing import ImageUrl, NdArray

class ProductDoc(BaseDoc):
    title: str
    image_url: Optional[ImageUrl] = None
    embedding: NdArray[128]
```

Useful behavior:

- Required fields are enforced by Pydantic validation.
- Field assignment is validated after construction.
- `id` is optional and generated when not provided.
- Nested `BaseDoc` fields model multimodal structure directly.
- `summary()` and `schema_summary()` are display helpers, not required for runtime logic.
- Pydantic v1 and v2 use different configuration syntax; see [troubleshooting](troubleshooting.md#pydantic-v1v2-config-differences).

## Predefined document classes

Use predefined documents when the modality matches their field contract; subclass them when you need extra fields.

| Class | Fields | Direct conveniences | Typical use |
| --- | --- | --- | --- |
| `TextDoc` | `text`, `url`, `embedding`, `bytes_`, plus `id` | `TextDoc("hello")` sets `text`; equality and containment can compare against strings. | Text payloads, text URLs, text embeddings. |
| `ImageDoc` | `url`, `tensor`, `embedding`, `bytes_`, plus `id` | String-like input can validate as `url`; tensor-like input can validate as `tensor`; explicit keyword fields are clearest. | Image URLs, image tensors, image embeddings. |
| `AudioDoc` | `url`, `tensor`, `embedding`, `bytes_`, `frame_rate`, plus `id` | String-like input can validate as `url`; tensor-like input can validate as `tensor`. | Audio payloads with optional sample/frame metadata. |
| `VideoDoc` | `url`, `audio`, `tensor`, `key_frame_indices`, `embedding`, `bytes_`, plus `id` | Can contain an `AudioDoc` for associated audio. | Video payloads, key-frame tensors, video embeddings. |

Predefined document loaders for URLs or bytes can require media extras and external I/O. The verified modeling scope covers the schema fields and local in-memory tensor values, not network/media loading.

## `DocList` details

`DocList[MyDoc]` is a mutable Python-list-like collection that validates each document against `MyDoc`.

```python
from docarray import BaseDoc, DocList

class Caption(BaseDoc):
    text: str

captions = DocList[Caption]([Caption(text="a"), Caption(text="b")])
assert captions.text == ["a", "b"]
```

Key rules:

- Use `DocList[DocType]` when later code needs array-level access like `docs.text`.
- Use bare `DocList([...])` only for heterogeneous collections where normal list behavior is enough.
- `append`, `extend`, and `insert` validate document type for typed lists.
- Required nested `BaseDoc` fields are lifted to nested typed `DocList` values.
- Optional nested `BaseDoc` fields are lifted to a Python list because the values may include `None`.
- `DocList.construct(docs)` skips validation and should only be used with trusted data.
- `DocList.to_doc_vec(tensor_type=NdArray)` converts to a homogeneous `DocVec` batch.

## `DocVec` details

`DocVec[MyDoc]` is a columnar batch for homogeneous documents. It stacks tensor fields and stores nested documents as nested `DocVec` columns.

```python
import numpy as np
from docarray import BaseDoc, DocList
from docarray.typing import NdArray

class ImageBatchDoc(BaseDoc):
    image: NdArray[3, 224, 224]

docs = DocList[ImageBatchDoc]([
    ImageBatchDoc(image=np.zeros((3, 224, 224))) for _ in range(8)
])
vec = docs.to_doc_vec()
assert vec.image.shape == (8, 3, 224, 224)
assert vec[0].is_view()
```

Key rules:

- Always parameterize: use `DocVec[MyDoc](docs)`, not bare `DocVec(docs)`.
- The input sequence must be non-empty.
- Every document must follow the same schema.
- Tensor columns are contiguous and bulk-accessible.
- Nested `BaseDoc` fields become nested `DocVec` values.
- Nested `DocList` or `DocVec` fields become list-like columns of `DocVec` values.
- Documents returned by integer indexing are views; setting fields on a view updates the parent `DocVec`.
- Deleting items is unsupported; convert to `DocList` before deletion/reordering.
- `to_doc_list()` un-stacks a `DocVec` and leaves the original `DocVec` unusable, so store the returned `DocList` and stop using the old vector.

## Tensor typing and shape validation

Use `NdArray` for the verified NumPy-backed path:

```python
from docarray.typing import NdArray

class EmbeddingDoc(BaseDoc):
    embedding: NdArray[512]
    image: NdArray[3, 224, 224]
    square_crop: NdArray[3, "side", "side"]
    channel_first: NdArray[3, ...]
```

Shape behavior:

- Exact integer dimensions must match, unless the value can be reshaped to the target shape.
- Repeated string dimensions must match each other, e.g. `NdArray[3, "side", "side"]` requires equal height and width.
- `...` allows a variable number of dimensions in one position.
- Impossible shape mismatches raise validation errors.
- `AnyEmbedding` covers generic embedding vectors; use explicit `NdArray[n]` when dimensionality matters.

Optional tensor framework boundaries:

- Use `TorchTensor`, `TensorFlowTensor`, or `JaxArray` only after installing and verifying the corresponding framework.
- Use `AnyTensor` when a schema must accept multiple frameworks, then pass `tensor_type=TorchTensor`, `TensorFlowTensor`, `JaxArray`, or `NdArray` when converting to `DocVec`.
- The verified default is `NdArray`; do not claim optional backend behavior without running backend-specific checks.

## Dynamic document helpers

Use `create_doc()` when fields are known at runtime:

```python
from docarray.documents.helper import create_doc
from docarray.documents import ImageDoc, TextDoc

MultiModal = create_doc(
    "MultiModal",
    image=(ImageDoc, ...),
    text=(TextDoc, ...),
    score=(float, 0.0),
)
```

Use `create_doc_from_dict()` for quick schema inference from a sample:

```python
from docarray.documents.helper import create_doc_from_dict

SampleDoc = create_doc_from_dict(
    "SampleDoc",
    {"text": TextDoc("hello"), "image": ImageDoc(), "rank": 1},
)
```

Caveats:

- A `None` example value becomes `Any`, not `Optional[SpecificType]`.
- Empty samples raise `ValueError`.
- `create_doc_from_typeddict()` exists for Pydantic v1 style workflows but is not compatible with Pydantic v2; prefer `create_doc()` for portable dynamic schemas.

## Modeling decision table

| Requirement | Prefer | Avoid | Why |
| --- | --- | --- | --- |
| Stable application schema | Custom `BaseDoc` subclass | Anonymous dictionaries | Pydantic validation, clear fields, and nested DocArray support. |
| One common modality with minor additions | Subclass `TextDoc`, `ImageDoc`, `AudioDoc`, or `VideoDoc` | Reimplementing standard fields | Keeps standard `url`/`tensor`/`embedding` conventions. |
| Runtime-generated fields | `create_doc()` | Hand-building classes with `type()` | Uses Pydantic/DocArray model creation and validates `BaseDoc` inheritance. |
| Sample-driven prototype | `create_doc_from_dict()` then manually tighten fields | Leaving `None`-derived `Any` fields in production | Samples cannot infer a precise type from `None`. |
| Mutable, reorderable, heterogeneous-tolerant workflow | `DocList` | `DocVec` | `DocList` behaves like a Python list and supports insertion/deletion/reordering. |
| Contiguous tensor batch for ML forward pass | `DocVec[Schema]` | Repeated `np.stack(docs.field)` from `DocList` | `DocVec` keeps stacked tensor columns and document views. |
| Optional nested docs with mixed missing/present values | `DocList` | `DocVec` | `DocVec` requires optional doc/tensor columns to be all missing or all present. |
| Framework-independent schema | `AnyTensor` plus explicit `tensor_type` during batching | Implicit backend assumptions | Keeps schema flexible while making `DocVec` column type explicit. |
| Persistence, wire formats, FastAPI payloads | Route to [`serialization-storage`](../../serialization-storage/) | Adding protocol details here | Serialization/storage is a separate sibling sub-skill. |
| Vector search or index schema | Route to [`vector-indexing`](../../vector-indexing/) | Modeling indexes as plain batches | Index workflows have separate backend and query constraints. |
