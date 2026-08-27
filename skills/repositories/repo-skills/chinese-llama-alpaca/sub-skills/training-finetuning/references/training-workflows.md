# Training Workflows

This reference explains how to build safe commands for the bundled PEFT/LoRA training scripts. Real training is long-running and should start only after the user approves model/data paths, GPU/backend use, output policy, and budget.

## File Map

| Need | Bundled file |
| --- | --- |
| CLM pretraining / continued pretraining | [`scripts/run_clm_pt_with_peft.py`](../scripts/run_clm_pt_with_peft.py) |
| Supervised instruction fine-tuning | [`scripts/run_clm_sft_with_peft.py`](../scripts/run_clm_sft_with_peft.py) |
| SFT prompt builder and collator | [`scripts/build_dataset.py`](../scripts/build_dataset.py) |
| PT shell template | [`templates/run_pt.sh`](../templates/run_pt.sh) |
| SFT shell template | [`templates/run_sft.sh`](../templates/run_sft.sh) |
| DeepSpeed config | [`templates/ds_zero2_no_offload.json`](../templates/ds_zero2_no_offload.json) |
| Safe data validator | [`scripts/validate_training_data.py`](../scripts/validate_training_data.py) |

## Before Any Training Run

1. Confirm the task family:
   - Chinese LLaMA: base/continued CLM pretraining.
   - Chinese Alpaca: instruction/chat SFT.
2. Confirm that the user has legal access to the required original LLaMA-compatible base weights and any existing Chinese LoRA/PEFT adapter path. This repo release provides LoRA adapters, not original full LLaMA weights.
3. Validate the training data using `--mode pt` or `--mode sft`.
4. Confirm tokenizer compatibility:
   - PT accepts only the documented model-vocab/tokenizer-length combinations.
   - SFT requires the Chinese Alpaca tokenizer length `49954`.
5. Use a fresh `OUTPUT_DIR`, or explicitly choose resume/overwrite behavior.
6. Decide whether DeepSpeed is installed and whether `templates/ds_zero2_no_offload.json` is appropriate for the GPU budget.

## CLM Pretraining / Continued Pretraining

Use PT for raw text continuation. The template is designed around `torchrun` and the no-offload ZeRO-2 DeepSpeed config.

Minimum environment variables for [`templates/run_pt.sh`](../templates/run_pt.sh):

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `MODEL_NAME_OR_PATH` | yes | none | Base HF model path or model id. |
| `TOKENIZER_NAME_OR_PATH` | yes | none | Matching LLaMA/Chinese tokenizer path or model id. |
| `DATASET_DIR` | yes | none | Directory with `.txt` files. |
| `DATA_CACHE_DIR` | yes | none | Writable datasets cache root. |
| `OUTPUT_DIR` | yes | none | Training output root. |
| `NPROC_PER_NODE` | no | `1` | Number of local GPU worker processes. |
| `BLOCK_SIZE` | no | `512` | Token block length for CLM chunks. |
| `LEARNING_RATE` | no | `2e-4` | LoRA optimizer LR. |
| `LORA_TRAINABLE` | no | attention+MLP projections | Comma-separated target modules. |
| `MODULES_TO_SAVE` | no | `embed_tokens,lm_head` | Non-LoRA modules saved in adapter checkpoint. |
| `PEFT_PATH` | no | empty | Existing adapter to resume/load with `PeftModel.from_pretrained`. |
| `RESUME_FROM_CHECKPOINT` | no | empty | Trainer checkpoint directory for resume. |
| `OVERWRITE_OUTPUT_DIR` | no | `false` | Set `true` only when intentionally replacing an output dir. |
| `MAX_STEPS` | no | empty | Optional bounded debug run limit. |

Typical safe flow:

```bash
python scripts/validate_training_data.py --mode pt --input /path/to/pt_data --max-records 1000
MODEL_NAME_OR_PATH=/path/to/base_or_chinese_llama \
TOKENIZER_NAME_OR_PATH=/path/to/matching_tokenizer \
DATASET_DIR=/path/to/pt_data \
DATA_CACHE_DIR=/path/to/new_pt_cache \
OUTPUT_DIR=/path/to/new_pt_output \
NPROC_PER_NODE=1 \
bash templates/run_pt.sh
```

The PT script tokenizes text, groups tokens into `--block_size` chunks, sets `labels=input_ids`, splits train/test by `--validation_split_percentage`, and saves PEFT checkpoints through `SavePeftModelCallback`.

## Supervised Instruction Fine-Tuning

Use SFT for Chinese Alpaca-style instruction following. It loads all `*.json` files from `--dataset_dir`, applies the Alpaca prompt template, masks prompt tokens with `-100`, and trains only on answer tokens.

