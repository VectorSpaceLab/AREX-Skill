# Data preparation workflows

These workflows are safe templates for preparing LLM Foundry data. They assume the `llmfoundry` package and data-prep dependencies are installed. Commands can run on CPU; GPUs are not required for conversion.

Before any expensive or credentialed operation:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture sample.jsonl --schema auto
python scripts/llmfoundry_data_prep_smoke.py --check-cli
```

The smoke script is read-only unless you point it at a fixture to validate.

## Workflow 1: Convert local pretraining JSONL to MDS

Use this for a local file or folder of JSON/JSONL records with a `text` field.

1. Validate the fixture:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture train.jsonl --schema pretraining
```

2. Convert to tokenized, fixed-length MDS:

```bash
llmfoundry data_prep convert_dataset_json \
  --path train.jsonl \
  --out-root mds/pretrain_json \
  --split train \
  --concat-tokens 2048 \
  --tokenizer EleutherAI/gpt-neox-20b \
  --eos-text '<|endoftext|>' \
  --compression zstd
```

Notes:

- `--concat-tokens` chooses `tokens: ndarray:int32` output. Without concatenation the converter writes `text` samples.
- If the tokenizer does not add BOS/EOS separators, provide `--bos-text` or `--eos-text`; otherwise examples can be glued together without a boundary.
- `--no-wrap` prevents tokens from one document wrapping into the next output sequence after a max-length boundary. It can reduce sample count.
- Use a fresh `--out-root`. If a split/output already exists, choose another folder or intentionally clean it first.

Minimal local loader config after conversion:

```yaml
train_loader:
  name: text
  dataset:
    local: mds/pretrain_json
    split: null
    max_seq_len: 2048
    shuffle: true
    allow_unsafe_types: false
  drop_last: true
  num_workers: 8
```

If your output root contains split subdirectories, set `local: mds/pretrain_json` and `split: train`.

## Workflow 2: Convert Hugging Face C4 or The Pile to MDS

Use the package CLI for the built-in C4/Pile constants.

```bash
llmfoundry data_prep convert_dataset_hf \
  --dataset allenai/c4 \
  --data-subset en \
  --out-root mds/c4 \
  --splits train_small,val_xsmall \
  --concat-tokens 2048 \
  --tokenizer EleutherAI/gpt-neox-20b \
  --eos-text '<|endoftext|>' \
  --compression zstd \
  --num-workers 8
```

Supported built-in dataset constants:

- `allenai/c4`, commonly with `--data-subset en`.
- `the_pile`, commonly with `--data-subset all` if the dataset variant expects a subset/name.

Split names are package-level split constants, not arbitrary HF split expressions:

- C4: `train`, `train_small`, `val`, `val_small`, `val_xsmall`, `val_xxsmall`.
- The Pile: `train`, `train_small`, `val`, `val_small`, `val_xsmall`.

Safety:

- This command streams from Hugging Face and can download tokenizer files; confirm network/cache permissions.
- `train` and `val` are very large. For smoke tests, use `train_small` or `val_xsmall`.
- If the dataset name is not one of the built-in constants, use `convert_dataset_json` or `convert_finetuning_dataset` with `dataset=json` and `data_files`.

## Workflow 3: Convert raw text files to tokenized MDS

Use this for a directory of `.txt` files.

```bash
llmfoundry data_prep convert_text_to_mds \
  --input-folder raw_text \
  --output-folder mds/raw_text \
  --concat-tokens 2048 \
  --tokenizer EleutherAI/gpt-neox-20b \
  --eos-text '<|endoftext|>' \
  --compression zstd \
  --processes 4 \
  --logging-level INFO
```

Options to choose deliberately:

- `--use-tokenizer-eos`: use the tokenizer's EOS string instead of passing `--eos-text`. Do not set both.
- `--trust-remote-code`: only set for tokenizers whose remote code you trust.
- `--reprocess`: force conversion even if the done marker suggests the same inputs/arguments were already processed.
- `--processes`: number of worker processes. Start small on shared filesystems or remote object stores.

Validation after conversion:

```bash
python - <<'PY'
import json
from pathlib import Path
index = Path('mds/raw_text/index.json')
print('exists:', index.exists())
if index.exists():
    data = json.loads(index.read_text())
    print('num_shards:', len(data.get('shards', [])))
PY
```

If `num_shards` is zero, the dataset was too small for the chosen `--concat-tokens` length or no text was read.

