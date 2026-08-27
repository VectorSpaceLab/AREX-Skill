# Fine-Tuning Troubleshooting

Start with data validation. Most fast failures come from JSONL shape, score arrays, missing optional training dependencies, CUDA/DeepSpeed mismatch, or launching distributed training with paths or devices that do not match the runtime.

## Invalid JSONL

Symptoms:

- JSON parser errors before training starts.
- `KeyError: 'query'`, `KeyError: 'pos'`, or `KeyError: 'neg'`.
- Assertion failures that `pos` and `neg` are lists.
- Empty negative lists leading to sampling errors.

Checks and fixes:

```bash
python scripts/validate_train_jsonl.py --task embedder data/train.jsonl
python scripts/validate_train_jsonl.py --task reranker data/train.jsonl
```

- Ensure each line is a complete JSON object, not a JSON array split across lines.
- Keep `query` as a non-empty string.
- Keep `pos` and `neg` as non-empty lists of strings.
- Remove blank text entries.
- If a row has no negatives, mine hard negatives, sample negatives from the corpus, or drop the row.
- If `neg` contains a value equal to the query or an exact positive, fix the mined negatives.

## Knowledge Distillation Score Errors

Symptoms:

- Error that `pos_scores` and `neg_scores` are missing when using knowledge distillation.
- Assertion or index errors after score generation.
- Scores present but KD quality looks wrong.

Checks and fixes:

```bash
python scripts/validate_train_jsonl.py --task embedder --knowledge-distillation data/train.scored.jsonl
```

- For KD, every row must include both `pos_scores` and `neg_scores`.
- `len(pos_scores)` must equal `len(pos)` and `len(neg_scores)` must equal `len(neg)`.
- Scores must be numeric values, not strings.
- If a mixed retrieval/classification file has mismatched scores, KD is not allowed. Regenerate teacher scores after final negative mining or remove both score fields and train with `--knowledge_distillation False`.

## Prompt and Type Problems

Symptoms:

- Decoder-only or ICL training formats inputs unexpectedly.
- Classification or clustering rows train poorly after mixing with retrieval rows.
- Same-dataset batching produces surprising batch sizes.

Checks and fixes:

- Keep `prompt` meaningful per row when mixing retrieval, classification, clustering, and STS style data.
- For embedder ICL or same-dataset batching, keep `type` consistent inside each dataset file when possible.
- Use known `type` values such as `normal`, `symmetric_class`, `symmetric_clustering`, `symmetric_sts`, or `only_1neg` when they match the task.
- Name files or directories with the `no_in_batch_neg` suffix when in-batch negatives are not appropriate.
- If using same-dataset batching, keep related rows in separate files or directories instead of mixing unrelated task types in one JSONL.

## Missing Finetune Extras

Symptoms:

- `ModuleNotFoundError: No module named 'deepspeed'`.
- `ModuleNotFoundError` or build errors for flash-attn.
- Training command accepts arguments but fails when DeepSpeed or flash-attn initializes.

Checks and fixes:

- Install the finetune extra in the target environment: `pip install -U "FlagEmbedding[finetune]"`.
- The extra declares DeepSpeed and flash-attn, but flash-attn is tightly coupled to PyTorch, CUDA, compiler, and GPU architecture.
- If flash-attn fails, remove `--use_flash_attn True` and retry only after confirming the stack supports it.
- For broad package import or backend setup issues, route to the root troubleshooting reference.

## Model, Token, and Cache Issues

Symptoms:

- HTTP, authorization, or gated-model errors.
- Repeated downloads or cache misses.
- `trust_remote_code` errors for model families that need custom code.

Checks and fixes:

- Prefer local checkpoint paths or pre-populated caches when the run must be offline.
- Set `cache_dir` to a writable location with enough disk.
- Use a Hugging Face token only when the selected model requires it.
- Enable `--trust_remote_code True` only for model families that require it and only after accepting remote-code risk.
- Do not treat hard-negative mining or teacher-score generation as offline unless every model artifact is local.

## CUDA, DeepSpeed, and Distributed Launch Issues

Symptoms:

- `torchrun` hangs or every process tries to use the same GPU.
- NCCL errors, CUDA out-of-memory, or DeepSpeed initialization failures.
- `--nproc_per_node` exceeds available devices.

Checks and fixes:

- Confirm visible devices before launching and set `--nproc_per_node` to that count.
- Use `CUDA_VISIBLE_DEVICES` to choose devices when needed.
- Start with one node unless multi-node rendezvous settings are explicitly required.
- Ensure the DeepSpeed config file exists in the run directory passed to `--deepspeed`.
- Use stage 0 first for small encoder-only jobs; use stage 1 or other memory strategies only when needed and verified.
- If NCCL fails on a single-machine debug run, retry with one process to separate data/model errors from distributed errors.

## OOM and Length Issues

Symptoms:

- CUDA OOM shortly after the first batch.
- OOM during tokenizer/collator work for long examples.
- Decoder-only jobs fail even with LoRA.

Checks and fixes:

```bash
python scripts/split_jsonl_by_text_length.py \
  --input-path data/train.jsonl \
  --output-dir data/split-by-length \
  --length-mode token-estimate \
  --length-list 0 256 512 1024 2048 4096
```

- Lower `query_max_len`, `passage_max_len`, or reranker `max_len`.
- Lower `per_device_train_batch_size` and increase `gradient_accumulation_steps` if needed.
- Use `sub_batch_size` for embedder training when collated query/passage tensors are too large.
- Keep `pad_to_multiple_of 8` for tensor-core efficiency, but lower lengths first when memory is the blocker.
- Use gradient checkpointing for large models.
- Decoder-only LoRA reduces trainable parameters, but activations can still dominate memory.

## Route Decisions

- Inference-only failures while loading embedders or rerankers belong to sibling `inference` unless they happen inside hard-negative or teacher-score preparation.
- Benchmark and post-training quality questions belong to sibling `evaluation`.
- Environment-wide installation, package import, or backend diagnosis belongs to the root troubleshooting reference.
