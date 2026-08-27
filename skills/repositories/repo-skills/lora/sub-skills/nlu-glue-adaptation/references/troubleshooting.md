# NLU GLUE troubleshooting

## CLI and dependency failures

- `unrecognized arguments: --apply_lora`: the runner is not the LoRA-aware
  version described by this skill. Check the runner version or port the four
  LoRA model arguments into the current script rather than removing the flag.
- `ModuleNotFoundError` for `datasets`, `transformers`, `tokenizers`, or
  `loralib`: install the runner's compatible dependency set in one environment.
  The archived environment is old; do not mix its pinned package versions with
  an unrelated modern Transformers checkout without testing.
- Model download/authentication errors: use a local cached model or configure
  the model hub credentials explicitly. Do not treat a failed download as a
  LoRA shape failure.

## Checkpoint and model shape

- Missing `lora_A`/`lora_B`: the model was constructed without `apply_lora`, the
  rank is zero/omitted, or the target module path differs.
- Unexpected adapter keys: the checkpoint targets a different architecture,
  layer naming scheme, rank mask, or model family.
- Classifier-head shape warning: a transferred MNLI adapter does not prove that
  a new task's classifier head is compatible. Load the adapter only after
  rebuilding the correct task head and inspect the missing/unexpected lists.
- MRPC/RTE/STS-B transfer fails: the historical commands expect an adapter
  initialized from LoRA-adapted MNLI. Check the path, filename, and base model;
  do not point at a raw pretrained model as `--lora_path`.

## Hardware and launch

- `torch.cuda.is_available()` is false or NCCL initialization fails: use a
  one-device smoke command first, install a matching CUDA PyTorch wheel, then
  move to `torchrun`/distributed launch. CPU success does not validate a
  multi-GPU benchmark.
- Out-of-memory: reduce per-device batch size and sequence length before
  changing rank. DeBERTa-v2 XXL is intentionally a large, multi-GPU recipe.
- Determinism errors: the historical scripts set CUDA workspace and deterministic
  flags. Check that the current PyTorch version supports those flags; otherwise
  record the difference instead of silently claiming identical results.

## Data and outputs

For local CSV/JSON data, verify a `label` column and one or two text columns.
Ensure train/validation extensions match when a test file is supplied. Use a
fresh output directory or pass the runner's explicit overwrite/resume option;
existing non-empty directories often cause an early failure.
