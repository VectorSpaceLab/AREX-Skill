# CrossEncoder API Reference

## Imports And Construction

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L6-v2",
    device="cpu",                 # or "cuda", "mps", "npu"
    local_files_only=False,
)
```

Important constructor controls:

- `model_name_or_path`: local directory or Hugging Face model id. A remote id may download unless `local_files_only=True`.
- `device`: compute device for inference. If `model_kwargs={"device_map": ...}` is used, the device map controls placement.
- `prompts` / `default_prompt_name`: prompt prefixes saved on or supplied to the model. Pass empty strings for query/document prompt keys to disable saved prompts when needed.
- `trust_remote_code`: only set for repositories whose code you have reviewed.
- `revision`, `token`, `cache_folder`, `local_files_only`: reproducibility, private model, cache, and offline controls.
- `model_kwargs`: forwarded to the underlying Transformers model; common values include `torch_dtype`, `attn_implementation`, `device_map`, and backend-specific `provider`, `file_name`, or `export`.
- `processor_kwargs`: forwarded to the tokenizer/processor; `max_length` sets `processor_kwargs["model_max_length"]`.
- `config_kwargs`: forwarded to config loading; use for options such as `classifier_dropout` or `num_labels`.
- `backend`: `"torch"`, `"onnx"`, or `"openvino"`. Export and optimization details belong in `../backend-export-optimization/SKILL.md`.
- `num_labels`: `1` for regression/reranking scores; `>1` for pair classification logits.
- `activation_fn`: applied in `predict`. Defaults to `torch.nn.Sigmoid()` for `num_labels == 1`, otherwise `torch.nn.Identity()`.

## `predict`: Score Explicit Pairs

Use `predict` when you already have pairs or when the model is a classifier with multiple labels.

```python
pairs = [
    ("query", "candidate A"),
    ("query", "candidate B"),
]
scores = model.predict(pairs, batch_size=32, convert_to_numpy=True)
```

Key arguments:

- `inputs`: one pair such as `[query, document]` or a batch such as `[(query, doc1), (query, doc2)]`. Pair elements may be strings, supported media objects, or multimodal dictionaries.
- `prompt_name` / `prompt`: apply a named prompt or explicit prompt for this call.
- `batch_size`: larger can improve throughput until memory or latency limits are hit.
- `show_progress_bar`: defaults based on logging level; set explicitly for scripts.
- `activation_fn`: overrides `model.activation_fn` for this call.
- `apply_softmax`: for `num_labels > 1`, converts class logits to probabilities along each row.
- `convert_to_numpy` / `convert_to_tensor`: choose output type. `convert_to_tensor=True` takes precedence.
- `device`: single device string or a list of devices. A device list triggers multiprocessing.
- `pool` / `chunk_size`: reuse or tune a multiprocessing pool for large batches.
- `processing_kwargs`: forwarded to preprocessing, for example per-call truncation/max-length processor settings.

Shape rules verified by tests:

- One pair like `["q", "d"]` returns a scalar-like score for single-label models or one vector for multi-label models.
- A batch like `[["q", "d1"], ["q", "d2"]]` returns one score/vector per pair.
- Empty inputs return an empty numpy array, tensor, or list according to conversion settings.
- A 1D numpy string array is treated as one pair; a 2D numpy string array is treated as a batch.

## `rank`: Rerank Documents For One Query

Use `rank` for a single query and an already-filtered candidate document list.

```python
results = model.rank(
    query="query text",
    documents=["candidate A", "candidate B"],
    top_k=10,
    return_documents=True,
    batch_size=32,
)
```

Return format:

```python
[
    {"corpus_id": 0, "score": 8.6, "text": "candidate A"},
    {"corpus_id": 1, "score": -4.3, "text": "candidate B"},
]
```

Behavior and constraints:

- `rank` creates `[query, doc]` pairs internally, calls `predict`, sorts by descending score, and returns `results[:top_k]`.
- `corpus_id` is the index in the provided `documents` list, not a global corpus identifier. Keep an external mapping if candidates came from a retriever.
- `return_documents=True` adds the original document under `text`; it can be memory-heavy for large payloads.
- `top_k=None` returns all candidates sorted.
- `rank` raises `ValueError` for models with `num_labels != 1`; use `predict` and class-specific post-processing for NLI or other pair classifiers.

## Activation, Softmax, And Labels

Use these rules to avoid the most common output mistakes:

- Reranking/regression: set or confirm `num_labels=1`. Scores are one scalar per pair and `rank` is valid.
- Pair classification: set `num_labels` to the number of classes. Use `predict`, not `rank`.
- `activation_fn` applies to logits before optional softmax. Default is sigmoid for single-label models and identity for multi-label models.
- `apply_softmax=True` only changes outputs when scores have more than one dimension, usually multi-class classifiers.
- MS MARCO rerankers commonly return raw logits. Use `activation_fn=torch.nn.Sigmoid()` if a downstream threshold expects 0-1 values; leave logits if only ordering matters.
- If labels are `contradiction`, `entailment`, `neutral`, map `scores.argmax(axis=1)` to the model's documented class order after using `apply_softmax=True` when probabilities are needed.

## Multimodal CrossEncoders

Some checkpoints support pairs involving text, images, audio, video, or multimodal dictionaries.

```python
print(model.modalities)
print(model.supports("image"))
print(model.supports(("text", "image")))
```

Use multimodal rerankers only when the selected checkpoint documents support for the requested modalities. Install matching extras such as `sentence-transformers[image]`, `sentence-transformers[audio]`, or `sentence-transformers[video]` when processors require them.

## Training And Evaluation Touchpoints

For reranker fine-tuning basics:

- Rerankers usually use `num_labels=1` and labeled query-document pairs or triplets.
- Pair classifiers use `num_labels > 1` and classification labels.
- `CrossEncoderRerankingEvaluator` accepts samples with `query`, `positive`, and exactly one of `negative` or `documents`; it reports metrics such as MAP, MRR, and NDCG.
- Detailed loss, trainer, evaluator, sampler, and dataset-column routing belongs in `../evaluation-and-training/SKILL.md`.
