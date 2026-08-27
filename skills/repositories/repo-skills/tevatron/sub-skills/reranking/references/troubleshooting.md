# Reranker Troubleshooting

## Pair or Triple Format Mistakes

Symptoms:

- `KeyError: 'query'`, `KeyError: 'positive_passages'`, `KeyError: 'negative_passages'`, `KeyError: 'docid'`, or `KeyError: 'title'`.
- Training runs but loss is meaningless or unstable.
- Rerank output has unexpected query/document ids, duplicate rows, or missing queries.

Checks:

- Training JSONL rows need `query`, `positive_passages`, and `negative_passages`.
- Inference JSONL rows need `query_id`, `query`, `docid`, `title`, and `text`.
- Passage lists contain objects with `title` and `text`; use `""` for missing titles.
- Pairwise rerank input has one query-document candidate per line, not one query with a list of documents.
- The positive passage is first in each training group because target labels are all zero.

Fixes:

- Rebuild inference JSONL with `scripts/prepare_rerank_input.py` and inspect the first few rows.
- For training, create a tiny one-query fixture and confirm `train_group_size` equals one positive plus intended negatives.
- Do not feed first-stage retriever training triples directly into reranker inference; convert first-stage runs to pairwise rerank rows first.

## `train_group_size` and Grouped Logits

Symptoms:

- Shape mismatch while reshaping logits.
- Loss does not improve despite plausible examples.
- A command uses `--train_group_size` that does not match grouped training intent.

Cause:

`RerankerTrainDataset` emits `train_group_size` flattened pair strings per query. `RerankerModel` reshapes flattened logits to `(per_device_train_batch_size, -1)` and applies cross entropy with target index `0`.

Fixes:

- Keep `--train_group_size` equal to one positive plus the number of negatives selected per query.
- Do not use `train_group_size=1` except for plumbing checks.
- If memory is the problem, reduce `--per_device_train_batch_size` or `--rerank_max_len`, or increase `--gradient_accumulation_steps`; do not silently reduce group size unless that is the intended ranking objective.
- If a custom dataset pre-expands pairs differently, rewrite it to return one grouped row per query.

## LoRA Load, Merge, or Target Mismatch

Symptoms:

- `ModuleNotFoundError: No module named 'peft'`.
- Missing or unexpected adapter keys.
- RankLLaMA command loads but scores are nonsensical.
- Errors mentioning target modules such as `q_proj`, `v_proj`, or `gate_proj`.

Checks:

- Install `peft` for any `--lora` or `--lora_name_or_path` workflow.
- Use the same base model family for adapter training and adapter inference.
- Use `--lora_target_modules` names that exist in the selected base architecture.
- For adapter checkpoints, pass the base model to `--model_name_or_path` and adapter path/name to `--lora_name_or_path`.
- For merged sequence-classification checkpoints, omit `--lora_name_or_path`.

Notes:

- Tevatron inference merges loaded LoRA adapters before scoring.
- Large LLaMA/Mistral adapters can require gated model access, GPU memory, and compatible `transformers`, `peft`, and `torch` versions.

## Missing `torch`, `peft`, or GPU Runtime

Symptoms:

- `ModuleNotFoundError: No module named 'torch'` when importing reranker dataset/model/driver modules.
- `ModuleNotFoundError: No module named 'peft'` when using LoRA.
- CUDA out-of-memory, unsupported precision, or FlashAttention-related errors.

Fixes:

- Install `torch` appropriate for the target CPU/GPU platform before running Tevatron reranker drivers.
- Install `peft` only when using LoRA.
- Reduce `--per_device_eval_batch_size`, `--per_device_train_batch_size`, or `--rerank_max_len` for memory pressure.
- Disable `--fp16`/`--bf16` if the selected hardware does not support the precision.
- For large models, use LoRA, gradient checkpointing, and tiny local fixtures for command validation before full runs.

## Score Output Formatting

Symptoms:

- Evaluation tool rejects rerank output.
- Downstream script expects TREC or MS MARCO format.
- Scores look unbounded, negative, or not probability-like.

Facts:

- `tevatron.reranker.driver.rerank` writes `query_id<TAB>docid<TAB>score`.
- Rows are sorted by descending score within each query.
- Scores are raw sequence-classification logits, not probabilities.
- The incoming first-stage retrieval score in rerank input JSONL is not used by the model.

Fixes:

- Convert to the evaluator's required run format before evaluation.
- Compare reranker scores only within the same query.
- Keep original retrieval scores in the input JSONL for debugging, but do not expect them to affect Tevatron rerank output.

## Cache, Model Download, or Dataset Download Failures

Symptoms:

- Hugging Face auth or network errors.
- Dataset split not found.
- Model/tokenizer path cannot be resolved.
- RankLLaMA/LLaMA/Mistral access denied.

Fixes:

- Use local JSONL with `--dataset_name json --dataset_path <file> --dataset_split train` for reproducible offline tests.
- Set `--cache_dir` for models and `--dataset_cache_dir` for datasets when using shared caches.
- Check gated model access for LLaMA/Mistral/RankLLaMA models.
- Validate tiny local fixtures before launching large downloads.

## Rerank Driver Rejects Multi-GPU Inference

Symptom:

- `NotImplementedError: Multi-GPU encoding is not supported.`

Fixes:

- Run rerank inference on one process/device.
- Split the input JSONL externally, or use `--dataset_number_of_shards` and `--dataset_shard_index` across independent single-device jobs, then concatenate and sort or validate outputs per query.

## Training Sharding Bug

Symptom:

- Attribute error involving `encode_data` when using dataset sharding for reranker training.

Cause:

The inspected Tevatron training dataset sharding branch references `self.encode_data` rather than `self.train_data`.

Fixes:

- Avoid `--dataset_number_of_shards > 1` in reranker training for this package version.
- If sharding is required, pre-shard JSONL files before training and pass one shard as `--dataset_path`.
- Inference sharding uses the inference dataset and is the safer built-in sharding path.

## Original Format Script Parsing Pitfall

Symptom:

- A four-column run line is parsed as if it were a six-column TREC line, or an unfamiliar run format silently assigns the wrong document id or score.

Cause:

One source helper used independent `if` plus `else` branches for line-length checks. That can mis-handle four-column lines.

Fixes:

- Prefer this sub-skill's `scripts/prepare_rerank_input.py` for local fixtures and adapted run files.
- Use `--strict` when missing query/doc ids should fail rather than skip.
- Inspect the generated JSONL and confirm `query_id`, `docid`, `query`, `title`, `text`, and optional `score` match the source fixtures.
