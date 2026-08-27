# Document modeling workflows

This page gives task recipes for the `document-modeling` sub-skill. It stays focused on schema design, document collections, and tensor typing. If the task is actually about persistence, wire formats, or indexes, route to the sibling sub-skills instead of expanding this one.

## 1) Model one multimodal record with `BaseDoc`

Use a custom `BaseDoc` when you need a stable application schema or when the public predefined docs do not match your field layout.

### Recipe

1. List the modalities and metadata you need.
2. Make required fields plain annotations and optional fields `Optional[...] = None`.
3. Use nested `BaseDoc` fields for multimodal composition.
4. Use `NdArray[...]` or `AnyTensor` for tensors that matter to ML code.
5. Validate one example instance before choosing a batch container.

```python
from typing import Optional

from docarray import BaseDoc
from docarray.documents import ImageDoc, TextDoc
from docarray.typing import NdArray


class ProductDoc(BaseDoc):
    title: str
    image: ImageDoc
    caption: Optional[TextDoc] = None
    embedding: NdArray[128]
```

### Good fit

- One data record at a time.
- Strong schema validation.
- Nested multimodal payloads.
- APIs that should mirror the document shape directly.

### Prefer a predefined doc instead when

- The payload is naturally text, image, audio, or video and the standard fields already fit.
- You only need to add a few extra fields to an existing predefined schema.

## 2) Use predefined docs when the modality already exists

`TextDoc`, `ImageDoc`, `AudioDoc`, and `VideoDoc` already encode common fields and validation paths.

### Recipe

- Use `TextDoc` for text plus optional URL, bytes, and embedding.
- Use `ImageDoc` for image URL, tensor, bytes, and embedding.
- Use `AudioDoc` for audio URL, tensor, bytes, embedding, and frame rate.
- Use `VideoDoc` for video URL, associated audio, tensor, key-frame indices, bytes, and embedding.

```python
import numpy as np
from docarray.documents import ImageDoc, TextDoc

image = ImageDoc(tensor=np.zeros((3, 224, 224)))
text = TextDoc("hello world")
```

### Good fit

- The schema is a known modality with standard field names.
- You want future agents to recognize the document immediately.
- You want to compose standard docs inside a larger `BaseDoc`.

## 3) Compose nested documents

Use nested documents to represent a hierarchy such as article → image → embedding, or request → sample → chunk.

### Recipe

```python
from docarray import BaseDoc, DocList
from docarray.documents import ImageDoc, TextDoc


class ArticleDoc(BaseDoc):
    title: str
    hero: ImageDoc
    summary: TextDoc
    tags: DocList[TextDoc]
```

### Rules of thumb

- Use a nested `BaseDoc` when one field is conceptually another document.
- Use `DocList[ChildDoc]` when a field is a repeated list of homogeneous child documents.
- If the child field can be absent on some rows, think carefully about `DocList` versus `DocVec`.

## 4) Choose `DocList` versus `DocVec`

Use the container that matches the downstream workload, not the one that is easiest to type.

### Recipe

1. Ask whether you need mutable list semantics or contiguous batch semantics.
2. Ask whether the collection may be heterogeneous.
3. Ask whether optional nested fields can vary row by row.
4. Ask whether the next step is ML batching or data shuffling.

### Decision guide

| If you need... | Use | Why |
| --- | --- | --- |
| Reordering, insertion, deletion, or streaming | `DocList` | It behaves like a Python list. |
| Homogeneous batch columns for ML | `DocVec` | It keeps contiguous tensor columns. |
| Mixed schemas | Bare `DocList` | Typed `DocList[DocType]` rejects heterogeneity. |
| Optional fields with mixed missing/present rows | `DocList` | `DocVec` requires all-none or all-present columns. |
| Views into stacked data | `DocVec` | Indexing returns document views backed by shared storage. |

### Example

```python
import numpy as np
from docarray import BaseDoc, DocList
from docarray.typing import NdArray


class ImageRow(BaseDoc):
    image: NdArray[3, 224, 224]
    label: str

rows = DocList[ImageRow]([
    ImageRow(image=np.zeros((3, 224, 224)), label="cat"),
    ImageRow(image=np.ones((3, 224, 224)), label="dog"),
])

batch = rows.to_doc_vec()
assert batch.image.shape == (2, 3, 224, 224)
```

