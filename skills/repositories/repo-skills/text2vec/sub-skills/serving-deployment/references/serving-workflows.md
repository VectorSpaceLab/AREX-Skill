# Serving workflows for text2vec

This reference turns text2vec embedding and similarity calls into service patterns.
Keep the service layer thin: choose and test the embedding/search behavior with
`embeddings` and `similarity-search`, then wrap that behavior with FastAPI,
Jina, or Gradio.

## FastAPI embedding service

Use the bundled `scripts/fastapi_app_template.py` when you need a simple JSON
HTTP endpoint. The template is import-safe: importing it only defines helpers;
it starts Uvicorn only when executed as a script.

### Launch pattern

From the sub-skill root, or by passing the full path to the script from any
current working directory:

```bash
python scripts/fastapi_app_template.py \
  --model-name-or-path shibing624/text2vec-base-chinese \
  --host 127.0.0.1 \
  --port 8001 \
  --device cpu
```

For containers or remote hosts, use `--host 0.0.0.0` only when the surrounding
network policy is correct. For offline deployments, pass a local model directory
as `--model-name-or-path`.

### App factory

The script exposes:

```python
from fastapi_app_template import create_app

app = create_app(model_name_or_path="/models/text2vec-local", device="cpu")
```

`create_app()` does not instantiate `SentenceModel`. The model is loaded lazily
on the first `POST /emb` or explicit `POST /warmup`; this avoids Hugging Face or
other remote model downloads during plain module import and app creation.

### Endpoints

| Method and path | Purpose | Loads model? | Shape |
|---|---|---:|---|
| `GET /healthz` | Liveness and configuration summary. | No | JSON object |
| `GET /readyz` | Readiness summary: `model_loaded` is true only after warmup or first request. | No | JSON object |
| `POST /warmup` | Explicitly load the model and run a one-text embedding probe. | Yes | JSON object with `embedding_dim` |
| `POST /emb` | Encode one text or a batch of texts. | Yes, if not already loaded | JSON object with `emb` |

Primary request bodies for `POST /emb`:

```json
{"input": "如何更换花呗绑定银行卡"}
```

```json
{"input": ["如何更换花呗绑定银行卡", "花呗更改绑定银行卡"]}
```

A raw JSON list of strings is also accepted for batch calls:

```json
["hello", "world"]
```

Response shape follows `SentenceModel.encode`:

- single string input -> `{"emb": [0.1, 0.2, ...]}`
- list input -> `{"emb": [[0.1, 0.2, ...], [0.3, 0.4, ...]]}`

The template normalizes embeddings, matching common cosine-similarity service
usage. If a service needs raw embeddings, make that an explicit endpoint
contract and document it for clients.

### Local model directory with health checks

For a local model directory and no startup network dependency:

1. Package or mount the model files into the runtime image or host.
2. Launch with `--model-name-or-path /path/to/local/model`.
3. Call `GET /healthz`; it should respond without model loading.
4. Call `POST /warmup` when you want to fail fast before sending traffic.
5. Use `GET /readyz` to confirm `model_loaded: true` after warmup.

If the local directory is incomplete, the failure appears on `/warmup` or the
first `/emb`, not during ordinary import or help parsing.

### Client examples

```bash
curl -s -X POST 'http://127.0.0.1:8001/emb' \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}'
```

```bash
curl -s -X POST 'http://127.0.0.1:8001/emb' \
  -H 'Content-Type: application/json' \
  -d '{"input":["hello","world"]}'
```

For browser clients, add CORS middleware only for the origins you intend to
serve. Do not expose a permissive wildcard CORS policy on a public endpoint
without an explicit security review.

## Composing services with text2vec workflows

Keep computation responsibilities separate from transport:

| Service endpoint pattern | Core text2vec logic | Route for details |
|---|---|---|
| `/emb` embedding gateway | `SentenceModel.encode`, model choice, device, normalization | `embeddings` |
| `/score` pair-similarity endpoint | `Similarity.get_score` or vector cosine | `similarity-search` |
| `/search` dense retrieval endpoint | query embedding plus `semantic_search` over stored corpus vectors | `similarity-search` |
| `/search` lexical fallback endpoint | `BM25.get_scores` over raw corpus text | `similarity-search` |

For retrieval applications, a common integration flow is:

1. Use `/emb` or a batch embedding workflow to encode corpus documents.
2. Store vectors and document IDs in the serving layer or vector database.
3. On query, encode the query with the same model and normalization settings.
4. Rank with cosine/dot-product search or text2vec `semantic_search`.
5. Return document IDs, texts, and scores; do not return huge full embedding
   arrays unless the client explicitly needs vectors.

## Jina service pattern

Jina is useful when the deployment needs Flow composition, gRPC/HTTP/WebSocket
frontends, Docker/Kubernetes-style packaging, or multiple models/GPU devices.
The high-level pattern is:

```python
from jina import Flow

flow = Flow(port=50001).add(
    uses="jinahub://Text2vecEncoder",
    uses_with={"model_name": "shibing624/text2vec-base-chinese"},
)

with flow:
    flow.block()  # long-running server; do not run this in normal tests
```

A client posts `Document` objects containing text and reads embeddings from the
returned documents:

```python
from jina import Client
from docarray import Document

client = Client(port=50001)
response = client.post("/", inputs=[Document(text="hello")])
embeddings = response.embeddings
```

Caveats:

- `jinahub://Text2vecEncoder` needs compatible Jina/JinaHub access and network
  availability unless the executor is vendored or replaced by a local executor.
- Jina and DocArray versions must match the executor's expectations.
- `flow.block()` is intentionally a forever server. Verification should use
  parser/import checks, a short-lived smoke service, or an already running test
  deployment rather than waiting on `block()`.
- For multi-model or multi-GPU serving, plan one executor/pod/process per model
  or GPU allocation instead of loading every model into one unbounded process.

## Gradio demo pattern

Use Gradio for interactive demos or stakeholder review. It is not the default
production API because `.launch()` starts a browser-facing, long-running UI.
Wrap it under `if __name__ == "__main__":` and keep the function body thin:

- for embedding previews, call `SentenceModel.encode` and display vector shape
  or a small vector prefix, not full large arrays;
- for pair similarity demos, call `Similarity.get_score` and show the scalar
  score;
- for retrieval demos, call the same search helper used by the service endpoint.

If a Gradio UI becomes business-critical, move the actual model and search logic
into a FastAPI/Jina service and let Gradio call that service as a client.

## Choosing FastAPI, Jina, or Gradio

| Need | Recommended pattern |
|---|---|
| Simple JSON REST endpoint, custom body schema, local/offline model directory | FastAPI template |
| Multi-model or multi-GPU service graph, gRPC/WebSocket, Jina ecosystem tooling | Jina Flow |
| Human-facing quick demo, examples, manual QA | Gradio |
| Batch files, CSV/JSONL outputs, scheduled offline jobs | Route to `embeddings` instead of serving |

When in doubt, start with FastAPI for one model and one endpoint. Switch to Jina
when service composition, protocol support, or model/device routing outweigh the
extra JinaHub/version/network surface.
