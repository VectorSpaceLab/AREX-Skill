# Fine-Tuning Data Formats

FlagEmbedding fine-tuning data is line-delimited JSON. Each line is one training item. The core schema is shared by embedders and rerankers:

```json
{"query": "question or source text", "pos": ["positive passage"], "neg": ["negative passage"]}
```

Required fields:

- `query`: non-empty string.
- `pos`: non-empty list of strings. The trainer samples one positive per item.
- `neg`: non-empty list of strings. The trainer samples `train_group_size - 1` negatives; if too few negatives exist it repeats samples, but an empty list fails.

Optional fields:

- `pos_scores`: list of numeric teacher scores, one per `pos` item.
- `neg_scores`: list of numeric teacher scores, one per `neg` item.
- `prompt`: prompt text. For embedders, it can override `query_instruction_for_retrieval` in query formatting. For decoder-only rerankers, it is used as the prompt appended to query/passage pairs.
- `type`: embedder task type, especially for decoder-only ICL and same-dataset batching. Evidence includes `normal`, `symmetric_class`, `symmetric_clustering`, `symmetric_sts`, and code handles `only_1neg`.

Additional fields are allowed and ignored by the core loaders unless a specialized dataset path reads them. Example evidence includes metadata such as `category`.

## Knowledge Distillation Scores

Use `--knowledge_distillation True` only when every row has both score arrays and the lengths match the text arrays:

```json
{
  "query": "what is restorative justice?",
  "pos": ["Restorative justice repairs harm through accountability."],
  "neg": ["Retributive justice focuses on punishment."],
  "pos_scores": [95.25],
  "neg_scores": [72.5]
}
```

Rules enforced by the training loaders and by the bundled validator:

- `pos_scores` and `neg_scores` must either both be present or both be absent.
- When present, `len(pos_scores) == len(pos)` and `len(neg_scores) == len(neg)`.
- Scores must be numbers, not strings or booleans.
- If KD is off, the loaders remove score columns. Keep scores only if they are valid or strip them before training.

Teacher scores are produced by scoring each `(query, positive)` pair first and each `(query, negative)` pair second. The output contract adds `pos_scores` and `neg_scores` to the original row and preserves the original `query`, `pos`, and `neg` fields.

## Hard Negatives

Hard negatives are non-positive passages retrieved as close neighbors to the query. They usually improve embedding and reranker training, but mining requires an embedder model, FAISS or equivalent nearest-neighbor search, and device/cache planning.

Hard-negative mining workflow option shape, for an approved external
model-loading runner or user-supplied script:

| Option | Example | Meaning |
| --- | --- | --- |
| `input_file` | `train.jsonl` | Source fine-tuning JSONL. |
| `output_file` | `train.mined.jsonl` | JSONL with mined `neg` values. |
| `range_for_sampling` | `2-200` | Neighbor rank window to sample from. |
| `negative_number` | `15` | Target negatives per row. |
| `embedder_name_or_path` | `BAAI/bge-base-en-v1.5` | Embedder model id or local checkpoint. |
| `embedder_model_class` | `encoder-only-base` | Explicit model class when auto detection is insufficient. |
| `normalize_embeddings` | `True` | Whether to normalize vectors before search. |
| `pooling_method` | `cls` | Encoder pooling method for compatible checkpoints. |
| `use_fp16` | `True` | Accelerator precision choice. |
| `devices` | `cuda:0` | Device list for model inference. |
| `cache_dir` | `./cache/model` | Model cache directory chosen by the runtime. |

Important flags and pitfalls:

- `range_for_sampling` is an inclusive-style rank window written as `left-right` in the source helper. Higher ranges usually make negatives easier.
- `negative_number` is the target number of negatives per row.
- `candidate_pool` can replace the implicit corpus. A compatible pool is JSONL with a `text` field per line.
- `use_gpu_for_searching` requires FAISS GPU support and CUDA-compatible hardware.
- `embedder_name_or_path` may download model files unless it is a local checkpoint or already cached.
- `embedder_model_class` should match the model family when automatic detection is not enough: `encoder-only-base`, `encoder-only-m3`, `decoder-only-base`, or `decoder-only-icl`.
- The mined `neg` values should not equal the `query` text or any exact `pos` text. The bundled validator treats such overlaps as errors.

