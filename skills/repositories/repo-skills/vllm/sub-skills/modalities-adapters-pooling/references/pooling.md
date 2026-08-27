# Pooling, Embeddings, Classification, Score, and Rerank

Use this reference when the desired output is not generated text: embeddings, class probabilities/logits, scalar similarity scores, ranked documents, rewards, token labels, or token vectors.

## Runner and task selection

Pooling APIs require a pooling-capable model and `runner="pooling"` or equivalent CLI/server conversion.

```python
from vllm import LLM

llm = LLM(
    model="embedding-or-reranker-model",
    runner="pooling",
)
```

If a model does not natively expose the requested pooling task, vLLM errors guide the conversion:

- Embedding unsupported: try `--convert embed` or `LLM(..., convert="embed")` when the model supports conversion.
- Classification unsupported: try `--convert classify` or `LLM(..., convert="classify")` when the model supports conversion.
- Wrong pooling task: set `pooling_task` on the call or configure `PoolerConfig(task="...")` at initialization.

Supported pooling task names include `embed`, `classify`, `score`-style cross encoder tasks, `token_embed`, `token_classify`, reward/classification variants, and `plugin` for custom IO processors.

## Offline embedding

```python
outputs = llm.embed(["hello", "goodbye"])
embedding = outputs[0].outputs.embedding
hidden_size = outputs[0].outputs.hidden_size
```

Output contract:

- `LLM.embed(...)` returns `list[EmbeddingRequestOutput]`.
- `EmbeddingRequestOutput.outputs.embedding` is a `list[float]`.
- Conversion requires pooled data to be a one-dimensional vector. If the tensor is not 1-D, `EmbeddingOutput.from_base` raises `ValueError("pooled_data should be a 1-D embedding vector")`.

## Offline classification

```python
outputs = llm.classify(["text to classify"])
probs = outputs[0].outputs.probs
num_classes = outputs[0].outputs.num_classes
```

Output contract:

- `LLM.classify(...)` returns `list[ClassificationRequestOutput]`.
- `ClassificationRequestOutput.outputs.probs` is a `list[float]` with length equal to the class count.
- Conversion requires a one-dimensional probability/logit vector. If the tensor is not 1-D, `ClassificationOutput.from_base` raises `ValueError("pooled_data should be a 1-D probability vector")`.

## Offline score / pair similarity

```python
outputs = llm.score(
    "query text",
    ["candidate A", "candidate B"],
)
scores = [item.outputs.score for item in outputs]
```

Input cardinality:

- `1 -> 1`: one query and one document/item.
- `1 -> N`: one query replicated across many documents/items.
- `N -> N`: aligned query/document lists of equal length.

Multimodal score inputs use `ScoreMultiModalParam` shape:

```python
query = {"content": [{"type": "text", "text": "find similar image"}]}
doc = {"content": [
    {"type": "text", "text": "candidate"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
]}
outputs = llm.score(query, [doc])
score = outputs[0].outputs.score
```

Output contract:

- `LLM.score(...)` returns `list[ScoringRequestOutput]`.
- `ScoringRequestOutput.outputs.score` is a scalar float.
- Conversion squeezes pooled data and requires a scalar. If the tensor is not scalar after squeeze, `ScoringOutput.from_base` raises `ValueError("pooled_data should be a scalar score")`.
- Cross-encoder scoring requires compatible model config, commonly `num_labels == 1` for scalar scoring.

## Generic `LLM.encode`

Use `LLM.encode(..., pooling_task="...")` when the specialized method does not cover the task:

```python
from vllm import PoolingParams

outputs = llm.encode(
    ["token-level request"],
    pooling_task="token_embed",
    pooling_params=PoolingParams(),
)
raw_tensor = outputs[0].outputs.data
```

`LLM.encode` returns `list[PoolingRequestOutput]` with raw `PoolingOutput.data`. Inspect tensor rank and meaning before converting. This is the correct path for token embedding, token classification, rewards, and plugins when no specialized wrapper exists.

## Online endpoints

When serving a pooling model, vLLM exposes OpenAI-compatible and additional pooling endpoints depending on model support and router registration:

- `/v1/embeddings`: embedding vectors in OpenAI-compatible response shape.
- `/pooling`: raw pooling output for supported pooling models.
- `/classify`: classification response with per-input probability/logit data.
- `/score` and `/v1/score`: scalar pair scores.
- `/rerank`, `/v1/rerank`, and `/v2/rerank`: ranked document results.

Rerank request shape:

```json
{
  "model": "reranker-model",
  "query": "what is vLLM?",
  "documents": ["doc A", "doc B"],
  "top_n": 2
}
```

Score request shape can use query/document-style fields or generic `data_1`/`data_2`, depending on the endpoint version:

```json
{
  "model": "score-model",
  "text_1": "query",
  "text_2": ["candidate A", "candidate B"]
}
```

## Multimodal pooling

Vision embedding, vision classification, and vision rerank/score use the same media safety rules as generation. For online flows, content parts should use `image_url`/video parts plus text. For offline flows, pass prompt objects or score multimodal params with `content` lists. Validate media URLs with the bundled `scripts/validate_multimodal_payload.py` helper before debugging model behavior.

## Output extraction table

| API | Returned object | Extract | Required shape |
| --- | --- | --- | --- |
| `LLM.generate` | `RequestOutput` | `outputs[0].outputs[0].text` | generated sequence(s) |
| `LLM.embed` | `EmbeddingRequestOutput` | `outputs[0].outputs.embedding` | 1-D vector |
| `LLM.classify` | `ClassificationRequestOutput` | `outputs[0].outputs.probs` | 1-D class vector |
| `LLM.score` | `ScoringRequestOutput` | `outputs[0].outputs.score` | scalar after squeeze |
| `LLM.encode` | `PoolingRequestOutput` | `outputs[0].outputs.data` | task-specific tensor |
| `/v1/embeddings` | JSON response | `data[].embedding` | 1-D vector |
| `/rerank` | JSON response | `results[].relevance_score` | scalar per document |
| `/score` | JSON response | `data[].score` | scalar per pair |

## Validation workflow

1. Decide whether the user needs text generation or a pooling task.
2. Confirm the model supports that task and modality.
3. Use `runner="pooling"` for offline pooling, or start the server with a pooling-capable model/conversion.
4. Select the narrowest API: `embed`, `classify`, `score`, `rerank`, or `encode` for raw/token/plugin tasks.
5. Validate output rank before converting or serializing. Report shape mismatch as an API/task mismatch, not a generic tensor bug.