## Workflow 4: Convert local supervised fine-tuning JSONL to MDS

Use prompt/response or chat JSONL. If the local records are already formatted, use `--skip-preprocessing`.

1. Validate schema:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture sft_train.jsonl --schema sft
```

2. Convert untokenized SFT MDS:

```bash
llmfoundry data_prep convert_finetuning_dataset \
  --dataset json \
  --data-files sft_train.jsonl,sft_validation.jsonl \
  --splits train,validation \
  --skip-preprocessing \
  --out-root mds/sft \
  --compression zstd
```

3. Convert tokenized SFT MDS for decoder-only training:

```bash
llmfoundry data_prep convert_finetuning_dataset \
  --dataset json \
  --data-files sft_train.jsonl,sft_validation.jsonl \
  --splits train,validation \
  --skip-preprocessing \
  --out-root mds/sft_tokenized \
  --compression zstd \
  --tokenizer EleutherAI/gpt-neox-20b \
  --max-seq-len 2048 \
  --target-prompts none \
  --target-responses last
```

Notes:

- `--data-files` is comma-separated and must have the same number of entries as `--splits`.
- `--dataset json` delegates to the Hugging Face `json` loader for local files.
- `--skip-preprocessing` means records are already in prompt/response or chat/messages format.
- Without `--tokenizer`, the converter writes formatted strings (`prompt`/`response` or `messages`) and tokenization happens during dataloader construction.
- With `--tokenizer`, the converter writes tokenized `turns` and filters examples with empty prompt/response, all-padding response targets, or prompts too long for the selected `--max-seq-len`/target policy.

Training-side dataset snippet for the resulting SFT MDS:

```yaml
train_loader:
  name: finetuning
  dataset:
    remote: null
    local: mds/sft_tokenized
    split: train
    max_seq_len: 2048
    decoder_only_format: true
    target_prompts: none
    target_responses: last
    shuffle: true
    allow_unsafe_types: false
  drop_last: false
  num_workers: 8
```

Only configure training launch, optimizer, callbacks, or checkpoint details in the training sub-skill.

## Workflow 5: Use a custom SFT preprocessor

If raw source records have custom columns, create an importable Python function that returns either `{'prompt': str, 'response': str}` or `{'messages': [...]}`.

Example raw record:

```json
{"question": "What is MDS?", "answer": "A streaming shard format.", "source": "faq"}
```

Preprocessor:

```python
# my_project/preprocess.py
def qa_to_prompt_response(example):
    return {
        'prompt': f"Question: {example['question']}\nAnswer:",
        'response': example['answer'],
    }
```

Command:

```bash
PYTHONPATH=. llmfoundry data_prep convert_finetuning_dataset \
  --dataset json \
  --data-files qa_train.jsonl \
  --splits train \
  --preprocessor my_project.preprocess:qa_to_prompt_response \
  --out-root mds/qa_sft \
  --tokenizer EleutherAI/gpt-neox-20b \
  --max-seq-len 2048 \
  --target-prompts none \
  --target-responses last
```

Registered built-in preprocessors include examples for Alpaca, Dolly, P3, Muennighoff P3/FLAN, OpenHermes/ShareGPT, StackMathQA, and NuminaMath-CoT. If the dataset name has a registered preprocessor and `--preprocessor` is omitted, LLM Foundry can use the registered one; otherwise it raises an error unless `--skip-preprocessing` is supplied.

## Workflow 6: Load existing MDS from object storage with a local cache

Use this when the data is already MDS and stored remotely.

```yaml
train_loader:
  name: text
  dataset:
    remote: s3://bucket/path/pretrain_mds
    local: cache/pretrain_mds
    split: train
    max_seq_len: 2048
    shuffle: true
    cache_limit: 500gb
    predownload: 100000
    download_retry: 4
    download_timeout: 120
    validate_hash: sha1
    allow_unsafe_types: false
  drop_last: true
  num_workers: 8
```

Checklist:

- Confirm the remote prefix contains `split/index.json`, e.g. `train/index.json`.
- Confirm the runtime has object-store credentials and permissions for list/read/download.
- Use a persistent local cache if restarts are common; use a job-local scratch cache if disk is limited.
- Keep `cache_limit` below available disk and account for compressed plus decompressed shard files when `keep_zip: true`.

## Workflow 7: Multiple MDS streams for pretraining

Use `streams` to mix datasets.

```yaml
train_loader:
  name: text
  dataset:
    streams:
      code:
        remote: s3://bucket/mds/code
        local: cache/code
        split: train
        proportion: 0.4
      web:
        remote: s3://bucket/mds/web
        local: cache/web
        split: train
        proportion: 0.6
    max_seq_len: 2048
    shuffle: true
    sampling_method: balanced
    batching_method: random
  drop_last: true
  num_workers: 8
