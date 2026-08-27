# GLUE LoRA workflows

## Runner contract

The LoRA-aware sequence-classification runner accepts the normal model/data and
training arguments plus these LoRA-specific model arguments:

| Argument | Meaning |
| --- | --- |
| `--apply_lora` | Construct LoRA-aware attention projections. |
| `--lora_r` | Rank of each low-rank update. Must be positive when LoRA is enabled. |
| `--lora_alpha` | Scaling numerator used by the layer (`alpha / r`). |
| `--lora_path` | Optional file containing adapter parameters to load after the base model. |

The runner loads a named GLUE task through the datasets library, or local CSV/
JSON files with a `label` column and one or two sentence columns. For local
files, training and validation files are required; a test file is required for
`--do_predict`.

## Command shape

For a small, single-device check:

```bash
python run_glue.py \
  --model_name_or_path roberta-base \
  --task_name mnli \
  --do_train --do_eval \
  --max_seq_length 128 \
  --per_device_train_batch_size 2 \
  --per_device_eval_batch_size 2 \
  --learning_rate 5e-4 \
  --num_train_epochs 1 \
  --output_dir ./mnli-lora-smoke \
  --overwrite_output_dir \
  --apply_lora --lora_r 8 --lora_alpha 16
```

For multi-GPU runs, wrap the same runner with the launcher supported by the
installed PyTorch version. The archived commands use
`torch.distributed.launch`; newer environments may require `torchrun`.

The bundled `build_glue_lora_command.py` emits a command without assuming a
particular checkout path and can reduce the archived 8-GPU recipes to one GPU
for a smoke test.

## Checkpoint transfer

The runner first constructs the base model from `model_name_or_path` and then,
when `--lora_path` is supplied, loads the adapter state with `strict=False`.
Use a compatible base architecture, rank, target projections, and label head.
Do not pass a full base checkpoint as `--lora_path`; the file should contain
LoRA keys (and optional selected biases), not the whole pretrained model.

A typical evaluation-only transfer has the following logical order:

1. Select the same base model used for adapter training.
2. Set `--apply_lora`, `--lora_r`, and `--lora_alpha` to the training values.
3. Set `--lora_path` to the adapter checkpoint.
4. Set `--do_eval` and a new output directory.
5. Inspect missing/unexpected keys and evaluation metrics before trusting the
   result.

## Task and augmentation notes

The repository includes launchers for CoLA, SST-2, MRPC, QNLI, QQP, RTE, STS-B,
and MNLI. The `mnli.cutoff.sh` and `mnli.rdrop.sh` variants add data/regularity
arguments beyond the core LoRA path; treat them as optional experiment
variants, not required adapter settings.

The published NLU numbers were obtained with large GPU jobs and specific model
checkpoints. Use them as historical context only. A successful one-GPU smoke
run validates wiring, not benchmark parity.
