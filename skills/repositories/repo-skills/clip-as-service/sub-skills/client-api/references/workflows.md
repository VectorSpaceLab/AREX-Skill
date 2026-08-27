# Client Workflows

## Connectivity profile

Use `profile()` before sending large batches. It verifies that the endpoint is reachable and reports round-trip, gateway, and model timings.

```python
from clip_client import Client

client = Client("grpc://127.0.0.1:51000")
print(client.profile())
print(client.profile("hello world"))
```

If this fails with an unavailable or connection error, do not debug embeddings yet; use [troubleshooting.md](troubleshooting.md) first.

## Encode text and images from strings

```python
from clip_client import Client

client = Client("grpc://127.0.0.1:51000")
emb = client.encode([
    "a photo of a red car",
    "a photo of a blue bicycle",
    "https://example.invalid/sample-image.png",  # replace with a real reachable image URL
])
print(emb.shape)
```

Use lists, tuples, or generators. A single bare string is invalid.

## Encode explicit Documents

```python
from clip_client import Client
from docarray import Document, DocumentArray

client = Client("grpc://127.0.0.1:51000")
docs = DocumentArray([
    Document(id="text-1", text="a small dog"),
    Document(id="image-1", uri="/path/to/local/image.jpg"),
])
result = client.encode(docs, batch_size=8)
assert result[0] is docs[0]
print(result.embeddings.shape)
```

Prefer `.uri` for many images so the client can load lazily instead of preloading all bytes into memory. Use `.blob` only when the user already has bytes and memory is bounded.

## Rank image-to-text matches

```python
from clip_client import Client
from docarray import Document

client = Client("grpc://127.0.0.1:51000")
doc = Document(
    uri="/path/to/image.jpg",
    matches=[
        Document(text="a dog in the grass"),
        Document(text="a red sports car"),
        Document(text="a bowl of fruit"),
    ],
)
ranked = client.rank([doc])
for match in ranked[0].matches:
    print(match.text, match.scores["clip_score"].value)
```

The returned `.matches` are sorted by softmax-style `clip_score`. The raw cosine similarity is available in `clip_score_cosine`.

## Rank text-to-image matches

```python
from clip_client import Client
from docarray import Document

client = Client("grpc://127.0.0.1:51000")
doc = Document(
    text="a photo of a conference room",
    matches=[
        Document(uri="/path/to/room-a.jpg"),
        Document(uri="/path/to/room-b.jpg"),
    ],
)
ranked = client.rank([doc], parameters={"drop_image_content": True})
print(ranked[0].matches[:, "scores__clip_score__value"])
```

Use `drop_image_content=True` when returning blobs/tensors would be too large.

## Async encoding

```python
import asyncio
from clip_client import Client

client = Client("grpc://127.0.0.1:51000")

async def main():
    other_task = asyncio.sleep(1)
    encode_task = client.aencode(["hello"] * 32, batch_size=8)
    embeddings, _ = await asyncio.gather(encode_task, other_task)
    print(embeddings.shape)

asyncio.run(main())
```

Do not switch to async solely for style; use it when the caller already has an event loop or concurrent I/O.

## Call index/search from the client

`index` and `search` need a server Flow containing an indexer. If the user only started an encoder Flow, build the search Flow using [search-retrieval](../../search-retrieval/SKILL.md) first.

```python
from clip_client import Client
from docarray import Document

client = Client("grpc://127.0.0.1:61000")
client.index([
    Document(id="caption-1", text="she smiled, with pain"),
    Document(id="image-1", uri="/path/to/apple.png"),
])

result = client.search(["smile"], limit=2)
for match in result[0].matches:
    print(match.id, match.scores)
```

## Callback-owned collection

If you provide `on_done` and do not let the client gather results internally, the method can return `None`:

```python
seen = []
def on_done(resp):
    seen.extend(resp.data.docs)

returned = client.encode(["hello"], on_done=on_done)
assert returned is None
assert seen
```

Use this pattern for streaming into an external sink, not when the caller expects a normal return value.
