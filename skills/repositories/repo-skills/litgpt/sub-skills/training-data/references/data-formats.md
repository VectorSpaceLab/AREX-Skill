# Data Formats And Data Modules

LitGPT separates supervised finetuning data modules from pretraining data modules. Validate paths and schemas before launching training; data errors otherwise appear after checkpoint setup or tokenizer work has already begun.

## JSON/JSONL SFT Contract

Use the `JSON` data module for local supervised finetuning files:

```bash
litgpt finetune_lora checkpoints/org/model \
  --data JSON \
  --data.json_path data/sft.jsonl \
  --data.val_split_fraction 0.1
```

Each sample must be a JSON object with:

- `instruction`: required string; task prompt/instruction.
- `output`: required string; desired response.
- `input`: optional string; extra input context for prompt styles such as Alpaca. Use `""` when no input is needed.

Accepted path shapes:

- Single `.json` file containing a list of sample objects.
- Single `.jsonl` file containing one sample object per non-empty line.
- Directory with `train.json`/`val.json`, `train.jsonl`/`val.jsonl`, or mixed supported suffixes for explicit split files.

Unsupported:

- File suffixes other than `.json` or `.jsonl`.
- Directory splits without both train and val files.
- Directory splits with `--data.val_split_fraction` set.
- Non-object records, top-level JSON objects for a single-file dataset, missing `instruction`, or missing `output`.

## Split Behavior

- A single file is split with `val_split_fraction`.
- Source validation defaults a single file with no explicit `val_split_fraction` to `0.05` and emits a warning.
- A split directory must not set `val_split_fraction`; train/val membership is already fixed by file names.
- `seed` controls deterministic random splitting and train-data shuffle order.

The user docs have historically shown `0.1` as an example/default for custom JSON, while installed source validation defaults to `0.05` for an unspecified single file. Prefer setting the fraction explicitly.

## Validate JSON SFT Data

Use the bundled validator before training:

```bash
python scripts/validate_json_sft_data.py data/sft.jsonl --val-split-fraction 0.1
python scripts/validate_json_sft_data.py data/sft_split_dir
python scripts/validate_json_sft_data.py data/sft.jsonl --json-report
```

The validator performs local file/schema checks only. It does not tokenize, download, instantiate LitGPT, or train.

Expected successes include:

- Summary of discovered split(s), sample counts, and optional-key counts.
- Warning when a single file omits `--val-split-fraction` and would default to `0.05`.
- Non-zero exit with row-level diagnostics for invalid JSONL, missing keys, invalid suffixes, or bad split directories.

## Built-In SFT Modules

Use built-in modules when they match the dataset and license/runtime requirements:

- `Alpaca`, `Alpaca2k`, `AlpacaGPT4`: Alpaca-style instruction-response data.
- `Deita`, `FLAN`, `LIMA`, `LongForm`: larger or specialized SFT datasets; some need optional packages, access tokens, or network/data downloads.
- `JSON`: local custom SFT file/directory with the schema above.

Inspect module-specific flags with:

```bash
litgpt finetune_lora --data.help JSON
litgpt finetune_lora --data.help Alpaca2k
```

Common SFT module fields include `mask_prompt`, `prompt_style`, `ignore_index`, `seed`, `num_workers`, file/download paths, and dataset-specific filtering/subset options.

## Prompt Style And Masking

- `prompt_style` controls how `instruction` plus optional `input` are wrapped before tokenization. The default JSON style is `alpaca`.
- `mask_prompt=false` trains on both prompt and response tokens.
- `mask_prompt=true` masks prompt labels with `ignore_index` so loss focuses on the response. Verify the exact field name in CLI help for the installed build; the source dataclass uses `mask_prompt`.
- If a custom prompt style expects extra keys, every sample must include those keys or tokenization fails.

## SFT Sequence Length

Finetuning loaders find the longest tokenized training sample and cap model training length at `min(longest_sample, train.max_seq_length or infinity)`. This is memory efficient but means one very long sample can increase memory for the run.

OOM-safe data choices:

- Set `--train.max_seq_length 256` or `512` for early smoke runs.
- Remove or split pathological long examples.
- Keep `--train.micro_batch_size 1` until the command is proven.
- Validate small datasets and exact splits before scaling.

## Pretraining Data Modules

Pretraining consumes next-token text/token streams rather than SFT instruction/output pairs.

Common options:

- `TextFiles`: local folder of plain text files; recommended only for small/custom datasets. Avoid many tiny files; concatenate into larger files when possible.
- `LitData`: preprocessed LitData directory or remote path for larger datasets; requires optional `litdata` support and preprocessing outside this helper.
- `TinyStories`, `OpenWebText`, `TinyLlama`, `MicroLlama`: built-in/prepared pretraining datasets; many require downloads, optional packages, or preprocessing.

Inspect module options with:

```bash
litgpt pretrain --data.help TextFiles
litgpt pretrain --data.help LitData
```

Pretraining commonly needs a tokenizer:

```bash
litgpt pretrain pythia-14m \
  --tokenizer_dir checkpoints/EleutherAI/pythia-14m \
  --data TextFiles \
  --data.train_data_path data/pretrain_text \
  --train.max_tokens 1000000 \
  --train.max_norm 1.0
```

## Data-Readiness Checklist

Before training:

- Confirm local paths exist and use supported suffixes or split names.
- Confirm SFT records have `instruction` and `output`; add `input` as `""` if the prompt style expects it.
- Set `val_split_fraction` explicitly for single JSON/JSONL files.
- Do not set `val_split_fraction` for split directories.
- Run a small `--train.max_steps` smoke only after schema/path validation; do not treat `max_steps` as the final pretraining budget.
- Check whether the selected built-in module downloads data or requires optional packages/access tokens.
