# Serialization and storage troubleshooting

Use this reference when DocArray serialization, local stores, S3 stores, DataFrame/CSV exchange, or FastAPI response routing fails.

## Optional extras are missing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` names `google.protobuf` or protobuf serialization fails. | The `proto` extra is missing or incompatible. | Install `pip install "docarray[proto]"`, then retry the protobuf path. Use JSON only as a temporary fallback when protobuf is not required. |
| `ImportError` names `lz4`. | `compress="lz4"` was requested without the optional `lz4` package. | Install `pip install "docarray[proto]"`, choose another compressor such as `gzip`, or pass `compress=None`. |
| `ImportError` names `pandas` during `to_dataframe()` or `from_dataframe()`. | The `pandas` extra is missing. | Install `pip install "docarray[pandas]"` or use JSON/protobuf/CSV where appropriate. |
| `from docarray.base_doc import DocArrayResponse` fails and names `fastapi`. | The `web` extra is missing. | Install `pip install "docarray[web]"`. App tests may also need normal FastAPI tooling such as a test client or server runner. |
| `from docarray.store import S3DocStore` fails and names `smart_open`, `boto3`, or `botocore`. | The `aws` extra or its S3 dependencies are missing. | Install `pip install "docarray[aws]"`, then verify credentials and network separately. |

The verified default scope for this skill includes CPU DocArray base plus `proto`, `pandas`, and `web`. S3/AWS and optional tensor frameworks are documented boundaries, not verified defaults.

## Protocol or compression mismatch

Symptoms include parse errors, unsupported binary version errors, protobuf parse failures, decompression errors, or loaded objects with unexpected types.

Checklist:

1. Use the same `protocol` and `compress` values on serialization and deserialization.
2. For `BaseDoc` base64, always pass `protocol` explicitly. In this version, `BaseDoc.to_base64()` defaults to `protocol="protobuf"`, but `BaseDoc.from_base64()` defaults to `protocol="pickle"`.
3. Remember collection defaults differ from single-document defaults: `DocList` and `DocVec` bytes/binary methods default to `protocol="protobuf-array"`; `BaseDoc` bytes default to `protocol="protobuf"`.
4. Watch filename suffix inference in `save_binary()` and `load_binary()`. Suffixes such as `.protobuf.gzip` can override the provided or default protocol/compression. Pass explicit arguments and choose unambiguous filenames when troubleshooting.
5. Use pickle protocols only for trusted Python-only data. Do not unpickle bytes received from untrusted sources.

## Protobuf `Union` and nested document limits

Protobuf deserialization does not support `Union` fields involving `BaseDoc` subclasses. A schema like this should use JSON instead:

```python
from typing import Union
from docarray import BaseDoc
from docarray.documents import ImageDoc, TextDoc

class MixedDoc(BaseDoc):
    payload: Union[TextDoc, ImageDoc]
```

Typical failure text includes `Union type is not supported for proto deserialization. Please use JSON serialization instead` or a field-specific protobuf deserialization error. Basic scalar unions such as `Union[int, str]` can round-trip in covered tests, but document unions should be treated as JSON-only.

Other protobuf caveats:

- Dict keys must be strings; non-string keys raise during protobuf conversion.
- Cyclic references raise during protobuf conversion.
- If a nested document field cannot be resolved to its concrete field type during protobuf deserialization, use JSON or tighten the schema.

## CSV limitations

CSV is row-based and scalar-oriented.

Common failures and fixes:

- `DocVec.to_csv()` or `DocVec.from_csv()` raises `NotImplementedError`: convert through `DocList` only when the schema is scalar-compatible.
  ```python
  vec.to_doc_list().to_csv("rows.csv")
  vec2 = DocList[MyDoc].from_csv("rows.csv").to_doc_vec()
  ```
- Bare `DocList` CSV export raises a type error: use `DocList[MyDoc]` so DocArray knows the schema.
- Column mismatch raises `ValueError`: CSV headers must match document field names or nested access paths such as `image__url`.
- Tensor, array, nested list, and nested `DocList` fields are not reliable CSV payloads. Scalar CSV was covered; tensor CSV failed in verification. Use JSON, protobuf-array bytes, binary files, or DataFrame workflows instead.
- Empty strings and the string `None` may be interpreted as missing values when rebuilding nested documents.
- Remote CSV URLs are supported by the API, but they introduce network and content-trust constraints that are outside this local serialization scope.

