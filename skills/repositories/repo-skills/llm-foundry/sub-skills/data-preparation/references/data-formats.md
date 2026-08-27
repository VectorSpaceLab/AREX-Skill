# LLM Foundry data formats

LLM Foundry data preparation has two broad stages:

1. **Source data**: JSON/JSONL, text files, Hugging Face datasets, Delta tables, or existing object-store data.
2. **Runtime data**: Mosaic Streaming/MDS directories consumed by dataloaders through `local`, `remote`, `split`, or `streams` fields.

Use this reference to decide whether the source is shaped correctly before running a conversion command or wiring it into a training/evaluation config.

## Pretraining text records

### JSON/JSONL schema

For pretraining text conversion, each record must expose a text field named exactly `text`.

```jsonl
{"text": "First document or chunk of text."}
{"text": "Second document or chunk of text."}
```

Rules:

- `convert_dataset_json` loads either a single JSON/JSONL file or a directory of JSON files via the Hugging Face `json` loader.
- Un-tokenized output writes MDS samples with column `text: str`/bytes.
- Tokenized/concatenated output writes MDS samples with column `tokens: ndarray:int32`.
- If `--concat_tokens` is used, `--tokenizer` is required. Choose `--bos_text` or `--eos_text` when the tokenizer does not insert a separator itself.
- Invalid or missing `text` keys fail during loading or iteration, not always at CLI argument parsing time. Validate locally first.

### Raw text folder schema

`convert_text_to_mds` scans an input folder recursively for `*.txt` files. Each file is treated as a text sequence. It can read local folders and supported remote object-store folders, but remote reads require object-store credentials.

```text
raw_text/
  book_a.txt
  book_b.txt
  nested/
    chapter_1.txt
```

Rules:

- Only `.txt` files are included.
- The converter tokenizes and concatenates text; there is no no-tokenizer raw-text mode for this command.
- It writes `tokens: ndarray:int32` MDS shards.
- An empty folder raises an input-missing-data error.
- A non-empty output folder raises an output-folder-not-empty error unless the converter detects a previous completed run with identical input/arguments and `--reprocess` is false.

## Supervised fine-tuning records

LLM Foundry supports two formatted fine-tuning shapes: prompt/response and chat/messages. A preprocessing function may convert arbitrary source columns into one of these shapes.

### Prompt/response format

Canonical local JSONL:

```jsonl
{"prompt": "Explain gradient checkpointing in one sentence.", "response": "It trades extra computation for lower activation memory by recomputing intermediates during backpropagation."}
{"prompt": "Translate to French: good morning", "response": "Bonjour"}
```

Accepted prompt key family and response key family are intentionally limited by the package. The safest keys are exactly `prompt` and `response`.

Rules:

- The formatted sample must be a mapping with exactly one allowed prompt key and one allowed response key.
- Prompt and response values must be strings.
- Empty prompt, empty response, or a response that becomes all padding/loss-ignored tokens can be filtered or rejected.
- Extra keys such as `id`, `metadata`, or `source` can make the formatted example unrecognized unless a preprocessing function removes them.

### Chat/messages format

Canonical local JSONL:

```jsonl
{"messages": [{"role": "user", "content": "Name a safe data-prep check."}, {"role": "assistant", "content": "Validate JSONL keys before conversion."}]}
{"messages": [{"role": "system", "content": "Be concise."}, {"role": "user", "content": "What is MDS?"}, {"role": "assistant", "content": "A sharded streaming dataset format."}]}
```

Rules:

- The formatted sample must contain one messages key, usually `messages`.
- `messages` must be a list with at least two messages.
- Every message must contain exactly `role` and `content`.
- Roles must be among `user`, `assistant`, `system`, and `tool`.
- The final message must be from `assistant`.
- Consecutive messages cannot repeat the same role in the validated chat path.
- `content` may be a string or list for chat-capable multimodal tokenizers; for ordinary text SFT, prefer strings.
- Tokenized chat examples rely on the tokenizer chat template when available; otherwise LLM Foundry uses an internal default chat template.

### Fine-tuning target policies

The fine-tuning collator controls which tokens contribute loss.

| Field | Valid values | Meaning |
| --- | --- | --- |
| `target_prompts` | `none`, `all`, `length>=N` | Whether prompt/context tokens generate loss. Default `none`. `length>=N` targets only prompts with at least `N` tokens. |
| `target_responses` | `last`, `all` | Whether only the final assistant response or all assistant responses generate loss. Default `last`. |
| `decoder_only_format` | `true`, `false` | Decoder-only combines prompt and response into one sequence; encoder-decoder separates context and target. |

