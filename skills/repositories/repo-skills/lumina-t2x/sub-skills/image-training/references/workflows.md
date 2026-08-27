# Image Training Workflows

## Purpose

Read this when you need to prepare data, launch training, resume a run, or adapt one of the Lumina image-model trainers.

## Common prerequisites

- CUDA-capable hardware is required.
- `flash-attn` is required by the image training code paths.
- A full Apex build is optional; a Python-only Apex install is a known failure mode.
- The repo's training code uses distributed launchers (`torchrun` or Slurm) for the main runs.

## Lumina-T2I training

### Typical route

1. Prepare a JourneyDB-style manifest and point `configs/data/JourneyDB.yaml` at it.
2. Convert or download the checkpoint family you want to finetune.
3. Launch one of the stage scripts under `lumina_t2i/exps/`.

### Useful command shape

- `torchrun --nproc-per-node=8 train.py --model <model> --data_path <JourneyDB.yaml> --results_dir <out> ...`
- `srun -n8 --ntasks-per-node=8 --gres=gpu:8 bash exps/<stage>.sh`

### High-value flags

- `--cache_data_on_disk` to cache manifests locally for repeated runs.
- `--resume <checkpoint_dir>` to continue a run.
- `--init_from <checkpoint_dir>` to load weights without optimizer/data-loader state.
- `--data_parallel sdp|fsdp` to choose the distributed strategy.
- `--precision`, `--grad_precision`, `--model_parallel_size`, `--tokenizer_path`, and `--snr_type` for model-specific control.

## Lumina-Next-T2I training

### Typical route

- `torchrun --nproc-per-node=8 train.py --model <model> --data_path <JourneyDB.yaml> --results_dir <out> ...`
- Use the `lumina_next_t2i/exps/` shell scripts as the launch template.

### High-value flags

- Same distributed and resume flags as Lumina-T2I.
- `--checkpointing` to enable gradient checkpointing.
- `--use_flash_attn` to control the attention kernel choice.
- `--local_diffusers_model_root` for offline or mirrored diffusers model loading.
- `--qk_norm` on the mini branch when you want the qk-norm variant.

## Lumina-Next-T2I-Mini training and DreamBooth

### Mini training

- `python train.py --data_path <...> --results_dir <...> ...`

### DreamBooth SD3 adaptation

- `python train_dreambooth_sd3.py --data_path <...> --model_path <...> --results_dir <...> --instance_prompt <...> ...`

### High-value DreamBooth flags

- `--train_text_encoder` to finetune the text encoder as well.
- `--instance_prompt` for the subject description.
- `--use_t5` / `--no_t5` to toggle the text encoder family.
- `--caption_dropout_prob` for caption regularization.
- `--local_diffusers_model_root` when the environment cannot download diffusers models online.

## Launch guidance

- Keep the stage scripts and the local data path synchronized.
- If a run is being resumed, prefer the explicit `--resume` path over rebuilding state from scratch.
- Use the training subskill checker before a long distributed launch when the manifest or path layout is uncertain.
