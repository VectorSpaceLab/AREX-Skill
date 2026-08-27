# CrossEncoder Reranking Workflows

## Choose The Right Model Type

Use a CrossEncoder reranker when:

- You already have a shortlist of candidates and need stronger pairwise relevance ordering.
- Query/document interaction matters, such as answer-bearing passage reranking, duplicate detection, or pair classification.
- Latency is acceptable for `len(queries) * len(candidates)` forward passes.

Use a bi-encoder or sparse encoder instead when:

- You need to search a large corpus by precomputing document vectors.
- You need sublinear nearest-neighbor retrieval over thousands to billions of documents.
- The task asks for embeddings, similarity matrices, clustering, or vector DB indexing.

A standard production pattern is: first-stage retriever returns top 20-200 candidates, then `CrossEncoder.rank` reranks that candidate list.

## Pair Scoring Workflow

1. Confirm the task is pair scoring, not embedding.
2. Load a model that matches the task family: MS MARCO/text-ranking for relevance, STS for similarity, Quora for duplicate questions, NLI for entailment-style classification, or a multimodal reranker for media pairs.
3. Prepare pair inputs as a batch of two-element items.
4. Choose output post-processing:
   - single-label relevance/similarity: scalar scores;
   - multi-class classifier: `apply_softmax=True` if probabilities are required;
   - raw logits: acceptable for ranking when only ordering matters.
5. Run `predict` with a conservative `batch_size`, then benchmark higher values.

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/stsb-roberta-base")
pairs = [
    ("It's sunny today.", "It is a bright day."),
    ("It's sunny today.", "The server failed."),
]
scores = model.predict(pairs, batch_size=16)
```

## Rerank Already-Retrieved Hits

Preserve retriever metadata outside the document list and use `corpus_id` to map back after reranking.

```python
from sentence_transformers import CrossEncoder

first_stage_hits = [
    {"id": "doc-42", "text": "Berlin had 3,520,031 registered inhabitants.", "score": 0.83},
    {"id": "doc-07", "text": "Berlin is well known for its museums.", "score": 0.71},
]
query = "How many people live in Berlin?"
documents = [hit["text"] for hit in first_stage_hits]

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
ranked = reranker.rank(query, documents, top_k=5, return_documents=True)

for item in ranked:
    source_hit = first_stage_hits[item["corpus_id"]]
    item["id"] = source_hit["id"]
    item["retriever_score"] = source_hit["score"]
```

Notes:

- `corpus_id` is stable only relative to the provided `documents` list.
- `return_documents=True` is convenient for short strings; for large metadata payloads, keep `return_documents=False` and map by `corpus_id`.
- Do not pass the whole corpus to `rank` unless the corpus is genuinely tiny.
- If first-stage retrieval already emits global IDs, keep those IDs in a parallel list or list of hit dictionaries.

## Prompted Rerankers

Some models save prompts or expect query/document prefixes. Use the constructor or call-time controls deliberately.

```python
model = CrossEncoder(
    "your-reranker",
    prompts={"query": "query: ", "document": "passage: "},
    default_prompt_name="query",
)

scores = model.predict(pairs, prompt="query: ")
```

If a saved prompt hurts a custom task, override with explicit prompts or pass empty prompt values for the relevant prompt names. Confirm the checkpoint's model card before changing prompt behavior.

## Throughput Tuning

- Start with `batch_size=16` or `32`, then increase until memory or latency degrades.
- Use `device="cuda"`, `"mps"`, or another accelerator only when the environment supports it.
- For large offline batches, pass `device=["cuda:0", "cuda:1"]` or reuse `pool = model.start_multi_process_pool(...)` with `predict`/`rank`.
- Set `show_progress_bar=False` for services and tests; enable it for long scripts.
- Long documents are truncated according to tokenizer/processor limits. Set `max_length` at construction or pass `processing_kwargs` per call when supported by the model.

## Multimodal Reranking Workflow

1. Select a multimodal CrossEncoder checkpoint that explicitly supports the required modality pair.
2. Install optional extras needed by that modality.
3. Check support at runtime with `model.modalities` and `model.supports(...)`.
4. Pass each pair element in the format supported by the processor: text strings, local image paths, PIL images, arrays, media dictionaries, or multimodal dictionaries.
5. Keep fallback text-only routing available for environments without media processors or GPU memory.

```python
model = CrossEncoder("Qwen/Qwen3-VL-Reranker-2B")
if not model.supports(("text", "image")):
    raise ValueError("Selected reranker does not support text-image pairs")
ranked = model.rank("green car", ["image-or-path-1", "image-or-path-2"])
```

## Minimal Evaluation Workflow

Use this only as a smoke-level reranker evaluation. Route detailed evaluation design to `../evaluation-and-training/SKILL.md`.

```python
from sentence_transformers.cross_encoder.evaluation import CrossEncoderRerankingEvaluator

samples = [
    {
        "query": "What is Python?",
        "positive": ["Python is a programming language."],
        "negative": ["Java is also a language.", "The sun is a star."],
    }
]
evaluator = CrossEncoderRerankingEvaluator(samples, name="tiny-rerank")
metrics = evaluator(model)
```

Valid evaluator sample shapes:

- `query`, `positive`, and `negative` for positives plus explicit negatives.
- `query`, `positive`, and `documents` for reranking an existing candidate list.
- Provide exactly one of `negative` or `documents`.
- `positive` may be a string or list, but a list is clearer for multiple relevant documents.

## Safe CLI Smoke Helper

The bundled helper adapts the repository CrossEncoder usage and reranking examples into a self-contained CLI:

```bash
python scripts/cross_encoder_rerank_smoke.py --help
python scripts/cross_encoder_rerank_smoke.py \
  --model cross-encoder/ms-marco-MiniLM-L6-v2 \
  --query "How many people live in Berlin?" \
  --documents "Berlin had 3,520,031 registered inhabitants." "Berlin is known for museums." \
  --top-k 2
```

Add `--local-files-only` for offline/cache-only validation. The helper does not download anything for `--help`; model loading happens only when `--model` is supplied.
