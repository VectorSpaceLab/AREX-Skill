---
name: models-and-encoders
description: "Load and validate MTEB models, built-in model metadata,
  SentenceTransformers/CrossEncoder/custom encoder/search protocols, prompts,
  encode kwargs, embedding cache/compression/search wrappers, and optional model
  extras."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MTEB Models and Encoders

Use this sub-skill when the user needs to choose, load, wrap, validate, or troubleshoot a model object for MTEB. This includes built-in MTEB model metadata, fallback Hugging Face/SentenceTransformers loading, CrossEncoder rerankers, custom `EncoderProtocol`/`CrossEncoderProtocol`/`SearchProtocol` implementations, prompt routing, `encode_kwargs`, BM25 baselines, embedding caching, embedding compression, and optional provider extras.

## Route by Need

- **Load a registered or Hub model:** Use `references/model-api.md` for `mteb.get_model`, `mteb.get_model_meta`, `mteb.get_model_metas`, `revision`, `device`, `embed_dim`, `experiment_kwargs`, and optional extras.
- **Build or validate a custom model:** Use `references/custom-encoders.md` and run `scripts/validate_encoder_protocol.py` before evaluation to catch missing `encode`, `predict`, `index`, `search`, `similarity`, or constructor-shape problems.
- **Add prompts or encode options:** Use `references/model-api.md` for `model_prompts`, prompt priority, `PromptType.query`/`PromptType.document`, and passing `encode_kwargs` through `mteb.evaluate`.
- **Cache or compress embeddings:** Use `references/model-api.md` for `CachedEmbeddingWrapper`, `NumpyCache`, `FaissCache`, `CompressionWrapper`, `OutputDType`, and cache-path hygiene.
- **Use search/reranking wrappers:** Use `references/custom-encoders.md` for `SearchEncoderWrapper`, `SearchCrossEncoderWrapper`, BM25 baselines, and when a CrossEncoder requires pre-ranked documents.
- **Fix model failures:** Use `references/troubleshooting.md` for import/install extras, provider packages, private datasets/models, cache/result paths, task filters, CLI/API misuse, and protocol mismatch symptoms.

## Minimal Patterns

```python
import mteb

meta = mteb.get_model_meta("intfloat/multilingual-e5-small")
model = meta.load_model(device="cpu")
# Equivalent eager load:
model = mteb.get_model("intfloat/multilingual-e5-small", device="cpu")
```

```python
import mteb
from sentence_transformers import SentenceTransformer, CrossEncoder

dense_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
```

```python
from mteb.models import CompressionWrapper
from mteb.models.cache_wrappers import CachedEmbeddingWrapper
from mteb.types import OutputDType

model = CachedEmbeddingWrapper(model, cache_path=".mteb-embedding-cache")
model = CompressionWrapper(model, output_dtype=OutputDType.INT8)
```

## Cross-links

- For actually evaluating a loaded model, pass model objects or `ModelMeta` into `../evaluation-workflows/`.
- For adding a new `ModelMeta` implementation to MTEB itself, use `../contributing-to-mteb/`.
- For model cards, result submission, and leaderboard expectations, use `../results-and-leaderboard/`.
