# Checkpoints and Resume

## Output names

Training saves native VLM weights under `--save_dir` using:

```text
save_weight_hidden_size[_moe].pth
```

Examples: `sft_vlm_768.pth`, `pretrain_vlm_768.pth`, `sft_vlm_768_moe.pth`.

The saved model weight excludes the frozen `vision_encoder.*` parameters. The SigLIP2 vision encoder remains an external resource.

## Resume state

Resume files live under `checkpoints/` and use:

```text
save_weight_hidden_size[_moe]_resume.pth
```

They include model state, optimizer state, epoch, step, world size, optional scaler state, and logging run id. Use `--from_resume 1` to load the resume state.

## Atomic saving

Checkpoint writes use temporary files followed by replace operations. This reduces risk of corrupted output if a save is interrupted.

## GPU count changes

When resuming with a different distributed world size, the utility scales the saved step count by integer arithmetic based on saved and current world sizes. Warn users before changing GPU count, batch size, or data ordering during resume because it can affect skipped batches and reproducibility.

## Resume checklist

- Same stage and compatible `--save_weight`, `--hidden_size`, and `--use_moe`.
- Resume file exists under `checkpoints/`.
- Required base resources still exist: tokenizer, SigLIP2, data parquet, and relevant weights.
- User approves continuing an expensive training job.