## DataFrame limitations

DataFrame conversion requires pandas and a typed homogeneous schema.

- Use `DocList[MyDoc].from_dataframe(df)` or `DocVec[MyDoc].from_dataframe(df, tensor_type=NdArray)`, not bare `DocList.from_dataframe(df)`.
- Column names must match schema fields or nested `__` access paths.
- For `DocVec` deserialization from DataFrame, pass `tensor_type=...` when you need a backend other than the default `NdArray`.
- List-like fields and nested `DocList` fields can be fragile in tabular form. Prefer JSON/protobuf/binary for rich multimodal payloads.

## `DocVec tensor_type` surprises

Every `DocVec.from_*` path in this scope defaults to `tensor_type=NdArray`. If a serialized vector originally used a different tensor framework, deserialization still returns `NdArray` unless you pass the target tensor class.

```python
loaded = DocVec[MyDoc].from_bytes(
    payload,
    protocol="protobuf-array",
    tensor_type=NdArray,
)
```

Use `TorchTensor`, `TensorFlowTensor`, or `JaxArray` only after installing and verifying the corresponding framework. Optional tensor backends were not verified by this sub-skill.

## File store path and namespace failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` while pushing to `file://.../name`. | The explicit parent directory does not exist. | Create the namespace directory first, then push. |
| `FileDocStore.list(namespace, ...)` raises `FileNotFoundError`. | The namespace directory does not exist. | Create the directory or list the correct existing namespace. |
| Store appears under DocArray's cache instead of the current directory. | The name after `file://` did not start with `/`, `~`, or `.`. | Use an explicit path or prefix relative paths with `./`, for example `file://./my-docs`. |
| A push raises `ConcurrentPushException` mentioning `.docs.tmp`. | Another push is active or a stale temp file remains. | Confirm no writer is active before deleting the temp file; then retry. |
| Pull logs that `local_cache` is unsupported for `file` protocol. | `DocList.pull()` defaults `local_cache=True`, but local file stores do not use caching. | Pass `local_cache=False` for quiet file pulls. `pull_stream()` already defaults to `False`. |

The file store adds `.docs` automatically. Pass the logical store name without `.docs` to `push`, `pull`, and `delete`.

## S3 credentials, network, and key failures

S3 operations are optional and service-dependent.

Common issues:

- Missing dependencies: install `docarray[aws]` and verify `smart_open`, `boto3`, and `botocore` imports.
- Missing credentials or wrong region/endpoint: configure the default `boto3` session/client before calling `DocList.push()` or `DocList.pull()`.
- Wrong URL shape: `s3://bucket/key` must include both bucket and key. `S3DocStore.list()` and `S3DocStore.delete()` take `bucket/namespace` or `bucket/key` without the `s3://` prefix.
- Missing bucket, denied permissions, DNS errors, proxy issues, or endpoint incompatibility: fix service access first; DocArray will surface the underlying boto3/smart_open error.
- Untrusted pickle payloads: the S3 store uses per-document pickle serialization internally. Treat S3 store contents as trusted application data only.
- `local_cache=True` on S3 may use a cache file when its size matches the object. Disable `local_cache` while debugging freshness.

Do not include credentials in generated code snippets. Future live S3 tasks should provide a safe credential and endpoint plan before running storage operations.

## FastAPI response class issues

- Import with `from docarray.base_doc import DocArrayResponse`; the import lazily requires FastAPI.
- Use `response_class=DocArrayResponse` on routes that return DocArray documents or lists containing DocArray tensors.
- For single documents, combine `response_model=OutputDoc` with `response_class=DocArrayResponse` when you want FastAPI schema validation plus DocArray tensor-aware rendering.
- For `DocList`, annotate route inputs/outputs as `List[MyDoc]`, convert inbound lists with `DocList[MyDoc].construct(docs)`, and return `list(doc_list)`. Send bodies with `doc_list.to_json()` and parse responses with `DocList[MyDoc].from_json(...)`.
- Large tensors can make OpenAPI examples slow or simplified. Validate runtime payloads separately from docs UI expectations.
