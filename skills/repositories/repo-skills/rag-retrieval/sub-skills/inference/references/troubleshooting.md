# Inference troubleshooting

Use this guide when `rag_retrieval.Reranker` inference does not behave as expected.

## `model_type` is unsupported

Symptom: `Reranker(..., model_type="...")` prints a message like `Model type is not support` and returns `None`.

Cause: explicit `model_type` is mapped only for `"cross-encoder"`, `"llm"`, and `"colbert"`. Anything else is treated as unsupported.

Fix:

```python
ranker = Reranker(model_name, model_type="cross-encoder", verbose=0)
# or
ranker = Reranker(model_name, model_type="llm", verbose=0)

if ranker is None:
    raise RuntimeError("rag_retrieval did not create a ranker")
```

Choose `cross-encoder` for sequence-classification rerankers and `llm` for causal-LM rerankers.

## ColBERT fails despite docs or mappings

Symptom: `Reranker("BAAI/bge-m3", model_type="colbert")` or auto-detected `BAAI/bge-m3` prints a dependency-style message and returns `None`.

Cause: `model_type="colbert"` maps to `ColBERTRanker`, but the current package registers only `CorssEncoderRanker` and `LLMRanker`. The ColBERT ranker import/registration is commented out.

Fix:

- Do not use this package version for ColBERT inference.
- For BGE cross-encoder inference, use a supported model such as `BAAI/bge-reranker-v2-m3`, not `BAAI/bge-m3`.
- If a user asks why ColBERT fails, explain that the mapping name exists but the inference implementation is not registered.

## Unexpected model downloads

Symptom: constructing `Reranker(...)` attempts to contact Hugging Face or load large model files.

Cause: `Reranker` immediately instantiates the selected ranker; registered rankers call `AutoTokenizer.from_pretrained` and either `AutoModelForSequenceClassification.from_pretrained` or `AutoModelForCausalLM.from_pretrained`.

Fix:

- For no-download checks, run `python scripts/reranker_api_smoke.py` from this sub-skill directory or inspect signatures instead of constructing `Reranker`.
- For real inference without downloads, pass a local model directory supplied by the user.
- For LLM rankers, remember that the package uses `trust_remote_code=True`; only load trusted models.

## Device selection surprises

Symptom: model loads on an unexpected accelerator or CPU.

Cause: when `device` is omitted, the helper prefers CUDA, then MPS, then NPU, then CPU.

Fix:

```python
ranker = Reranker(model_name, model_type="cross-encoder", device="cpu", verbose=0)
ranker = Reranker(model_name, model_type="cross-encoder", device="cuda:0", dtype="fp16", verbose=0)
```

If CUDA/MPS/NPU is selected but not usable in the runtime, set `device="cpu"` for diagnostics.

## Dtype issues

Symptom: fp16/bf16 fails or silently becomes float32.

Cause: CPU forces float32. Otherwise `dtype="fp16"`/`"float16"` maps to `torch.float16`, `dtype="bf16"`/`"bfloat16"` maps to `torch.bfloat16`, and all other values map to float32.

Fix:

- Use `dtype="fp16"` only on hardware and models that support it.
- Use `dtype="bf16"` only when the accelerator supports bf16.
- Use `device="cpu"` or omit `dtype` for conservative debugging.

## Cross-encoder query too long

Symptom: `max_score_slice` reranking raises `Your query is too long! Please make sure your query less than 400 tokens!`

Cause: cross-encoder long-document preprocessing computes `max_doc_inputs_length = max_length - len(query_tokens) - 2` and asserts that it is greater than 100.

Fix:

- Shorten the query.
- Increase `max_length` if the model supports it.
- Use `long_doc_process_strategy="max_length_truncation"` for a fast diagnostic, understanding it may miss relevant later text.

## Empty docs return a dict

Symptom: code expects `RankedResults` but receives `{"rerank_docs": [], "rerank_scores": []}`.

Cause: both cross-encoder and LLM `rerank` methods filter docs to non-empty strings and return the legacy dict when the query is empty/`None` or no docs remain.

Fix:

```python
ranked = ranker.rerank(query, docs)
if isinstance(ranked, dict):
    results = []
else:
    results = ranked.results
```

Sanitize inputs upstream if callers need stable mapping to external document ids.

## BCE scores look normalized

Symptom: BCE reranker scores are between 0 and 1 even with `normalize=False`.

Cause: cross-encoder scoring applies sigmoid when `"bce"` appears in `model_name_or_path`, regardless of the `normalize` flag.

Fix: treat BCE scores as already sigmoid-normalized. For BGE cross-encoder models, set `normalize=True` if a 0-1 range is desired.

## LLM prompt does not change scores as expected

Symptom: prompt tuning appears ineffective or changes token budget unexpectedly.

Cause: LLM scoring formats inputs as `A: {query}`, `B: {passage}`, appends the prompt, and scores the final `Yes` token logit for non-layerwise models. Very long prompts reduce practical context and may change padding length.

Fix:

- Keep prompts concise and binary: tell the model to answer `Yes` or `No`.
- Use the same prompt for `compute_score` and `rerank` when comparing results.
- Use `normalize=True` only if downstream code expects sigmoid probabilities rather than raw logits.

## MiniCPM cutoff layers are ignored or fail

Symptom: `cutoff_layers` appears unused, or a model call complains about cutoff arguments.

Cause: the package passes `cutoff_layers` only when `"layerwise"` appears in `model_name_or_path`. Non-layerwise LLM rankers are called without it.

Fix:

- Use `cutoff_layers=[28]` or another intended list only for layerwise models such as `BAAI/bge-reranker-v2-minicpm-layerwise`.
- Do not pass layerwise expectations to Gemma-style rankers.

## Pydantic deprecation warnings

Symptom: importing or constructing result objects emits warnings about `@validator` under newer Pydantic versions.

Cause: `Result` uses Pydantic's legacy `@validator` style. This is a warning-level compatibility issue in many environments, not an inference failure.

Fix:

- Suppress warnings only in caller-owned test/logging code if needed.
- Do not edit runtime package internals from a user task unless specifically asked.
- Validate behavior with `Result(doc_id=0, text="x", score=1.0, rank=1)` and `RankedResults(...)` if result construction is in doubt.

## `Result` validation error

Symptom: constructing `Result(doc_id=..., text=...)` raises a validation error.

Cause: `Result` requires at least one of `score` or `rank`.

Fix:

```python
from rag_retrieval.infer.reranker_models.result import Result

Result(doc_id=0, text="doc", score=0.5)
Result(doc_id=0, text="doc", rank=1)
```

## Progress bars in automated output

Symptom: scoring emits tqdm progress bars.

Cause: `compute_score` defaults `enable_tqdm=True`. `rerank` calls internal scoring paths without exposing `enable_tqdm`.

Fix:

- For `compute_score`, pass `enable_tqdm=False`.
- For `rerank`, reduce noisy package prints with `verbose=0`; progress bars are not used in the internal rerank batch loops.
