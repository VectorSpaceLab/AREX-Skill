# Data-prep CLI and API reference

Primary public entrypoint:

```bash
llmfoundry data_prep COMMAND [OPTIONS]
```

The package CLI is implemented with Typer. Command names are explicit snake_case; option names are normally kebab-case, e.g. Python argument `out_root` is `--out-root`.

Use `llmfoundry data_prep --help` and `llmfoundry data_prep COMMAND --help` in the active environment when exact formatting is needed.

## Public CLI commands

### `convert_dataset_hf`

Converts supported Hugging Face pretraining datasets to MDS.

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

Options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--dataset` | yes | Dataset constant. Built-in constants are `allenai/c4` and `the_pile`. |
| `--out-root` | yes | Root output directory; each requested split writes a subdirectory. |
| `--data-subset` | no | Dataset subset/name, such as `en` for C4. |
| `--splits` | no | Comma-separated split constants. Default includes `train`, `train_small`, `val`, `val_small`, `val_xsmall`. |
| `--compression` | no | MDS compression, e.g. `zstd`; `None` means no compression. |
| `--concat-tokens` | no | If set, tokenize and concatenate to this sequence length. |
| `--tokenizer` | required when `--concat-tokens` is set | Hugging Face tokenizer name/path. |
| `--tokenizer-kwargs` | no | JSON object string passed to tokenizer builder. |
| `--bos-text`, `--eos-text` | no | Boundary strings inserted before/after records during concatenation. |
| `--no-wrap` | no | Prevent document tokens from wrapping across output sequences. |
| `--num-workers` | no | DataLoader workers for conversion. |

Failure highlights:

- Unknown dataset constant raises a value error; use JSON workflows for arbitrary HF datasets.
- Requested output split must not already exist under `out_root`.
- `--concat-tokens` without `--tokenizer` is invalid.
- Tokenizer and HF dataset loading may require network/cache access.

### `convert_dataset_json`

Converts local JSON/JSONL with `text` records to MDS.

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

Options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--path` | yes | Input JSON/JSONL file or folder of JSON files. |
| `--out-root` | yes | Output MDS directory. |
| `--concat-tokens` | yes in the Typer CLI | Sequence length for tokenized concatenation. Source wrapper also supports `None` for no-concat programmatic use. |
| `--tokenizer` | yes in the Typer CLI | Tokenizer name/path for concatenation. |
| `--compression` | no | Defaults to `zstd`. |
| `--split` | no | Hugging Face split name, default `train`. |
| `--bos-text`, `--eos-text` | no | Boundary strings for concatenation. |
| `--no-wrap` | no | Prevent wrapping across max-length boundaries. |
| `--num-workers` | no | Conversion workers. |

Input schema:

```jsonl
{"text": "document text"}
```

Output columns:

- With concatenation: `tokens: ndarray:int32`.
- Without concatenation through programmatic API: `text: str`.

### `convert_finetuning_dataset`

Converts HF or local supervised fine-tuning data to MDS, with optional preprocessing and tokenization.

```bash
llmfoundry data_prep convert_finetuning_dataset \
  --dataset json \
  --data-files train.jsonl,validation.jsonl \
  --splits train,validation \
  --skip-preprocessing \
  --out-root mds/sft \
  --tokenizer EleutherAI/gpt-neox-20b \
  --max-seq-len 2048 \
  --target-prompts none \
  --target-responses last \
  --compression zstd
```

Options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--dataset` | yes | Dataset name/path for `datasets.load_dataset`; use `json` for local JSONL data files. |
| `--data-subset` | no | HF subset/name. |
| `--splits` | no | Comma-separated splits, default `train,validation`. |
| `--preprocessor` | no | Registered name or import path `module:function` that formats raw records. |
| `--data-files` | no | Comma-separated files, one per split. Length must equal splits length when set. |
| `--skip-preprocessing` | no | Treat records as already formatted prompt/response or chat/messages. |
| `--out-root` | yes | Root output directory or remote URI. |
| `--local` | no | Local copy/cache root when `--out-root` is remote. |
| `--compression` | no | MDS compression. |
| `--num-workers` | no | Conversion workers. |
| `--tokenizer` | no | If set, output tokenized `turns`; otherwise output formatted strings/JSON. |
| `--tokenizer-kwargs` | no | JSON object string passed to tokenizer builder. |
| `--max-seq-len` | no | Default `2048`; also injected into tokenizer kwargs as model max length. |
| `--target-prompts` | no | `none`, `all`, or `length>=N`; default `none`. |
| `--target-responses` | no | `last` or `all`; default `last`. |
| `--encoder-decoder` | no | Use encoder-decoder target policy; requires prompts `none`, responses `last`. |

Output columns:

- Untokenized prompt/response: `prompt: str`, `response: str`.
- Untokenized chat: `messages: json`.
- Tokenized current format: `turns: json`, each turn containing `input_ids` and `labels` lists.

Built-in preprocessor registry examples:

- `tatsu-lab/alpaca`
- `HuggingFaceH4/databricks_dolly_15k`
- `bigscience/P3`
- `Muennighoff/P3`, `Muennighoff/flan`
- `teknium/OpenHermes-2.5`
- `math-ai/StackMathQA`
- `AI-MO/NuminaMath-CoT`

### `convert_text_to_mds`

Converts local or remote folders of `.txt` files to tokenized MDS.

```bash
llmfoundry data_prep convert_text_to_mds \
  --input-folder raw_text \
  --output-folder mds/raw_text \
  --concat-tokens 2048 \
  --tokenizer EleutherAI/gpt-neox-20b \
  --eos-text '<|endoftext|>' \
  --compression zstd \
  --processes 4
