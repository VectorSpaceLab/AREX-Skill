# Reranker Arguments Reference

Tevatron reranker drivers parse three groups: `tevatron.reranker.arguments.ModelArguments`, `tevatron.reranker.arguments.DataArguments`, and Hugging Face `TrainingArguments`. The installed package identifies as Tevatron `0.0.1`; reranker argument dataclasses import in a minimal environment, while actual reranker dataset/model/driver execution requires optional PyTorch.

## Model Arguments

| Argument | Default | Use |
| --- | --- | --- |
| `--model_name_or_path` | required | Base model, trained reranker checkpoint, or merged sequence-classification checkpoint. |
| `--config_name` | unset | Optional config path/name when different from the model. |
| `--tokenizer_name` | unset | Optional tokenizer path/name; defaults to `model_name_or_path`. |
| `--cache_dir` | unset | Hugging Face model/config/tokenizer cache directory. |
| `--lora` | `false` | Train a new LoRA adapter through `peft`. |
| `--lora_name_or_path` | unset | Load an existing LoRA adapter. In inference, Tevatron merges it into the base model before scoring. |
| `--lora_r` | `8` | Rank for new LoRA adapters. |
| `--lora_alpha` | `64` | Alpha for new LoRA adapters. |
| `--lora_dropout` | `0.1` | Dropout for new LoRA adapters. |
| `--lora_target_modules` | `q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj` | Comma-separated module names for adapter injection. |

Implementation facts:

- `RerankerModel` wraps `AutoModelForSequenceClassification` and expects one logit per pair.
- If the loaded model config lacks `pad_token_id`, Tevatron sets it to `0` in inference and to tokenizer fallback values in training.
- New LoRA training uses `TaskType.SEQ_CLS` and `target_modules` split on commas.
- DeepSpeed ZeRO-3 save logic writes LoRA adapter weights separately when enabled.

## Data Arguments

| Argument | Default | Use |
| --- | --- | --- |
| `--dataset_name` | `json` | Hugging Face dataset name or loader type. Use `json` for local JSONL. |
| `--dataset_config` | unset | Optional dataset config/subset. |
| `--dataset_path` | unset | Local data file or directory passed as `data_files`. |
| `--dataset_split` | `train` | Dataset split to load. For local JSONL, use `train`. |
| `--dataset_cache_dir` | unset | Hugging Face dataset cache directory. |
| `--dataset_number_of_shards` | `1` | Split dataset for sharded processing. Safer for inference than training in this package version. |
| `--dataset_shard_index` | `0` | Shard index to process. |
| `--train_group_size` | `8` | Number of passages emitted per query group during training. |
| `--positive_passage_no_shuffle` | `false` | Always choose the first positive passage instead of epoch-dependent rotation. |
| `--negative_passage_no_shuffle` | `false` | Always choose the first `train_group_size - 1` negatives instead of shuffled epoch-dependent sampling. |
| `--rerank_output_path` | unset | Required output TSV path for `tevatron.reranker.driver.rerank`. |
| `--rerank_max_len` | `512` | Maximum total token length for each concatenated query-passage sequence. |
| `--query_prefix` | empty | Text prepended before the query, often `query: ` for RankLLaMA-style models. |
| `--passage_prefix` | empty | Text prepended before title/passage text, often `document: ` for RankLLaMA-style models. |
| `--append_eos_token` | `false` | Append tokenizer EOS after truncation; used by some LLaMA-style workflows. |
| `--pad_to_multiple_of` | `16` | Padding multiple used by reranker collators. |

Implementation caution: the inspected training dataset sharding branch references an internal `encode_data` attribute instead of `train_data`. Avoid `--dataset_number_of_shards > 1` in reranker training for this package version. Pre-shard JSONL files externally if training sharding is necessary. Inference sharding uses `inference_data` and is the safer built-in path.

## Training JSONL Fields

Each training row should contain one query group:

```json
{
  "query": "what is neural reranking?",
  "positive_passages": [
    {"title": "Reranking", "text": "A cross encoder scores query document pairs."}
  ],
  "negative_passages": [
    {"title": "Unrelated", "text": "This passage is not relevant."}
  ]
}
```

Rules:

- `positive_passages` and `negative_passages` must be lists.
- Every passage object should include `title` and `text`; use an empty string for missing titles.
- Tevatron selects one positive and then `train_group_size - 1` negatives.
- The positive formatted pair is always first and target label `0` is used for every query.
- If there are too few negatives, Tevatron samples with replacement; if there are no negatives and `train_group_size > 1`, training cannot build the group correctly.
- `train_group_size=1` produces positive-only groups and is usually only useful for plumbing tests, not ranking quality.

## Inference JSONL Fields

Each rerank row should contain one query-document candidate:

```json
{
  "query_id": "q1",
  "query": "what is neural reranking?",
  "docid": "d1",
  "title": "Reranking",
  "text": "A cross encoder scores query document pairs.",
  "score": 12.3
}
```

Rules:

- `query_id`, `query`, `docid`, `title`, and `text` are required by `RerankerInferenceDataset`.
- `score` is optional and ignored by the model; keep it only for auditing first-stage retrieval.
- One row equals one candidate. Do not write one query row with a list of documents.
- Duplicate query-document rows produce duplicate scoring rows; deduplicate before inference if needed.

## TrainingArguments That Matter Most

| Argument | Why it matters |
| --- | --- |
| `--output_dir` | Required by Hugging Face training/inference argument parsing; training saves model/tokenizer here. |
| `--do_train` | Standard `TrainingArguments` flag indicating training intent; include it in train command plans. |
| `--overwrite_output_dir` | Needed if `output_dir` exists and is not empty. |
| `--per_device_train_batch_size` | Stored in `RerankerModel` and used for grouped-logit reshape during training. |
| `--per_device_eval_batch_size` | Controls rerank inference batch size and memory use. |
| `--fp16` / `--bf16` | Mixed precision; depends on model, device, and PyTorch support. |
| `--gradient_checkpointing` | Often needed for large LoRA rerankers. |
| `--gradient_accumulation_steps` | Increases effective batch size without changing grouped loss shape. |
| `--dataloader_num_workers` | Can speed data loading but complicates fixture debugging. |
| `--local_rank` / launcher args | Multi-GPU training may work through Trainer/DeepSpeed; multi-GPU rerank inference is explicitly unsupported. |
| `--deepspeed` | Optional DeepSpeed config path for large-model training. |

## Pair Formatting Details

The pair string is constructed as:

```text
query_prefix + " " + query + " " + passage_prefix + " " + normalized_title + " " + text
```

Then `.strip()` removes leading/trailing spaces. Hyphens in titles are replaced with spaces. Use prefixes such as `query: ` and `document: ` only when the model was trained with those instructions; leave prefixes empty for ordinary BERT-style rerankers unless the checkpoint documentation says otherwise.

## Output Score Format

`tevatron.reranker.driver.rerank` writes one line per scored candidate:

```text
query_id<TAB>docid<TAB>score
```

Rows are sorted by descending score within each query. Scores are raw sequence-classification logits. They can be negative, unbounded, and not comparable across unrelated queries.