This sub-skill does not bundle a runnable hard-negative miner because the original workflow loads models and FAISS and can use network, caches, and GPUs. Use the option shape above to configure a separate approved model-loading workflow after the user approves those dependencies.

## Teacher-Score Generation

Reranker-score workflow option shape, for an approved external model-loading
runner or user-supplied script:

| Option | Example | Meaning |
| --- | --- | --- |
| `input_file` | `train.mined.jsonl` | Source JSONL after negative mining. |
| `output_file` | `train.scored.jsonl` | JSONL with added `pos_scores` and `neg_scores`. |
| `reranker_name_or_path` | `BAAI/bge-reranker-v2-m3` | Reranker model id or local checkpoint. |
| `reranker_model_class` | `encoder-only-base` | Explicit class when auto detection is insufficient. |
| `devices` | `cuda:0 cuda:1` | Devices for reranker inference. |
| `cache_dir` | `./cache/model` | Model cache directory chosen by the runtime. |
| `reranker_query_max_length` | `512` | Query-side truncation length. |
| `reranker_max_length` | `1024` | Reranker packed/passage truncation length. |

Useful flags and dependencies:

- `reranker_name_or_path` may be a Hugging Face id or local checkpoint and may require a token/cache.
- `reranker_model_class` can be `encoder-only-base`, `decoder-only-base`, `decoder-only-layerwise`, or `decoder-only-lightweight`; `auto` is common when the runtime can infer the class.
- `reranker_peft_path` points to an adapter checkpoint when scoring with PEFT.
- `use_fp16`, `use_bf16`, `devices`, `trust_remote_code`, `cache_dir`, and batch/length settings affect model loading and memory.
- `normalize`, `prompt`, `cutoff_layers`, `compress_ratio`, and `compress_layers` change scoring behavior for specialized rerankers.

Do not enable `--knowledge_distillation True` in training until `scripts/validate_train_jsonl.py --knowledge-distillation` passes on the final scored JSONL.

## Prompt and Type Handling

Embedder query formatting:

- If `--query_instruction_for_retrieval` is set, the trainer formats the query with `query_instruction_format`.
- When a row has `prompt`, that per-row prompt is used instead of the global query instruction.
- For symmetric data types such as `symmetric_class`, `symmetric_clustering`, and `symmetric_sts`, same-dataset batching can format passages with the query instruction path.

Reranker prompt formatting:

- Encoder-only rerankers tokenize a query/passage pair.
- Decoder-only rerankers build a sequence shaped like query, separator token, passage, separator token, prompt.
- Optional per-row `query_prompt` and `passage_prompt` fields are honored by the dataset code when query or passage instruction flags are enabled, but the public minimal schema uses `prompt`.

Same-dataset batching notes:

- `same_dataset_within_batch` keeps each batch within one dataset source.
- A file or directory name ending in `no_in_batch_neg` marks data where in-batch negatives should not be used.
- Optional per-row `batch_size` can override the default batch size for that dataset.
- `small_threshold` and `drop_threshold` merge or drop small datasets in directory inputs.

## Offline Validation

Run the bundled validator before building a command:

```bash
python scripts/validate_train_jsonl.py --task embedder train.jsonl
python scripts/validate_train_jsonl.py --task reranker --knowledge-distillation train.scored.jsonl
```

Common decisions:

- Missing `neg`: not trainable as-is. Mine negatives, sample negatives from the corpus, or remove the row.
- Mismatched score lengths: KD is not allowed until scores are regenerated or removed.
- Mixed retrieval/classification rows: allowed when each row has valid `query`, `pos`, and `neg`; for bge-en-icl or same-dataset batching, keep meaningful `prompt` and `type` values.