Minimum environment variables for [`templates/run_sft.sh`](../templates/run_sft.sh):

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `MODEL_NAME_OR_PATH` | yes | none | LLaMA-compatible HF model path or model id. |
| `TOKENIZER_NAME_OR_PATH` | yes | none | Chinese Alpaca tokenizer path or model id; script expects length `49954`. |
| `DATASET_DIR` | yes | none | Directory with `.json` instruction files. |
| `OUTPUT_DIR` | yes | none | SFT output root. |
| `NPROC_PER_NODE` | no | `1` | Number of local GPU worker processes. |
| `MAX_SEQ_LENGTH` | no | `512` | Prompt+answer truncation length. |
| `LEARNING_RATE` | no | `1e-4` | LoRA optimizer LR. |
| `PEFT_PATH` | no | empty | Existing adapter path/model id to load before continuing. |
| `DO_EVAL` | no | `false` | Set `true` to add evaluation flags. |
| `VALIDATION_FILE` | only if `DO_EVAL=true` | empty | JSON validation file path. |
| `FORCE_RESIZE_EMBEDDINGS` | no | `false` | Adds `--force_resize_embeddings`; see API notes before relying on it. |
| `RESUME_FROM_CHECKPOINT` | no | empty | Trainer checkpoint directory for resume. |
| `OVERWRITE_OUTPUT_DIR` | no | `false` | Set `true` only when intentionally replacing an output dir. |
| `MAX_STEPS` | no | empty | Optional bounded debug run limit. |

Typical safe flow:

```bash
python scripts/validate_training_data.py --mode sft --input /path/to/sft_data --max-records 100
MODEL_NAME_OR_PATH=/path/to/base_or_merged_llama \
TOKENIZER_NAME_OR_PATH=/path/to/chinese_alpaca_tokenizer \
DATASET_DIR=/path/to/sft_data \
OUTPUT_DIR=/path/to/new_sft_output \
NPROC_PER_NODE=1 \
bash templates/run_sft.sh
```

To continue from an existing PEFT adapter, set `PEFT_PATH`. To resume a `Trainer` checkpoint, set `RESUME_FROM_CHECKPOINT`. These are different: `PEFT_PATH` loads adapter weights into the model, while `RESUME_FROM_CHECKPOINT` resumes optimizer/trainer state from a checkpoint directory.

## LoRA Defaults and Target Modules

The original shell templates use these practical defaults:

| Parameter | Default in bundled templates | Notes |
| --- | --- | --- |
| `LORA_TRAINABLE` / `--trainable` | `q_proj,v_proj,k_proj,o_proj,gate_proj,down_proj,up_proj` | Covers attention projections and MLP projections. |
| `LORA_RANK` / `--lora_rank` | `8` | LoRA rank. Increase only with memory approval. |
| `LORA_ALPHA` / `--lora_alpha` | `32` | LoRA scaling. |
| `LORA_DROPOUT` / `--lora_dropout` | `0.05` | Dropout used by source shell templates. |
| `MODULES_TO_SAVE` / `--modules_to_save` | `embed_tokens,lm_head` | Important when vocabulary is expanded or embeddings/output head change. |

The Python scripts default to narrower `trainable=q_proj,v_proj`, `lora_rank=8`, `lora_alpha=32`, `lora_dropout=0.1`, and no `modules_to_save`. Prefer the shell-template defaults for Chinese vocabulary expansion unless a user intentionally narrows LoRA targets.

## DeepSpeed Zero-2 No-Offload

[`templates/ds_zero2_no_offload.json`](../templates/ds_zero2_no_offload.json) configures ZeRO stage 2 with no CPU/NVMe offload. It leaves batch size, micro-batch size, gradient accumulation, gradient clipping, and fp16 enablement on `auto` so the Hugging Face `TrainingArguments`/DeepSpeed integration resolves them from command-line flags.

If `deepspeed` is unavailable or mismatched, either install a compatible DeepSpeed for the user-approved environment or omit `--deepspeed` for a smaller debug run. Omitting DeepSpeed changes memory behavior and is not equivalent to the source template.

## Checkpoint Outputs

Both training scripts add `SavePeftModelCallback`:

- PT saves adapter/tokenizer snapshots under `pt_lora_model`.
- SFT saves adapter/tokenizer snapshots under `sft_lora_model`.
- During periodic saves, the callback nests that name inside the checkpoint folder, for example `checkpoint-200/pt_lora_model/pt_lora_model` or `checkpoint-200/sft_lora_model/sft_lora_model` depending on the script path branch.
- At train end, final adapter/tokenizer output is saved directly under `OUTPUT_DIR/pt_lora_model` or `OUTPUT_DIR/sft_lora_model`.

The scripts also save Trainer metrics and state in `OUTPUT_DIR`. Keep these outputs separate from source model/tokenizer directories.

## Safe Adaptation Rules

- Do not edit copied scripts unless the user asks for a code change; prefer changing environment variables and template flags.
- Use model ids or user-provided paths only; do not hard-code private checkout, environment, or cache paths.
- Run a bounded `MAX_STEPS` smoke only after explicit approval. Even a 100-step run loads large models.
- If the goal is chat/instruction following, prefer Chinese Alpaca tokenizers and SFT. If the goal is base Chinese continuation, prefer Chinese LLaMA tokenizer/model combinations and PT.
