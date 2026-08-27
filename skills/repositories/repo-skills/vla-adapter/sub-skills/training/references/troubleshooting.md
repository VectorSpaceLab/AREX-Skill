# Troubleshooting

## The helper prints a command, but nothing runs

That is intentional. `scripts/build_finetune_command.py` is a safe renderer only. Copy the emitted command into a shell when you are ready to launch training.

## The benchmark and dataset do not match

- `--benchmark libero` should point at a LIBERO dataset such as `libero_spatial_no_noops`.
- `--benchmark calvin` should use `dataset_name=calvin_abc` and a data root that contains `calvin_abc` directly.
- `--benchmark aloha` should use the TFDS dataset registered by the ALOHA setup helper.

If the command still points at the wrong directory, fix `--data_root_dir` before launching.

## CALVIN still looks like LIBERO

The README instruction is to remove the LIBERO subfolder from the data root when switching to CALVIN. In practice that means the data root should be the parent directory that contains `calvin_abc`, not the LIBERO-only subfolder.

## ALOHA training fails before loading data

Make sure the ALOHA dataset has been registered first. The setup helper writes the bimanual TFDS config that the training command expects.

If you are using local pretrained models, make sure the local-model setup step was run before training.

## The run resumes from the wrong step

Resuming requires three things to line up:

- `--resume True`
- `--resume_step <exact-step>`
- `--resum_vla_path <checkpoint-root>`

The most common failure is pointing `resum_vla_path` at the wrong level or using a step number that does not match the checkpoint suffix.

## Checkpoints are being overwritten

That is the expected behavior when `save_latest_checkpoint_only=True`.

If you want every save to remain on disk, keep `save_latest_checkpoint_only=False`.

## LoRA merge is slow

Set `merge_lora_during_training=False` and merge later with the offline merge helper. This keeps the training loop lighter and avoids spending extra time on the merge path during save steps.

## W&B is trying to talk to the network

- ALOHA uses offline W&B by default in the stock launcher.
- For other benchmarks, add `WANDB_MODE=offline` and `WANDB_CONSOLE=off` yourself if you want the same behavior.
- If you only want the command text, use `--print-env` to display the environment block separately.

## You hit `AttributeError: 'NoneType' object has no attribute 'eglQueryString'`

Install the system OpenGL / EGL packages mentioned in the repository README:

- `libgl1-mesa-dev`
- `libegl1-mesa-dev`
- `libgles2-mesa-dev`
- `libglew-dev`

## The command OOMs on the first step

Use a smaller GPU profile:

- `tiny`: 1 / 8
- `low`: 4 / 4
- `medium`: 8 / 2
- `large`: 16 / 1

If you still OOM on a low profile, lower the batch size further and increase gradient accumulation manually in the emitted command.

## The command uses the wrong save format

Remember the distinction:

- `use_lora=True` keeps LoRA adapter checkpoints.
- `use_fz=True` writes the full model directly.

If you want the standard paper-style recipe, keep `use_lora=True` and `use_fz=False`.

## The generated command is missing offline env lines

That is normal for non-ALOHA recipes unless `--print-env` is set. If you want the same offline behavior for a LIBERO or CALVIN run, add the environment lines manually or regenerate with `--print-env`.
