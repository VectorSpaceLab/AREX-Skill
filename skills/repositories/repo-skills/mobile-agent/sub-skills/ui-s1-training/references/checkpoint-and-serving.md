# UI-S1 Checkpoint Merge and Serving

`UI-S1/scripts/model_merger.py` supports `merge` and `test` operations for FSDP or Megatron checkpoint layouts.

## Merge

```bash
python sub-skills/ui-s1-training/scripts/build_model_merger_command.py \
  --operation merge \
  --backend fsdp \
  --local-dir /runs/checkpoints/global_step_10 \
  --target-dir /runs/merged-hf
```

Important options:

- `--backend fsdp|megatron`
- `--local_dir`: checkpoint directory.
- `--hf_model_path`: optional/deprecated original Hugging Face model config path.
- `--target_dir`: merged Hugging Face output.
- `--tie-word-embedding`: Megatron-only word embedding tying.
- `--is-value-model`: value model flag where supported.
- `--hf_upload_path` and `--private`: upload controls; do not use without a private token and explicit approval.

## Test

```bash
python sub-skills/ui-s1-training/scripts/build_model_merger_command.py \
  --operation test \
  --backend fsdp \
  --local-dir /runs/checkpoints/global_step_10 \
  --test-hf-dir /models/reference-hf
```

Verify checkpoint layout, config compatibility, and disk space before live merge/test.
