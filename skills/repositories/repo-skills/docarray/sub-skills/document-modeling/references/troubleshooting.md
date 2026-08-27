# Document modeling troubleshooting

Use this guide when DocArray schema creation, validation, `DocList`, `DocVec`, tensor typing, or optional framework imports fail.

## Pydantic v1/v2 config differences

### Symptom

A schema config example copied from a different Pydantic major version fails, or a config attribute appears ignored.

### Cause

`BaseDoc` is a Pydantic model. Pydantic v1 uses a nested `Config` class; Pydantic v2 uses `model_config`. DocArray provides examples for both styles.

### Fix

For Pydantic v1:

```python
from docarray import BaseDoc

class MyDoc(BaseDoc):
    class Config(BaseDoc.Config):
        arbitrary_types_allowed = True
```

For Pydantic v2:

```python
from docarray import BaseDoc

class MyDoc(BaseDoc):
    model_config = BaseDoc.ConfigDocArray.ConfigDict(
        arbitrary_types_allowed=True
    )
```

If portability matters, detect the Pydantic major version in your own application setup and use the matching syntax. Do not mix both styles blindly in one schema.

## Validation errors when constructing `BaseDoc`

### Symptom

Construction fails with a Pydantic `ValidationError`, often for a tensor shape, URL type, or nested document field.

### Likely causes

- A required field was omitted.
- A field was passed with the wrong type.
- `NdArray[shape]` could not validate or reshape the input.
- A nested field expects a `BaseDoc` subclass but received an incompatible value.

### Fix

- Make absent fields explicit with `Optional[...] = None`.
- Use exact predefined docs, e.g. `TextDoc(text="...")` and `ImageDoc(tensor=array)`.
- Confirm per-document tensor shape excludes the batch axis.
- Build one single document first, then put it in `DocList` or `DocVec`.

## Heterogeneous `DocList` versus typed `DocList` errors

### Symptom

`DocList[ImageDoc]([...])`, `.append()`, `.extend()`, or `.insert()` raises a message like `... is not a <class ...>`.

### Cause

A typed `DocList[DocType]` validates every item against `DocType`. This is required for schema-level bulk field access such as `docs.tensor` or `docs.text`.

### Fix

- If all documents should share one schema, convert or wrap every item into the same `DocType`.
- If schemas are intentionally mixed, use bare `DocList([...])` and treat it more like a Python list.
- Do not expect array-level field access on a heterogeneous list.

## `DocVec` requires an explicit document type

### Symptom

Calling `DocVec([...])` raises a type error instructing you to use `DocVec[MyDoc](docs)`.

### Cause

`DocVec` must know the homogeneous schema before it can allocate columns.

### Fix

```python
from docarray import DocVec

vec = DocVec[MyDoc](docs)
```

Also ensure `docs` is not empty; an empty `DocVec` cannot infer or allocate columns.

## `DocVec` optional-field rules

### Symptom

Creating a `DocVec` with optional nested documents or tensors fails when some rows have `None` and others have values. Error text can say that all docs should have a field set to `None`, or that a field is `None` even though it is required/present in the first doc.

### Cause

`DocVec` is columnar. For optional tensor or nested document columns it supports two states:

- all documents have `None`, so the whole column is `None`; or
- all documents have a value, so the column is allocated and stacked.

It cannot represent a mixed `None`/value column for those nested tensor/doc fields.

### Fix

- Keep the data in `DocList` when row-wise missingness is meaningful.
- Normalize the data before batching: fill missing nested docs/tensors with defaults, or split present and missing rows into separate batches.
- If all values are missing now but will be filled later, `DocVec` can set the column later with a full-length list of values or set it back to `None`.

## `DocVec` deletion and stale object after `to_doc_list()`

### Symptom

- `del vec[i]` raises `NotImplementedError`.
- Accessing a `DocVec` after `to_doc_list()` raises an unusable-object style error.

