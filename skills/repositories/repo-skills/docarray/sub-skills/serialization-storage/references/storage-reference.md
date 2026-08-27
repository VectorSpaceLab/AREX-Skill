# Storage reference

This reference covers DocArray `DocList` push/pull stores for `file://` and `s3://` URLs. For schema design, route to sibling [`document-modeling`](../../document-modeling/). For serialization protocol details outside stores, use [serialization-reference.md](serialization-reference.md).

## Store API surface

`push`/`pull` is implemented on `DocList`, not directly on `BaseDoc` or `DocVec`.

```python
from docarray import DocList

result: dict = docs.push(url, show_progress=False)
pulled = DocList[MyDoc].pull(url, show_progress=False, local_cache=True)

result: dict = DocList[MyDoc].push_stream(iter_docs, url, show_progress=False)
stream = DocList[MyDoc].pull_stream(url, show_progress=False, local_cache=False)
```

URL protocols are resolved from strings of the form `protocol://namespace/name`. Supported protocols are `file` and `s3`. Unsupported protocols raise `ValueError`.

Use a typed `DocList[MyDoc]` for `pull()` and `pull_stream()`. A bare `DocList.pull(...)` has no schema and raises a type error.

## Local file store

### Behavior summary

| API | Signature shape | Behavior |
| --- | --- | --- |
| `docs.push("file://...")` | `push(url: str, show_progress: bool = False)` | Streams documents to a local `.docs` file. Internally uses per-document `protocol="protobuf"` and `compress="gzip"`. |
| `DocList[MyDoc].pull("file://...")` | `pull(url: str, show_progress: bool = False, local_cache: bool = True)` | Reads the `.docs` file and returns a full `DocList[MyDoc]`. For file stores, `local_cache` is not used. |
| `DocList[MyDoc].push_stream(...)` | `push_stream(docs: Iterator[BaseDoc], url: str, show_progress: bool = False)` | Streams documents from any iterator to a local `.docs` file without first building a full `DocList`. |
| `DocList[MyDoc].pull_stream(...)` | `pull_stream(url: str, show_progress: bool = False, local_cache: bool = False)` | Returns an iterator of documents from the local `.docs` file. |
| `FileDocStore.list(namespace, show_table=False)` | `list(namespace: str, show_table: bool) -> List[str]` | Lists `*.docs` files in an existing namespace directory and returns file stems. |
| `FileDocStore.delete(name, missing_ok=False)` | `delete(name: str, missing_ok: bool = False) -> bool` | Deletes `name + ".docs"`. Returns `True` when deleted. With `missing_ok=True`, returns `False` if absent; otherwise raises. |

Resolution rules for the part after `file://`:

- Names that do not start with `/`, `~`, or `.` are stored under DocArray's user cache directory.
- Names starting with `/`, `~`, or `.` are resolved as filesystem paths.
- The `.docs` suffix is added by `FileDocStore`; pass the logical name without `.docs` to `push`, `pull`, `list`, and `delete`.
- For explicit nested paths, the parent namespace directory must already exist. The file store does not create missing parents for you.
- Push writes `name.docs.tmp` first and then renames it to `name.docs`. A stale or active temporary file can raise `ConcurrentPushException`.

### Safe local example

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from docarray import BaseDoc, DocList
from docarray.store import FileDocStore

class NoteDoc(BaseDoc):
    text: str

docs = DocList[NoteDoc]([NoteDoc(text="first"), NoteDoc(text="second")])

with TemporaryDirectory() as tmp:
    namespace = Path(tmp) / "docstore"
    namespace.mkdir(parents=True, exist_ok=True)

    url = f"file://{namespace / 'notes'}"
    docs.push(url, show_progress=False)

    pulled = DocList[NoteDoc].pull(url, show_progress=False, local_cache=False)
    assert [d.text for d in pulled] == ["first", "second"]

    assert "notes" in FileDocStore.list(str(namespace), show_table=False)
    assert FileDocStore.delete(str(namespace / "notes"), missing_ok=False)
```

### Streaming local example

```python
from tempfile import TemporaryDirectory
from pathlib import Path
from docarray import BaseDoc, DocList

class EventDoc(BaseDoc):
    text: str

def generate_events():
    for idx in range(3):
        yield EventDoc(text=f"event-{idx}")