```

Do not mix top-level `remote`/`local` with `streams`. For single-stream local data, use top-level `local` and `split` instead.

## Workflow 8: Fine-tuning with packing

Packing is configured on the fine-tuning dataloader, not the converter.

```yaml
train_loader:
  name: finetuning
  dataset:
    local: mds/sft_tokenized
    split: train
    max_seq_len: 2048
    decoder_only_format: true
    target_prompts: none
    target_responses: last
    packing_ratio: 5.0
    max_leftover_bins_to_keep: 200
    shuffle: true
  drop_last: false
  num_workers: 8
```

Rules:

- Packing is only supported for decoder-only format.
- `packing_ratio` must be a float `>= 1` or the string `auto`.
- `max_leftover_bins_to_keep` requires `packing_ratio`.
- `auto` profiles the dataloader and chooses a ratio; it can still waste/discard some examples because profiling sees only a sample of the dataset.
- Packing does not change device batch size; it changes the number of raw examples consumed per packed batch.

## Workflow 9: Delta/Databricks to local JSONL

Use this only when Databricks credentials and table permissions are available. The CLI exports a Unity Catalog Delta table to local JSONL. It does not write MDS directly.

```bash
llmfoundry data_prep convert_delta_to_json \
  --delta-table-name catalog.schema.table \
  --json-output-folder delta_json \
  --cluster-id 1234-567890-clusterid \
  --batch-size 1000000 \
  --processes 4 \
  --json-output-filename train-00000-of-00001.jsonl
```

Alternative SQL path:

```bash
llmfoundry data_prep convert_delta_to_json \
  --delta-table-name catalog.schema.table \
  --json-output-folder delta_json \
  --http-path /sql/1.0/warehouses/example \
  --batch-size 1000000
```

After export, validate and convert the JSONL with the appropriate local workflow:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture delta_json/train-00000-of-00001.jsonl --schema sft
llmfoundry data_prep convert_finetuning_dataset \
  --dataset json \
  --data-files delta_json/train-00000-of-00001.jsonl \
  --splits train \
  --skip-preprocessing \
  --out-root mds/delta_sft
```

Prerequisites:

- Databricks SDK, SQL connector, Databricks Connect/PySpark, `lz4`, `pyarrow`, and network access.
- Workspace config with host/token available to the Databricks SDK.
- Unity Catalog table name in `catalog.schema.table` form.
- Cluster/warehouse access with supported runtime and governance mode.
- A local, empty `--json-output-folder`; remote output folders are rejected.

## Workflow 10: Contrastive-pair MDS

For local contrastive JSONL, use an MDS writer or an upstream converter that writes one of the supported contrastive schemas. For Delta tables, the package contains a programmatic utility that validates columns and writes contrastive MDS, but the public `llmfoundry data_prep` CLI exposes only `convert_delta_to_json`, not a contrastive-MDS command.

Local schema examples:

```jsonl
{"text_a": "query 1", "text_b": "positive passage 1"}
{"query_text": "query 2", "positive_passage": "positive passage 2", "negative_passages": "[\"hard negative 1\", \"hard negative 2\"]"}
```

Dataloader snippet:

```yaml
train_loader:
  name: contrastive_pairs
  dataset:
    local: mds/contrastive
    split: train
    max_seq_len: 1024
    shuffle_hard_negatives: false
    prepend_query: "query: "
    prepend_passage: "passage: "
  max_hard_negatives: 2
  drop_last: false
  num_workers: 4
```

Validation:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture pairs.jsonl --schema contrastive
```

## General validation checklist

- Fixture is valid JSONL and each line is an object.
- Required keys are present and values have safe types.
- Dataset has enough samples for world size, dataloader batch size, and `drop_last` settings.
- Tokenizer is available locally or the user authorized downloads.
- Output root is fresh or intentionally cleaned.
- MDS output contains `index.json` and at least one shard.
- Remote object-store paths are readable/writable as required.
- Databricks commands are never run without credentials, table access, and explicit user approval.