```

Options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--output-folder` | yes | Folder or supported remote URI for MDS output. |
| `--input-folder` | yes | Folder or supported remote URI containing `.txt` files. |
| `--concat-tokens` | yes | Tokenized sequence length. |
| `--tokenizer` | yes | Hugging Face tokenizer name/path. |
| `--bos-text`, `--eos-text` | no | Boundary strings. |
| `--compression` | no | Default `zstd`. |
| `--use-tokenizer-eos` | no | Use tokenizer EOS text; do not also set `--eos-text`. |
| `--no-wrap` | no | Prevent text wrapping across output sequences. |
| `--processes` | no | Worker processes; default is CPU count minus a margin, capped. |
| `--reprocess` | no | Force reprocessing even if done marker matches. |
| `--trust-remote-code` | no | Allow tokenizer remote code execution. Use only for trusted tokenizers. |
| `--logging-level` | no | Logging level, default `INFO`. |

Important behavior:

- The command loads the tokenizer once in the main process and again in workers.
- It writes a `.text_to_mds_conversion_done` marker containing arguments and object names.
- It raises if no `.txt` files are found, output folder is non-empty, Unicode decode fails, or no shards are produced.

### `convert_delta_to_json`

Exports a Unity Catalog Delta table to local JSONL. It requires Databricks credentials and does not run safely without workspace/table access.

```bash
llmfoundry data_prep convert_delta_to_json \
  --delta-table-name catalog.schema.table \
  --json-output-folder delta_json \
  --cluster-id 1234-567890-clusterid \
  --batch-size 1000000 \
  --processes 4 \
  --json-output-filename train-00000-of-00001.jsonl
```