### Cause

`DocVec` is optimized for columnar batch storage, not row deletion. Converting to `DocList` unstacks and consumes internal storage.

### Fix

```python
rows = vec.to_doc_list()
# use rows from now on; do not keep using vec
```

Perform deletion, insertion, shuffling, or reranking on the resulting `DocList`.

## Tensor shape mismatch

### Symptom

A tensor field annotated as `NdArray[3, 224, 224]` fails validation or warns that a reshape is being attempted.

### Cause

DocArray validates tensor shapes from the annotation. Exact dimensions must match unless the value can be reshaped to the target shape. Repeated string dimensions must be consistent.

### Fix

- Use per-document shapes, not batch shapes, in `BaseDoc` fields.
- Use `NdArray[3, ...]` when only the leading channel count matters.
- Use `NdArray[3, "side", "side"]` when square dimensions matter but size varies.
- Use unparameterized `NdArray` during exploration, then tighten once shapes are known.

## NumPy 2 `DocVec` device issue

### Symptom

`DocVec` construction with NumPy-backed tensors fails with an error related to an unsupported or unexpected `device` argument/attribute.

### Cause

The verified environment exposed a DocArray NumPy backend compatibility issue with NumPy 2.x. The validated CPU environment used NumPy 1.26.4.

### Fix

- Prefer `numpy<2` for the current verified DocArray CPU `DocVec` workflows.
- If you must use NumPy 2, run a local smoke first with a small `DocVec[MyDoc]` using `NdArray` fields before trusting batch behavior.
- Use `scripts/schema_smoke.py` from this sub-skill to check the active environment.

## Missing optional Torch/TensorFlow/JAX imports

### Symptom

Importing `TorchTensor`, `TensorFlowTensor`, `JaxArray`, or modality-specific framework tensor classes raises `ImportError`.

### Cause

DocArray exposes optional tensor classes lazily. The matching backend package must be installed separately. The verified minimum scope did not install or verify those optional tensor frameworks.

### Fix

- For verified CPU default workflows, use `NdArray`.
- Install and verify the optional framework before using its tensor class.
- When a schema uses `AnyTensor`, pass the intended backend class to `DocVec(..., tensor_type=...)` only after the backend import succeeds.
- Do not treat successful `BaseDoc` import as proof that Torch, TensorFlow, or JAX tensor classes are available.

## Dynamic schema helper pitfalls

### Symptom

`create_doc()` rejects a base class, `create_doc_from_dict()` raises `ValueError`, or a dynamically inferred field is too broad.

### Causes and fixes

- `__base__` must be `BaseDoc` or a subclass; do not pass raw `pydantic.BaseModel`.
- `create_doc_from_dict()` requires at least one item.
- `None` example values infer `Any`; replace them with explicit fields via `create_doc()` when the type matters.
- `create_doc_from_typeddict()` is not compatible with Pydantic v2; prefer `create_doc()` for version-portable dynamic schemas.

## Predefined document loader caveats

### Symptom

A URL or bytes loader on `ImageDoc`, `AudioDoc`, `VideoDoc`, or `TextDoc` fails even though the schema constructs correctly.

### Cause

Document modeling and in-memory tensors are in the verified scope. Actual media loading can require optional image/audio/video dependencies, network access, or local files that are outside the verified default.

### Fix

- Keep modeling examples explicit with `text=...`, `tensor=...`, or `bytes_=...` when avoiding optional I/O.
- Verify media extras and file/network access before using `.load()` or `.load_bytes()` in production.
- Keep those loader checks separate from schema validation checks.

## Boundary routes

- If the failure happens during bytes, JSON, protobuf, CSV, DataFrame, file store, S3, or FastAPI response handling, route to [`serialization-storage`](../../serialization-storage/).
- If the failure happens during indexing, vector search, query building, filters, or external database selection, route to [`vector-indexing`](../../vector-indexing/).