with TemporaryDirectory() as tmp:
    namespace = Path(tmp)
    url = f"file://{namespace / 'events'}"

    DocList[EventDoc].push_stream(generate_events(), url, show_progress=False)
    stream = DocList[EventDoc].pull_stream(url, show_progress=False)
    assert [doc.text for doc in stream] == ["event-0", "event-1", "event-2"]
```

Prefer `pull_stream()` when the consumer can process one document at a time and the dataset may be large. Prefer `pull()` when downstream logic needs random access, length, or vectorized `DocList` field access.

## S3 store

S3 support is optional and was not service-verified in the selected CPU environment. Treat this section as usage guidance until a future task provides credentials, endpoint, bucket, and network access.

### Requirements

- Install the AWS extra: `pip install "docarray[aws]"`.
- The lazy `S3DocStore` import requires `smart_open`, `boto3`, and `botocore` to import successfully.
- `DocList.push("s3://bucket/key")` and `DocList[MyDoc].pull("s3://bucket/key")` use the default `boto3` client/resource configuration. Configure credentials, region, endpoint, and signature behavior outside the DocArray call before using the store.
- The S3 name must include both a bucket and a key separated by `/`, for example `s3://my-bucket/path/to/docs`.
- The object key written by DocArray is `key + ".docs"`.

### Behavior summary

| API | Signature shape | Behavior |
| --- | --- | --- |
| `docs.push("s3://bucket/key")` | `push(url: str, show_progress: bool = False)` | Streams documents to S3 via `S3DocStore.push_stream`. Internally uses per-document `protocol="pickle"`; only use with trusted Python data. |
| `DocList[MyDoc].pull("s3://bucket/key")` | `pull(url: str, show_progress: bool = False, local_cache: bool = False)` | Downloads and returns a full `DocList[MyDoc]`. `local_cache=True` may reuse a cache file when size matches the remote object. |
| `DocList[MyDoc].push_stream(...)` | `push_stream(docs: Iterator[BaseDoc], url: str, show_progress: bool = False)` | Streams an iterator to `s3://bucket/key.docs`. |
| `DocList[MyDoc].pull_stream(...)` | `pull_stream(url: str, show_progress: bool = False, local_cache: bool = False)` | Returns an iterator of documents from `s3://bucket/key.docs`. |
| `S3DocStore.list("bucket/namespace", show_table=False)` | `list(namespace: str, show_table: bool = False) -> List[str]` | Lists `*.docs` object names under a bucket namespace and returns stems. Do not include `s3://`. |
| `S3DocStore.delete("bucket/key", missing_ok=True)` | `delete(name: str, missing_ok: bool = True) -> bool` | Deletes `key + ".docs"`. Returns `False` for missing objects when `missing_ok=True`. Do not include `s3://`. |

### S3 usage skeleton

```python
from docarray import BaseDoc, DocList

class NoteDoc(BaseDoc):
    text: str

# Configure the default boto3 session/client before this point.
docs = DocList[NoteDoc]([NoteDoc(text="first"), NoteDoc(text="second")])

docs.push("s3://my-bucket/path/to/notes", show_progress=False)
pulled = DocList[NoteDoc].pull(
    "s3://my-bucket/path/to/notes",
    show_progress=False,
    local_cache=False,
)
assert [doc.text for doc in pulled] == ["first", "second"]
```

Use `from docarray.store import S3DocStore` for list/delete only after the `aws` extra and S3 configuration are ready:

```python
from docarray.store import S3DocStore

names = S3DocStore.list("my-bucket/path/to", show_table=False)
removed = S3DocStore.delete("my-bucket/path/to/notes", missing_ok=True)
```

## Choosing between binary files and stores

| Need | Prefer | Reason |
| --- | --- | --- |
| One local artifact with explicit protocol choice | `save_binary()` / `load_binary()` | You control `protocol`, `compress`, and file suffix behavior. |
| Local handoff by logical namespace | `DocList.push("file://...")` / `pull()` | Store API adds `.docs`, list/delete helpers, and streaming push/pull. |
| Large local stream | `push_stream()` / `pull_stream()` | Avoids materializing a full `DocList` on one side. |
| Remote object storage | `s3://` store after credential verification | Uses the same `DocList` store interface but depends on AWS-compatible service state. |
| `DocVec` storage | `vec.save_binary()` or `vec.to_doc_list().push(...)` | Stores do not live directly on `DocVec`; convert to `DocList` or use binary serialization. |
