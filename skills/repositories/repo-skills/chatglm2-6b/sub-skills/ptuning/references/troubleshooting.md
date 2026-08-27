# P-Tuning Troubleshooting

## Dataset and parser errors

- **Missing column / empty dataset:** check `--prompt_column`,
  `--response_column`, and optional `--history_column` against the actual JSON
  keys. Run `validate_ptuning_data.py` before `torchrun`.
- **History error:** each item must be `[query, response]`; keep the history
  list ordered oldest to newest. Very long history is truncated by
  `max_source_length`.
- **File extension error:** the argument dataclass accepts JSON/CSV file
  extensions. Ensure train/validation/test paths exist and contain records.

## Checkpoints

- **Prefix weight size/key error:** use the base model plus the exact training
  `pre_seq_len`/`prefix_projection`; strip the
  `transformer.prefix_encoder.` prefix as documented.
- **Unexpected missing model files:** distinguish a prefix checkpoint (small,
  trainable prefix only) from a full checkpoint (complete model). Do not pass a
  prefix directory as `model_name_or_path` without the base model.
- **Output collisions:** use separate `output_dir` values for ADGEN, chat, and
  full-finetune runs; check the checkpoint step before prediction.

## Runtime and memory

- **CUDA OOM:** use quantization where supported, reduce source/target lengths,
  batch size, or increase gradient accumulation without changing effective
  batch size; close other GPU jobs. A longer context increases KV/cache and
  sequence memory.
- **`cpm_kernels` or OpenMP errors:** install the selected quantization/backend
  dependency for the platform. CUDA INT4 kernels are not an MPS fallback.
- **Training appears idle:** preprocessing, cache creation, and dataset workers
  can dominate the first stage; use a small subset and lower
  `preprocessing_num_workers` while diagnosing.

## Optional full fine-tuning

- **`deepspeed` not found:** the minimum environment intentionally omits it;
  install a CUDA/PyTorch-compatible version only for the optional full-finetune
  workflow and verify its launcher before a real run.
- **Distributed launch failure:** confirm `NUM_GPUS`, visible devices, free
  port, and the DeepSpeed config. Start with one-process P-Tuning v2 before
  debugging a four-GPU full-finetune run.

## Checkpoint web demo

If the P-Tuning Gradio demo fails at `.style()` or imports a newer Gradio API,
use the legacy-compatible Gradio guidance in `chat-and-demos` or adapt the UI
constructor. Keep the base model path and prefix checkpoint arguments
separate.
