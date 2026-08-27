# Data Preparation Workflows

These are distilled command patterns for a user's own checkout or installed copy
of the project. They describe what to run; the bundled validators in `scripts/`
are the safe, self-contained checks to run before training.

Always create the data directory first. The common full-run convention is a large
local data directory such as `/ephemeral/data`, but any writable path is valid if
you pass it consistently to configs and commands.

## Dependency Groups

| Need | Packages |
|---|---|
| Inspect/validate HDF5 and JSONL | `python`, `numpy`, `h5py`; `tiktoken` only for optional decode in `inspect_h5_tokens.py`. |
| Pile download/tokenization | `requests`, `zstandard`, `tqdm`, `tiktoken`, `h5py`, `numpy`. |
| Hugging Face datasets | `datasets` plus a reachable or pre-populated Hugging Face cache. |

If a user only needs to validate existing local files, do not install dataset or
network-heavy extras.

## 1. Pile/Pile-Uncopyrighted To Flat HDF5

**Output:** flat HDF5 `tokens` array with EOT `50256` after every document.

Preferred streaming/batch-tokenization command shape:

```bash
mkdir -p /ephemeral/data
PYTHONPATH=. python scripts/prepare_pretrain_data.py --split val \
  --out /ephemeral/data/pile_dev.h5
PYTHONPATH=. python scripts/prepare_pretrain_data.py --split train --num_shards 1 \
  --out /ephemeral/data/pile_train.h5
```

Useful small/debug variant:

```bash
PYTHONPATH=. python scripts/prepare_pretrain_data.py --split val \
  --max_tokens 200000 --out /ephemeral/data/pile_dev_tiny.h5
```

Validation after generation:

```bash
python skills/disco/train-llm-from-scratch/sub-skills/data-preparation/scripts/inspect_h5_tokens.py \
  /ephemeral/data/pile_dev.h5 --expect-eot-id 50256
```

Legacy compatibility path:

```bash
python scripts/data_download.py --train_max 1 --train_dir data/train --val_dir data/val
python scripts/data_preprocess.py --max_data 1000 \
  --out_train_file data/train/pile_train.h5 --out_val_file data/val/pile_dev.h5
```

Prefer the streaming command for new work because the legacy preprocessing path
resizes the HDF5 dataset per document and is slower. Use the legacy path only
when reproducing an old layout or tutorial step.

## 2. Alpaca/Dolly/GSM8K To Packed SFT HDF5

**Output:** `sft_packed.h5` and `sft_dev_packed.h5`, each with `tokens` and
`loss_mask` datasets of shape `(rows, context_length)`.

Full command shape:

```bash
mkdir -p /ephemeral/data
PYTHONPATH=. HF_HOME=/ephemeral/hf_cache python scripts/prepare_sft_data.py \
  --context_length 1024 --out_dir /ephemeral/data
```

Tiny network/cache smoke when datasets are reachable:

```bash
PYTHONPATH=. HF_HOME=/ephemeral/hf_cache python scripts/prepare_sft_data.py \
  --context_length 128 --limit_per_set 20 --out_dir /ephemeral/data/sft_smoke
```

Validation after generation:

```bash
python skills/disco/train-llm-from-scratch/sub-skills/data-preparation/scripts/validate_sft_h5.py \
  /ephemeral/data/sft_packed.h5 --context-length 1024
```

What the preparation command does:

- Alpaca and Dolly examples become one user turn plus one assistant turn.
- GSM8K examples become one user question plus assistant completion in
  `<think>...</think><answer>N</answer>` form.
- `encode_chat` creates `ids` and aligned `loss_mask`; only assistant completion
  tokens and the assistant EOT are trained.
- `pack_examples` concatenates all examples and slices fixed-length rows.

## 3. HH-RLHF/UltraFeedback To Preference JSONL

**Output:** `preferences.jsonl` and `preferences_test.jsonl`, each row containing
`prompt`, `chosen`, and `rejected`.

Command shape:

```bash
mkdir -p /ephemeral/data
PYTHONPATH=. HF_HOME=/ephemeral/hf_cache python scripts/prepare_preference_data.py \
  --source both --max_per_source 40000 --out_dir /ephemeral/data
```

Smaller variants:

```bash
PYTHONPATH=. HF_HOME=/ephemeral/hf_cache python scripts/prepare_preference_data.py \
  --source hh --max_per_source 1000 --out_dir /ephemeral/data/pref_smoke
PYTHONPATH=. HF_HOME=/ephemeral/hf_cache python scripts/prepare_preference_data.py \
  --source ultrafeedback --max_per_source 1000 --out_dir /ephemeral/data/pref_smoke
```

Validation after generation:

```bash
python skills/disco/train-llm-from-scratch/sub-skills/data-preparation/scripts/validate_preference_jsonl.py \
  /ephemeral/data/preferences.jsonl --limit-rows 5000
```

What the preparation command does:

- HH-RLHF strings are split at the last `Assistant:` marker so the prompt is
  shared and only the final response differs.
- UltraFeedback rows use the top-level prompt plus final chosen/rejected message
  content.
- Degenerate pairs with identical chosen and rejected strings are skipped.

## 4. GSM8K And Arithmetic To RL Prompt JSONL

**Output:** `rl_prompts_train.jsonl`, `rl_prompts_test.jsonl`, and
`arithmetic_prompts.jsonl`, all with `prompt` and `gold`.

Command shape:

```bash
mkdir -p /ephemeral/data
PYTHONPATH=. HF_HOME=/ephemeral/hf_cache python scripts/prepare_rl_prompts.py \
  --out_dir /ephemeral/data
```

Tiny variant:

```bash
PYTHONPATH=. HF_HOME=/ephemeral/hf_cache python scripts/prepare_rl_prompts.py \
  --train_limit 100 --test_limit 50 --arith_n 100 --arith_max 20 \
  --out_dir /ephemeral/data/rl_smoke
```

Validation after generation:

```bash
python skills/disco/train-llm-from-scratch/sub-skills/data-preparation/scripts/validate_rl_prompts_jsonl.py \
  /ephemeral/data/rl_prompts_train.jsonl --gold-policy numeric --limit-rows 5000
python skills/disco/train-llm-from-scratch/sub-skills/data-preparation/scripts/validate_rl_prompts_jsonl.py \
  /ephemeral/data/arithmetic_prompts.jsonl --gold-policy numeric --arithmetic-sanity
```

What the preparation command does:

- GSM8K gold is parsed from the final `#### N` field.
- Arithmetic curriculum rows are generated programmatically from `+`, `-`, and
  `*` expressions and store a float result.

## Choosing Paths For User Data

| User says... | Choose... | Validate with... |
|---|---|---|
| "I have raw text or Pile shards for base training" | flat HDF5 pretraining pipeline | `inspect_h5_tokens.py` |
| "I have instruction conversations or Alpaca-style rows" | SFT packed HDF5 pipeline | `validate_sft_h5.py` |
| "I have human preference pairs" | preference JSONL | `validate_preference_jsonl.py` |
| "I have math prompts for PPO/GRPO" | RL prompt JSONL | `validate_rl_prompts_jsonl.py` |

Do not launch training from this sub-skill. After data validates, route to the
appropriate sibling skill for the stage that consumes the file.
