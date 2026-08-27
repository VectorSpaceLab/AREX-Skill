# Client API Reference

## Verified public class

```python
from clip_client import Client
```

Verified constructor signature:

```text
Client.__init__(self, server: str, credential: dict = {}, **kwargs)
```

`server` is a URI-like endpoint with scheme, host, and port. Valid schemes are `grpc`, `http`, `websocket`, and TLS variants `grpcs`, `https`, `websockets`/`wss`. Credentials are taken from `credential["Authorization"]` or `CLIP_AUTH_TOKEN`.

## Method signatures and endpoint mapping

| Method | Verified signature shape | Server endpoint | Main return |
| --- | --- | --- | --- |
| `profile` | `profile(content: Optional[str] = '') -> Dict[str, float]` | `/` | latency dictionary |
| `encode` | `encode(content, **kwargs)` | `/encode/{model_name}` or `/encode` | NumPy array for iterable strings; `DocumentArray` for Documents |
| `aencode` | `async aencode(content, **kwargs)` | `/encode/{model_name}` or `/encode` | same as `encode` |
| `rank` | `rank(docs, **kwargs) -> DocumentArray` | `/rank/{model_name}` or `/rank` | `DocumentArray` with sorted matches and CLIP scores |
| `arank` | `async arank(docs, **kwargs) -> DocumentArray` | `/rank/{model_name}` or `/rank` | same as `rank` |
| `index` | `index(content, **kwargs)` | `/index` | `DocumentArray` or callback-owned `None` |
| `aindex` | `async aindex(content, **kwargs)` | `/index` | same as `index` |
| `search` | `search(content, limit: int = 10, **kwargs) -> DocumentArray` | `/search` | `DocumentArray` with `.matches` |
| `asearch` | `async asearch(content, limit: int = 10, **kwargs)` | `/search` | same as `search` |

## Common keyword arguments

| Argument | Applies to | Meaning |
| --- | --- | --- |
| `batch_size` | encode/rank/index/search | Request size sent per stream batch; defaults to 8 in payload construction. |
| `show_progress` | all streaming methods | Show progress bar when true. |
| `parameters` | all request methods | Extra endpoint parameters. For encode/rank this can include `model_name` and `drop_image_content`; for search, `limit` is inserted. |
| `prefetch` | all request methods | Number of in-flight batches. Use lower values when server work is expensive or memory-bound. |
| `on_done`, `on_error`, `on_always` | all request methods | Jina callbacks. If callbacks own result collection, the method may return `None`. |
| `source` | rank only | Nested field used for candidates; default is `matches`. |
| `limit` | search only | Number of search results returned per query. |

## Input contracts

### Iterable of strings

Each string is auto-detected:

- Local image path, remote image URL, or data URI: image input.
- Other string: text input.

A bare string is rejected because it is iterable character-by-character. Wrap one item in a list:

```python
client.encode(["hello world"])
```

### DocArray Documents

Use `Document`/`DocumentArray` when fields must be explicit:

- `.text` means text.
- `.uri`, `.blob`, or `.tensor` means image when `.text` is absent.
- If both `.text` and `.uri` are present, text is used first.
- Tensor image shape should be `[H, W, C]` before preprocessing.

For `rank`, every root `Document` must have candidates in `.matches` or the field named by `source`.

## Output contracts

- `encode(list[str])` returns a NumPy `ndarray` with shape `[N, D]`.
- `encode(DocumentArray)` returns a `DocumentArray` of the same objects, with `.embedding` set.
- `rank` returns root documents with `.matches` sorted descending by `.scores["clip_score"].value`. Matches also receive `.scores["clip_score_cosine"]`.
- `index` returns documents after embeddings are computed by the server/indexer Flow.
- `search` returns query documents with `.matches` populated by the indexer.

Order-preservation tests assume unique `Document.id` values. If users supply duplicate IDs, gathered results can be incomplete or overwrite each other.

## Authentication and headers

- gRPC: authorization is sent as metadata key `authorization`.
- HTTP: authorization is sent as header `Authorization`.
- Websocket credentials are not supported by this client implementation; the client warns and proceeds without applying the credential.

## Async guidance

Use `aencode`, `arank`, `aindex`, or `asearch` only when the surrounding application is already async or can overlap I/O. For ordinary scripts, sync methods are simpler and correct.
