# Training Data Formats

This reference covers the data shapes consumed by the bundled training scripts and the safe validation helper. Validate small samples before allocating GPUs or writing large caches.

## SFT Instruction JSON

Use SFT mode for Chinese Alpaca-style instruction/chat-oriented fine-tuning with [`scripts/run_clm_sft_with_peft.py`](../scripts/run_clm_sft_with_peft.py). The script scans `--dataset_dir` for `*.json` files and builds a tokenized instruction dataset with [`scripts/build_dataset.py`](../scripts/build_dataset.py).

Each JSON file should be a UTF-8 top-level list. Every record must contain string fields:

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `instruction` | yes | string | The user task or question. Must not be empty. |
| `input` | yes | string | Optional context. Use an empty string when there is no extra context. |
| `output` | yes | string | The desired response. Must not be empty. |

The bundled tiny sample is [`templates/instruction_sample.json`](../templates/instruction_sample.json). It demonstrates schema only; do not treat it as a useful training corpus.

### Alpaca Prompt Template

The SFT data builder uses this prompt prefix for every record:

```text
Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response: 
```

If `input` is not an empty string, the builder appends a newline plus `input` to the instruction before formatting the prompt. The target text is `output` followed by the tokenizer EOS token. Labels are `-100` across the prompt/source tokens and ordinary target token ids across the answer tokens, so loss is computed only on the response.

### SFT Validation

Run the bundled validator before SFT:

```bash
python scripts/validate_training_data.py --mode sft --input templates/instruction_sample.json
python scripts/validate_training_data.py --mode sft --input /path/to/user_sft_dir --max-records 100
```

The helper reports invalid JSON, a non-list top level, missing `instruction`/`input`/`output`, non-string values, and empty `instruction` or `output`. It accepts either one JSON file or a directory containing `*.json` files.

## PT Plain Text Data

Use PT mode for Chinese LLaMA-style continued CLM pretraining or base-model vocabulary adaptation with [`scripts/run_clm_pt_with_peft.py`](../scripts/run_clm_pt_with_peft.py). The script scans `--dataset_dir` for `*.txt` files and loads them through the datasets text loader.

Expected shape:

- UTF-8 plain text.
- One or more non-empty lines of raw training text.
- No JSON envelope and no `instruction`/`output` keys.
- Place one or more `.txt` files directly under `--dataset_dir`.

The bundled tiny sample is [`templates/pretrain_sample.txt`](../templates/pretrain_sample.txt). It demonstrates text shape only.

Validate PT data with:

```bash
python scripts/validate_training_data.py --mode pt --input templates/pretrain_sample.txt
python scripts/validate_training_data.py --mode pt --input /path/to/user_pt_dir --max-records 1000
```

The helper reports missing files, invalid UTF-8, empty files, all-whitespace checked text, and extremely short checked text.

## Sequence Length and Blocking

- PT uses `--block_size`. If omitted, the script starts from the tokenizer `model_max_length`; if that exceeds 1024, it warns and caps the default to 1024. The bundled PT template defaults to `BLOCK_SIZE=512`.
- SFT uses `--max_seq_length` and truncates prompt+answer token sequences to that length. The bundled SFT template defaults to `MAX_SEQ_LENGTH=512`.
- Increasing either length raises memory use. Confirm GPU memory before increasing it.

## Dataset Cache Behavior

PT and SFT both use persistent datasets caches. Stale or corrupted caches can silently reuse older tokenization unless they are cleared or redirected.

### PT Cache

For every `*.txt` filename under `--dataset_dir`, the PT script creates cache subdirectories under `--data_cache_dir`:

- `<filename>_text` for raw text/tokenized arrow intermediates.
- `<filename>` for the saved grouped dataset loaded by `datasets.load_from_disk`.

To refresh PT preprocessing after changing tokenizer, `--block_size`, data contents, or worker count, use a new `--data_cache_dir` or remove the affected filename-specific cache directories.

### SFT Cache

The SFT builder uses a cache path based on each JSON filename without its extension. In the bundled SFT script it is called with `data_cache_dir=None`, so the cache is created next to each JSON data file. To refresh SFT preprocessing after changing tokenizer, `--max_seq_length`, or data contents, remove the corresponding filename-derived cache directory before rerunning.

## Tokenizer and Vocabulary Considerations

- Chinese LLaMA is base/continuation-oriented and can use LLaMA or Chinese LLaMA vocabulary configurations depending on the pretraining goal.
- Chinese Alpaca is instruction/chat-oriented. The SFT script requires a Chinese Alpaca tokenizer with vocabulary size `49954` and raises an error if the tokenizer length differs.
- The PT script allows only these model-vocab/tokenizer-length combinations: `32000/32000`, `32000/49953`, `49953/49953`, and `49954/49954`.
- Keep `modules_to_save=embed_tokens,lm_head` when training with expanded vocabulary so adapter checkpoints preserve embedding and output-head changes.

## Credential-Bound Prompt Crawling Is Excluded

The source release included a prompt crawler for generating instruction data with an OpenAI API key. This skill does not bundle it as a runnable helper because it requires credentials, network access, and paid/credentialed API calls. If a user wants generated instruction data, first establish their credential, cost, safety, and data-governance policy outside this runtime skill, then validate the resulting JSON with the SFT schema above.