## 5) Create dynamic schemas at runtime

Use dynamic schema creation when the fields are not known until runtime or when you are translating a sample payload into a DocArray model.

### Recipe: `create_doc()`

```python
from docarray import BaseDoc
from docarray.documents import ImageDoc, TextDoc
from docarray.documents.helper import create_doc


RuntimeDoc = create_doc(
    "RuntimeDoc",
    __base__=BaseDoc,
    image=(ImageDoc, ...),
    title=(TextDoc, ...),
    score=(float, 0.0),
)
```

Use this when you already know the exact field types and just need a class object.

### Recipe: `create_doc_from_dict()`

```python
import numpy as np
from docarray.documents import ImageDoc
from docarray.documents.helper import create_doc_from_dict


SampleDoc = create_doc_from_dict(
    "SampleDoc",
    {
        "image": ImageDoc(tensor=np.zeros((3, 224, 224))),
        "title": "hello",
        "rank": 1,
    },
)
```

Use this when you have an example payload and want a quick prototype.

### Caution

- A `None` sample value becomes `Any`, not `Optional[SpecificType]`.
- Empty input raises `ValueError`.
- `create_doc_from_typeddict()` is not the portable choice for Pydantic v2 workflows.

## 6) Type tensors for ML batching

Use `NdArray` when NumPy is the verified target. Add explicit shapes when downstream code depends on them.

### Recipe

```python
from docarray import BaseDoc
from docarray.typing import NdArray


class BatchInput(BaseDoc):
    image: NdArray[3, 224, 224]
    embedding: NdArray[128]
```

### Rules

- Use exact integer dimensions for hard shape checks.
- Use repeated string dimensions when two axes must match.
- Use `...` when one axis can vary in length.
- Keep batch shapes on the outside of the tensor, not inside the per-document schema, unless you explicitly want batched values.

### When a field may use multiple tensor frameworks

- Keep the schema broad with `AnyTensor`.
- Convert the batch with `DocVec(..., tensor_type=NdArray)` or the matching backend type.
- Only rely on Torch, TensorFlow, or JAX when that backend has been installed and verified separately.

## 7) Use `DocVec` for batch-first ML code

If the next step is a model forward pass or a vectorized tensor transform, move from `DocList` to `DocVec` as soon as the schema is homogeneous.

### Recipe

```python
from docarray import BaseDoc, DocList
from docarray.typing import NdArray
import numpy as np


class PatchDoc(BaseDoc):
    tensor: NdArray[3, 32, 32]

patches = DocList[PatchDoc]([
    PatchDoc(tensor=np.zeros((3, 32, 32))),
    PatchDoc(tensor=np.ones((3, 32, 32))),
])

vec = patches.to_doc_vec()
assert vec.tensor.shape == (2, 3, 32, 32)
```

### Good fit

- A model expects contiguous tensors.
- You want bulk field access without repeated Python-side stacking.
- You want document views whose mutations reflect on the parent batch.

## 8) Use `DocList` for mixed or partially missing nested documents

If some rows contain a nested document and others do not, keep the collection in `DocList` unless you can normalize the data first.

### Recipe

```python
from typing import Optional
from docarray import BaseDoc, DocList
from docarray.documents import ImageDoc
from docarray.typing import NdArray
import numpy as np


class Row(BaseDoc):
    image: Optional[ImageDoc] = None
    feature: NdArray[4]

rows = DocList[Row]([
    Row(image=ImageDoc(tensor=np.zeros((3, 4, 4))), feature=np.zeros(4)),
    Row(image=None, feature=np.ones(4)),
])
```

### Why

- `DocList` can hold `None` and still preserve the row-wise structure.
- `DocVec` only works when the optional field is all missing or all present.

## 9) Route out when the task crosses a boundary

- Need bytes/JSON/protobuf/CSV/DataFrame or file/S3 storage? Route to [`serialization-storage`](../../serialization-storage/).
- Need indexes, search, filtering, or backend selection? Route to [`vector-indexing`](../../vector-indexing/).

If the task includes both modeling and one of those downstream concerns, finish the modeling step here and hand the result to the sibling sub-skill instead of expanding this one.