Options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--delta-table-name` | yes | Unity Catalog table as `catalog.schema.table`. |
| `--json-output-folder` | yes | Local output folder; remote URIs are rejected. |
| `--http-path` | no | Databricks SQL warehouse/http path; selects DBSQL method. |
| `--batch-size` | no | Row chunks for DBSQL fetches; default is very large. |
| `--processes` | no | Parallel download workers. |
| `--cluster-id` | no if serverless/http path path is used; otherwise often required | Cluster for Databricks Connect. |
| `--use-serverless` | no | Use serverless Databricks Connect path. |
| `--json-output-filename` | no | Combined JSONL filename; must end in `.jsonl`. |

Credential/dependency requirements:

- Databricks SDK config must provide host and token.
- `databricks-sdk`, `databricks-sql`, `databricks-connect`, `pyspark`, `pyarrow`, and `lz4` must be importable for full functionality.
- The user must have table read permissions and cluster/warehouse attach or query permissions.

## Source-derived API facts

The following signatures were verified from installed/source facts and should guide config construction and debugging.

### Runtime datasets and dataloaders

```python
StreamingTextDataset(
    tokenizer,
    max_seq_len: int,
    token_encoding_type: str = 'int64',
    streams=None,
    remote=None,
    local=None,
    split=None,
    download_retry: int = 2,
    download_timeout: float = 60,
    validate_hash=None,
    keep_zip: bool = False,
    epoch_size=None,
    predownload=None,
    cache_limit=None,
    partition_algo: str = 'relaxed',
    num_canonical_nodes=None,
    batch_size=None,
    shuffle: bool = False,
    shuffle_algo: str = 'py1e',
    shuffle_seed: int = 9176,
    shuffle_block_size=None,
    sampling_method: str = 'balanced',
    sampling_granularity: int = 1,
    batching_method: str = 'random',
    allow_unsafe_types: bool = False,
    replication=None,
    stream_name: str = 'stream',
    stream_config=None,
    **kwargs,
)
```

Key behavior:

- Requires a tokenizer and `max_seq_len`.
- Reads either `text` samples and tokenizes on the fly, or `tokens` samples as NumPy/bytes.
- `token_encoding_type` must be one of `int8`, `int16`, `int32`, `int64`, `uint8`, `uint16`, `uint32`, `uint64` for legacy byte tokens.
- Tokenizing `text` requires tokenizer `pad_token_id`.

```python
build_text_dataloader(
    tokenizer,
    device_batch_size,
    dataset: dict,
    drop_last: bool,
    num_workers: int,
    pin_memory: bool = True,
    prefetch_factor: int = 2,
    persistent_workers: bool = True,
    timeout: int = 0,
) -> DataSpec
```

Key behavior:

- Raises if tokenizer is `None`.
- Accepts `dataset.streams` or single `dataset.remote`/`dataset.local`/`dataset.split`.
- Filters dataset config to valid `StreamingTextDataset` and base `StreamingDataset` parameters.

```python
StreamingFinetuningDataset(
    tokenizer,
    token_encoding_type: str = 'int64',
    streams=None,
    local=None,
    remote=None,
    split=None,
    download_retry: int = 2,
    download_timeout: float = 60,
    validate_hash=None,
    keep_zip: bool = False,
    epoch_size=None,
    predownload=None,
    cache_limit=None,
    partition_algo: str = 'relaxed',
    num_canonical_nodes=None,
    batch_size=None,
    shuffle: bool = False,
    shuffle_algo: str = 'py1e',
    shuffle_seed: int = 9176,
    shuffle_block_size=None,
    sampling_method: str = 'balanced',
    sampling_granularity: int = 1,
    batching_method: str = 'random',
    max_seq_len: int = 2048,
    allow_unsafe_types: bool = False,
    replication=None,
    packing_ratio=None,
    stream_name: str = 'stream',
    stream_config=None,
    **kwargs,
)
```

Key behavior:

- Reads current tokenized `turns`, old tokenized `input_ids`/`labels`, or untokenized prompt/chat records.
- `packing_ratio` affects `state_dict` sample accounting and collator behavior.
- Too few samples for physical/canonical nodes raises a dataset-too-small error.

```python
build_finetuning_dataloader(
    tokenizer,
    device_batch_size,
    dataset: dict,
    num_workers: int,
    drop_last: bool = False,
    pin_memory: bool = True,
    prefetch_factor: int = 2,
    persistent_workers: bool = True,
    timeout: int = 0,
) -> DataSpec
```

Key behavior:

- Raises if tokenizer is `None`.
- Uses HF path if `dataset.hf_name` is set.
- Uses streaming path if `dataset.remote` or `dataset.streams` is set.
- For streaming path, `remote` requires `local` unless using `streams` with local fields inside each stream.
- Validates target policy and rejects mixing HF-only fields with streaming fields.

### Converter wrapper signatures

```python
convert_dataset_hf_from_args(
    dataset: str,
    data_subset: str | None,
    splits: list[str],
    out_root: str,
    compression: str | None,
    concat_tokens: int | None,
    tokenizer: str | None,
    tokenizer_kwargs: str | None,
    bos_text: str | None,
    eos_text: str | None,
    no_wrap: bool,
    num_workers: int | None,
) -> None
```

```python
convert_dataset_json_from_args(
    path: str,
    out_root: str,
    compression: str | None,
    concat_tokens: int | None,
    split: str,
    tokenizer: str | None = None,
    bos_text: str | None = None,
    eos_text: str | None = None,
    no_wrap: bool = False,
    num_workers: int | None = None,
) -> None
```

```python
convert_finetuning_dataset_from_args(
    dataset: str,
    data_subset: str | None,
    splits: list[str],
    preprocessor: str | None,
    data_files: list[str],
    skip_preprocessing: bool,
    out_root: str,
    local: str | None,
    compression: str | None,
    num_workers: int | None,
    tokenizer: str | None,
    tokenizer_kwargs: str | None,
    max_seq_len: int,
    target_prompts: str,
    target_responses: str,
    encoder_decoder: bool,
)
```

```python
convert_text_to_mds_from_args(
    output_folder: str,
    input_folder: str,
    compression: str,
    concat_tokens: int,
    tokenizer_name: str,
    bos_text: str | None,
    eos_text: str | None,
    use_tokenizer_eos: bool,
    no_wrap: bool,
    processes: int,
    reprocess: bool,
    trust_remote_code: bool,
    logging_level: str,
) -> None
```

```python
convert_delta_to_json_from_args(
    delta_table_name: str,
    json_output_folder: str,
    http_path: str | None,
    cluster_id: str | None,
    use_serverless: bool,
    batch_size: int,
    processes: int,
    json_output_filename: str,
) -> None
```

## Programmatic contrastive data facts

The public data registry includes the dataloader name `contrastive_pairs`.

Supported raw sample shapes:

```json
{"text_a": "query", "text_b": "positive"}
```

or

```json
{"query_text": "query", "positive_passage": "positive", "negative_passages": "[\"negative\"]"}
```

Important API behavior:

- `build_pairs_dataloader(dataset, tokenizer, device_batch_size, drop_last, num_workers, ..., max_hard_negatives=None)` raises if tokenizer is missing.
- The dataset tokenizes query, positive passage, and selected negatives to `max_seq_len`.
- `max_hard_negatives` truncates the negative list.
- `prepend_query`, `prepend_passage`, `append_eos_token`, `append_token`, and `shuffle_hard_negatives` are passed to the streaming pairs dataset through `dataset` fields.

## Safe import/signature probe

Use the bundled script to inspect what is actually importable in the current environment:

```bash
python scripts/llmfoundry_data_prep_smoke.py --dump-json
```

It reports missing dependencies rather than installing anything, downloading tokenizers, querying Hugging Face, querying Databricks, or writing data.