Important constraints:

- For encoder-decoder data (`encoder_decoder` CLI flag or `decoder_only_format: false`), use `target_prompts: none` and `target_responses: last`.
- Decoder-only SFT normally uses `target_prompts: none`, `target_responses: last` so the model learns to answer rather than imitate the user prompt.
- If prepared/tokenized MDS was created with one target policy but a training config uses another, examples may truncate away all loss-generating tokens and fail later.

## Tokenized fine-tuning MDS columns

When `convert_finetuning_dataset` is run with a tokenizer, it writes the current tokenized fine-tuning format:

```json
{
  "turns": [
    {"input_ids": [101, 102], "labels": [201, 202]}
  ]
}
```

The streaming fine-tuning reader also supports older MDS layouts:

- `input_ids` + `labels` as bytes or NumPy arrays.
- `prompt` + `response` as untokenized strings.
- `messages` as chat JSON.

Prefer the current `turns` format for newly prepared tokenized SFT datasets.

## MDS/StreamingDataset layout

MDS output is a directory containing an `index.json` plus shard files. Split-aware outputs put one MDS directory per split.

```text
my_mds_dataset/
  train/
    index.json
    shard.00000.mds.zstd
  validation/
    index.json
    shard.00000.mds.zstd
```

or for a single-split converter:

```text
my_json_mds/
  index.json
  shard.00000.mds.zstd
```

Dataloader config chooses where the shards are read from and cached:

```yaml
train_loader:
  name: text
  dataset:
    remote: s3://bucket/path/to/my_mds_dataset
    local: cache/my_mds_dataset
    split: train
    max_seq_len: 2048
    shuffle: true
    cache_limit: 200gb
    predownload: 100000
    keep_zip: false
```

Field meanings:

- `remote`: remote object-store directory for the MDS dataset. May be omitted for local-only data.
- `local`: local directory used for an existing local dataset or as the download/cache destination for remote shards.
- `split`: subdirectory under `remote` and `local` to read, such as `train`, `val`, or `validation`.
- `streams`: multiple weighted stream dictionaries; use this instead of top-level `remote`/`local` when mixing datasets.
- `cache_limit`: maximum local cache size, as bytes or strings like `500gb`.
- `predownload`: target number of samples to download ahead while iterating.
- `allow_unsafe_types`: whether to deserialize unsafe shard types such as Pickle. Keep `false` unless the dataset is trusted.

Local split validation behavior:

- If `remote` is absent or equals `local`, and `local` exists, LLM Foundry checks that `local` contains the requested `split` subdirectory.
- For `streams`, the same split check applies to each stream's local/remote pair.

## Multiple streams

Use `streams` for mixing or sampling from multiple MDS roots.

```yaml
train_loader:
  name: text
  dataset:
    streams:
      web:
        remote: s3://bucket/pretrain/web
        local: cache/web
        split: train
        proportion: 0.8
      books:
        remote: s3://bucket/pretrain/books
        local: cache/books
        split: train
        proportion: 0.2
    max_seq_len: 2048
    shuffle: true
```

Do not set top-level `remote`/`local` at the same time as `streams`; put stream-specific locations inside each stream.

## Contrastive-pair records

The contrastive dataloader supports two sample shapes.

### One query, one response

```jsonl
{"text_a": "what is streaming data", "text_b": "a dataset served from shards"}
```

Any key starting with `text_a` and any key starting with `text_b` is recognized for this shape.

### One query, positive, and hard negatives

```jsonl
{"query_text": "what is streaming data", "positive_passage": "data served from MDS shards", "negative_passages": "[\"a model architecture\", \"an optimizer\"]"}
```

Rules:

- Required keys are `query_text` and `positive_passage`.
- `negative_passages` is optional for Delta-to-contrastive conversion and should be a JSON-encoded list string in MDS for the streaming reader.
- Dataloader options include `max_hard_negatives`, `prepend_query`, `prepend_passage`, `append_eos_token`, `append_token`, and `shuffle_hard_negatives`.
- `append_eos_token` and `append_token` are mutually exclusive.

## Safe schema preflight

Before conversion, run the bundled validator on a small local fixture:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture train.jsonl --schema pretraining
python scripts/llmfoundry_data_prep_smoke.py --fixture sft.jsonl --schema sft
python scripts/llmfoundry_data_prep_smoke.py --fixture chat.jsonl --schema chat
python scripts/llmfoundry_data_prep_smoke.py --fixture pairs.jsonl --schema contrastive
```

This validates local JSONL shape only. It does not download tokenizers, query Hugging Face, query Databricks, or write MDS shards.
